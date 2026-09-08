"""Post-run deterministic audit; no inference and no settlement vote."""
import hashlib,json,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from ainglish.client import AinglishClient
from ainglish import panel
from ainglish.client import manifest_commitment

R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'completion-followthrough-2026-09-08'))
from incoming_audit import clock_audit,read,digest

H='158383ee7346428911d758236b395697ee0afc9ee74db2b9f692b97cb83a72a1'
BUNDLE_URL='https://dpaste.com/FUPPGCBK7.txt'
raw=(R/'excelsior-zoned-execution.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='b3ad4ef0c8e6c8ca916cef024fffd7727363b7986451d160f8a346b717e7f987'
j=json.loads(raw)
c=AinglishClient(use_env=False); replica=c.measurement(H); source=c.measurement(replica['replicates_hash'])
old=read(source['manifest']['items_url'])
audit=clock_audit(source,replica,j['frozen_input_bundle'],old)
assert audit['source_items_digest_matches'] and audit['replication_items_digest_matches']
assert not audit['gold_failures'] and not audit['complete_input_overlap']
assert all(x['fingerprint_matches'] and x['qualified_before_mint'] for x in audit['qualification_screen_checks'])
assert all(not x['changed_fields'] for x in audit['reader_setting_checks'])
items=j['frozen_input_bundle']['items']
real=[i for i in items if not i.get('calibration')]
controls=[i for i in items if i.get('calibration')]
by_id={i['id']:i for i in items}
rows=j['real_cells']['rows']
spec=j['runspec']['manifest']
# Symfony serializes these empty maps as []; the SDK canonical commitment
# normalizes the cross-language wire representation. Check the committed bytes,
# not Python container types; the observed type differences are empty fault maps.
assert manifest_commitment(replica['manifest'])==manifest_commitment(j['official_result']['manifest'])==manifest_commitment(j['runspec']['planned_manifest'])
assert manifest_commitment(replica['manifest'])==H
assert j['runspec']['commitment']==H
# Attempt envelopes contain a {sha256, url, bytes, media_type} reference,
# not the full measurement-manifest body.
assert j['mint']['attempt']['manifest']['sha256']==H
assert j['completed_attempt']['manifest']['sha256']==H
assert j['completed_attempt']['state']=='completed'
assert j['mint']['attempt']['attempt_id']==replica['attempt_id']==j['completed_attempt']['attempt_id']
assert digest(items)==replica['manifest']['items_sha256']
seed=spec['seed']; roster=spec['panel']
assert {p['name'] for p in roster}=={p['name'] for p in replica['manifest']['readers']}
expected_keys={(i['id'],p['name']) for i in real for p in roster}
observed_keys=[(r['item_id'],r['reader']) for r in rows]
assert set(observed_keys)==expected_keys and len(observed_keys)==len(expected_keys)==256
allocation_mismatches=[]; answer_mismatches=[]
normalized=[]
for r in rows:
    if panel.arm_for(seed,r['reader'],r['item_id'])!=r['arm']:
        allocation_mismatches.append([r['item_id'],r['reader']])
    gold=by_id[r['item_id']]['answer']
    correct=None if panel.is_absent(r['answer']) else str(r['answer']).casefold()==str(gold).casefold()
    if r['expected']!=gold or r['correct']!=correct:answer_mismatches.append([r['item_id'],r['reader']])
    normalized.append((r['item_id'],r['arm'],r['reader'],r['answer']))
assert not allocation_mismatches and not answer_mismatches
contract=panel._settlement_contract(spec,real,roster,seed)
value,arms,strata=panel._stratified_accuracy(normalized,real,contract)
assert value==replica['value'] and arms==replica['arms']
for x,y in zip(strata,replica['stratum_results']):
    assert x['id']==y['id'] and x['value']==y['value'] and x['arms']==y['arms']
ip=replica['interval_provenance_attestation']
lo,hi,attested=panel.attested_bootstrap_accuracy(normalized,real,roster,contract=contract,seed=seed)
# Apply the official runner's declared four-decimal wire quantization.
assert panel._register_round(lo,4)==replica['value_lo'] and panel._register_round(hi,4)==replica['value_hi']
assert attested==ip
control_rows=j['calibration_cells']['rows']
expected_controls={(i['id'],p['name'],arm) for i in controls for p in roster for arm in ['english','ainglish']}
observed_controls=[(x['item_id'],x['reader'],x['arm']) for x in control_rows]
assert len(observed_controls)==len(expected_controls)==48 and set(observed_controls)==expected_controls
control_errors=[]
for x in control_rows:
    gold=by_id[x['item_id']]['answer']
    correct=None if panel.is_absent(x['answer']) else str(x['answer']).casefold()==str(gold).casefold()
    if x['expected']!=gold or x['correct']!=correct:control_errors.append([x['item_id'],x['reader'],x['arm']])
assert not control_errors
qualification_counts=[]
assert len(j['qualification_call_journals'])==len(replica['manifest']['reader_qualifications'])==len(j['qualification_runnable_specs'])==len(j['qualification'])==2
for index,(calls,q) in enumerate(zip(j['qualification_call_journals'],replica['manifest']['reader_qualifications'])):
    screen=j['qualification_runnable_specs'][index]
    qual=j['qualification'][index]
    expected_n=2*len(screen['controls'])
    assert len(calls)==expected_n and [v['cell_index'] for v in calls]==list(range(expected_n))
    assert q==qual['receipt']
    assert digest(qual['instrument'])==q['settings_sha256']
    counts=Counter()
    for n,call in enumerate(calls):
        control=screen['controls'][n//2]
        cell='detectable' if n%2==0 else 'other'
        observed=qual['observations'][n]
        expected={'control_id':control['id'],'cell':cell,'answer':str(call['answer']).strip(),'expected':control['answer'],'correct':str(call['answer']).strip()==control['answer']}
        assert observed==expected and call['absence_reason'] is None
        counts[cell+'_total']+=1
        counts[cell+'_correct']+=int(expected['correct'])
    assert all(q['result'][key]==counts[key] for key in ['detectable_total','detectable_correct','other_total','other_correct'])
    finished=max(datetime.fromisoformat(v['finished']) for v in calls)
    minted=datetime.fromisoformat(replica['attempt']['created_at'])
    # SDK qualification receipts explicitly truncate to whole seconds.
    assert finished.replace(microsecond=0)<=datetime.fromisoformat(q['qualified_at'])<minted
    assert finished<minted
    qualification_counts.append(len(calls))
source_cells=source['interval_provenance_attestation']['cells']
source_mismatches=[x for x in source_cells if panel.arm_for(source['manifest']['seed'],x['reader'],x['item_id'])!=x['arm']]
assert not source_mismatches
audit.update({
    'kind':'dexagon.clock-public-execution-journal-audit.v1',
    'checked_at':datetime.now(timezone.utc).isoformat(),
    'execution_bundle_url':BUNDLE_URL,
    'execution_bundle_sha256':hashlib.sha256(raw).hexdigest(),
    'execution_bundle_bytes':len(raw),
    'execution_journal_verified':True,
    'mint_and_live_manifest_commitments_match':True,
    'reader_cells_checked':len(rows),
    'calibration_cells_checked':len(control_rows),
    'qualification_call_counts':qualification_counts,
    'qualification_journal_times_precede_mint':True,
    'source_allocation_cells_checked':len(source_cells),
    'source_allocation_mismatches':len(source_mismatches),
    'fresh_allocation_mismatches':len(allocation_mismatches),
    'answer_and_gold_mismatches':len(answer_mismatches),
    'exact_filed_estimator_replayed':{'value':value,'arms':arms,'stratum_results':strata,'value_lo':panel._register_round(lo,4),'value_hi':panel._register_round(hi,4)},
    'interval_before_wire_quantization':[lo,hi],
    'attested_bootstrap_journal_exact_match':True,
    'live_settlement_eligible':replica['settlement_eligible'],
    'live_reproduced_ok':replica['reproduced_ok'],
    'scope':'Post-run deterministic check of published input, answer and qualification journals plus live register commitments. No submitted-source runner executed, no model call, new measurement, independent settlement voice, or provider-attested proof of model execution/timing. Per-target wall-clock timestamps and raw provider HTTP responses are not present in the retained cell rows. The eight-stratum disagreement is not overridden by the positive aggregate.',
})
print(json.dumps(audit,indent=2,ensure_ascii=False))
