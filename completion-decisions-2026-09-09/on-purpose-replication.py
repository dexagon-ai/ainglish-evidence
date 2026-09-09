"""One independently eligible, fresh-input replication; never tune after counting."""
import argparse,json
from pathlib import Path
from unittest.mock import patch
from ainglish import token_measurement
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client

ROOT=Path(__file__).resolve().parent/'on-purpose-replication'
TARGET='256a92882cc54e2347488c832bbcbd6171f8027482f4e1913217bebbe470ff24'
PID='a-kwn7gx5nstn1cnyn'
def save(name,obj):
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/name).open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False)
def fresh():
    c=ainglish_client();s=c.suggestions(proposal=PID)
    assert any(x.get('replicates_hash')==TARGET for x in s['suggestions']), 'Target no longer recommended to this identity'
    m=c.measurement(TARGET);p=c.proposal('on-purpose-by-accident',authenticated=True)
    assert p['public_id']==PID and p['stage'] in ['seconded','measured']
    assert m['submitter']['sub']!=c.whoami()['sub'] and m['evidence_state']=='valid' and not m['confirmed']
    assert manifest_commitment(m['manifest'])==TARGET
    return c,s,p,m
def prepare():
    c,s,p,m=fresh();source=m['manifest']
    # Four deliberate actions and four explicitly unforeseen slips, all software reports.
    # Full comparator context is shared; no timing, actor, object or repair is added in one arm.
    texts=[
        ('I archived the obsolete build script deliberately; the release notes remain.','I archived the obsolete build script on-purpose; the release notes remain.'),
        ('The formatter overwrote the config comment, which I had not foreseen — retrieving it from version control.','The formatter overwrote the config comment by-accident — retrieving it from version control.'),
        ('The nightly export was paused deliberately: the storage node is under repair.','The nightly export was paused on-purpose: the storage node is under repair.'),
        ('Handover: the search index was reset by mistake during the smoke test, unforeseen; expect a rebuild.','Handover: the search index was reset by-accident during the smoke test; expect a rebuild.'),
        ('I rotated the staging certificate deliberately; the old certificate is retained.','I rotated the staging certificate on-purpose; the old certificate is retained.'),
        ('The cleanup task removed the fixture directory by mistake, an outcome its operator did not foresee; restoring the archive.','The cleanup task removed the fixture directory by-accident; restoring the archive.'),
        ('We disconnected the obsolete webhook deliberately; the replacement is active.','We disconnected the obsolete webhook on-purpose; the replacement is active.'),
        ('The scheduler restarted the worker by mistake, an outcome its operator did not foresee; the queued task was retried.','The scheduler restarted the worker by-accident; the queued task was retried.'),
    ]
    pairs=[{'english':e,'ainglish':a} for e,a in texts]
    old={(x['english'],x['ainglish']) for x in source['test_set']}
    assert old.isdisjoint(texts) and len(set(texts))==8
    manifest={'metric':'token_delta','models':source['models'],'test_set':pairs,
              'replicates_hash':TARGET,'estimand_contract':source['estimand_contract']}
    plan=token_measurement.prepare({'manifest':manifest,'replication_target_manifest':source},expected_replicates_hash=TARGET)
    save('source.json',m);save('proposal-before.json',p);save('suggestions-before.json',s)
    save('plan.json',plan);save('preflight.json',c.preflight_attempt(p['slug'],plan['manifest'],**plan['mint']))
    save('design.json',{'pairs':8,'forms':'4 deliberate / 4 unforeseen slips','prior_pair_overlap':0,
        'comparator':'Complete same-information English; unforesight explicit in all four accident pairs. No new settlement strata or tokenizer population.',
        'legacy_identity':'New v2 sample identity is honest and distinct from retained v1; live admission, not a copied stale digest, decides eligibility.',
        'spend':'No token counts before mint; preserve disagreement and member_span is not a sampling confidence interval.'})
    print('Prepared only; publish freeze before run.')
def run():
    assert not (ROOT/'mint.json').exists(),'Reconcile retained attempt instead of rerunning'
    c,s,p,m=fresh();plan=json.loads((ROOT/'plan.json').read_text())
    c.preflight_attempt(p['slug'],plan['manifest'],**plan['mint'])
    opened=c.mint_attempt(p['slug'],plan['manifest'],**plan['mint']);save('mint.json',opened)
    aid=opened['attempt']['attempt_id']
    with patch('tiktoken.load.read_file',side_effect=RuntimeError('Cached encodings only; downloads prohibited')):
        result=token_measurement.run_prepared(plan,aid,expected_replicates_hash=TARGET)
        token_measurement.verify_payload(result['payload'])
    save('result.json',result);save('receipt.json',c.measure(p['slug'],result['payload']))
    save('source-after.json',c.measurement(TARGET));save('proposal-after.json',c.proposal(p['slug'],authenticated=True))
    save('suggestions-after.json',c.suggestions(proposal=PID))
    print('Filed',manifest_commitment(result['payload']['manifest']),result['payload']['value'])
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);args=ap.parse_args()
    (prepare if args.action=='prepare' else run)()
