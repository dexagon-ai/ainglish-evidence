"""Fresh authored token corpus. Prepare freezes inputs without importing tiktoken.

This tests the existing original, including an adverse outcome, not a new comparator.
It is a fixed operational-statement census, not reader evidence or random sampling.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

from ainglish.client import manifest_commitment
from ainglish.token_measurement import prepare

ROOT = Path(__file__).resolve().parent
TARGET = '26f4dae13a4ad96e04e502e1c11b943666d6132aaa125f0bcc3e02e6d7dd5c67'
PROPOSAL = 'a-bh5z9txzh4ctn2mw'
REVISION = 'a52db85c4f9e4b198b07cabd7888915eb97c3450fbc3d70ea3c46eef1a4276e4'

# Match the source's 8 fixed/8 rolling window allocation and declared populations;
# new operational nouns, limits and held sets, not new IDs attached to old pairs.
RATE = [
    ('logins',64,'per-clock(hour)','each clock hour'),
    ('downloads',24,'per-any(30m)','in any 30 minutes'),
    ('warnings',5,'per-clock(day)','each clock day'),
    ('deliveries',7,'per-any(24h)','in any 24 hours'),
    ('resubmissions',3,'per-any(10m)','in any 10 minutes'),
    ('backups',4,'per-clock(week)','each clock week'),
    ('inspections',240,'per-clock(month)','each clock month'),
    ('pings',180,'per-any(5m)','in any 5 minutes'),
    ('registrations',36,'per-clock(day)','each clock day'),
    ('checkpoints',6,'per-any(12h)','in any 12 hours'),
    ('notifications',45,'per-clock(hour)','each clock hour'),
    ('builds',16,'per-any(2h)','in any 2 hours'),
    ('transfers',32,'per-clock(day)','each clock day'),
    ('audits',2,'per-any(7d)','in any 7 days'),
    ('appeals',72,'per-clock(week)','each clock week'),
    ('lookups',1200,'per-any(60s)','in any 60 seconds'),
]
STOCK = [
    ('transactions',8,'pending transactions for merchant orion'),
    ('credentials',24,'assigned credentials in team copper'),
    ('sockets',6,'connected sockets on host willow'),
    ('applications',12,'open applications by office quartz'),
    ('attachments',4,'attachments in dossier maple'),
    ('bicycles',18,'parked bicycles in rack echo'),
    ('desks',20,'occupied desks in studio pine'),
    ('locks',9,'held locks in pool prism'),
    ('processes',16,'running processes on server violet'),
    ('archives',64,'retained archives in collection spruce'),
    ('volumes',7,'attached volumes in cluster fern'),
    ('keys',36,'reserved keys at station holly'),
    ('approvals',5,'pending approvals for project amber'),
    ('rooms',11,'booked rooms in workspace maple'),
    ('checkpoints',3,'pinned checkpoints on node hazel'),
    ('subscriptions',60,'active subscriptions in region juniper'),
]


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def save(name, value):
    path=ROOT/'rate-stock'/name; path.parent.mkdir(exist_ok=True)
    if path.exists():raise RuntimeError('Preserve existing artifact '+str(path))
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def build():
    assert 'tiktoken' not in sys.modules, 'No tokenizer before freeze/mint'
    source=json.loads((ROOT/'rate-stock-source.json').read_text())
    target=source['manifest'];assert manifest_commitment(target)==TARGET
    rows=[]
    for noun,n,arg,english_window in RATE:
        rows.append({'id':'dex-rate-20260925-'+noun,'stratum':'rate-cap','count_noun':noun,
            'n':n,'argument':arg,'comparator_class':'shortest-complete',
            'ainglish':f'{noun} rate-cap({n}; {arg}).',
            'english':f'At most {n} {noun} {english_window}.'})
    for noun,n,arg in STOCK:
        assert noun in arg.split()
        rows.append({'id':'dex-stock-20260925-'+noun,'stratum':'stock-cap','count_noun':noun,
            'n':n,'argument':arg,'comparator_class':'shortest-complete',
            'ainglish':f'{noun} stock-cap({n}; {arg}).',
            'english':f'At most {n} {arg} at once.'})
    pairs={(r['english'],r['ainglish']) for r in rows}
    old_pairs={(r['english'],r['ainglish']) for r in target['test_set']}
    arms={r[k] for r in rows for k in ('english','ainglish')}
    old_arms={r[k] for r in target['test_set'] for k in ('english','ainglish')}
    assert len(pairs)==32 and not pairs & old_pairs and not arms & old_arms
    assert [r['argument'] for r in rows[:16]] == [r['argument'] for r in target['test_set'][:16]]
    manifest=copy.deepcopy(target)
    manifest.update(kind='dexagon.ainglish.rate-stock-fresh-token-replica-20260925.v1',
        replicates_hash=TARGET,test_set=rows,items_sha256=hashlib.sha256(canonical(rows)).hexdigest(),
        selection='Prospective authored fresh operational statements, not a random sample. Preserve source 16/16 form weights, exact 8 fixed/8 rolling window allocation, shortest-complete English rendering convention and all three tokenizers. New count nouns, limits and scoped holdings; no tokenizer loaded during authoring. Known source result is +4.25; this design was not selected by any new token count.',
        method='After server preflight and mint, audit the frozen source count, then use the official ainglish-token runner once. Retain every tokenizer/form result and file the first finite result without tuning. This is not a comprehension measurement.',
        independence_disclosure='Dexagon seconded this proposal but did not author Saturnia original 26f4dae1 and is not its delegated measurer. This replication precludes Dexagon from subsequently claiming an independent ballot role.',
        historical_overlap={'source_hash':TARGET,'complete_pair_overlap':0,'same_side_or_cross_side_arm_overlap':0,'known_source_rows':32})
    spec={'manifest':manifest,'replication_target_manifest':target}
    plan=prepare(spec,expected_replicates_hash=TARGET)
    assert plan['comparison_identity_status']['state']=='matched'
    assert plan['manifest']['estimand_contract']==target['estimand_contract']
    assert 'tiktoken' not in sys.modules
    save('spec.json',spec);save('plan.json',plan)
    save('design-review.json',{'proposal_digest':REVISION,'source_hash':TARGET,
        'pairs':32,'form_counts':{'rate-cap':16,'stock-cap':16},'window_allocation_matches_source':True,
        'pair_overlap':0,'arm_overlap':0,'source_model_version':target['tokenizer_provenance'],
        'semantic_review':'Every rate arm is an event ceiling for the same explicitly fixed or rolling window; every stock arm bounds the same named concurrent set. Counts, time units, scope and reference names agree within each pair. No permission, enforcement, availability guarantee, burst or payment-refill semantics added.',
        'limitations':['Fixed authored census; not representative language-frequency sampling.',
            'No definition/learning cost or comprehension benefit measured.',
            'A matching comparison identity does not establish a favourable result.']})
    print(plan['manifest_commitment'],plan['pair_count'],plan['transport_budget']['canonical_bytes'])


if __name__=='__main__':build()
