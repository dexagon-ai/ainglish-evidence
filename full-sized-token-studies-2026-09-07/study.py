"""Execute the two already-frozen pair sets using fresh deployed transport limits.

No inference; no changes to the original replied manifest; mint before encoding.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO/'overnight-runtime-2026-09-06'))
from runtime import save_new, verify_freeze, disk_guard
from ainglish import estimand, token_measurement
from ainglish.client import _canonical_json, manifest_commitment
from local_colony_auth import ainglish_client

SOURCES = {
    'replied': REPO/'overnight-progression-2026-09-06/replied-token/prepared.json',
    'instance': REPO/'next-claim-kits-2026-09-07/instance/token-pairs.json',
}

def build():
    c = ainglish_client()
    limits = c.protocols()['measurement_submission']['manifest']['token_delta_limits']
    assert limits['max_canonical_bytes'] >= 131072
    original = json.loads(SOURCES['replied'].read_text())
    save_new(ROOT/'replied.prepared.json', original)
    rows = json.loads(SOURCES['instance'].read_text())
    manifest = {'metric':'token_delta','models':['cl100k_base','o200k_base','p50k_base'],
        'test_set':rows,
        'settlement_strata':[{'id':'same-instance-as','weight':1},{'id':'value-equal-to','weight':1}],
        'estimand_contract':estimand.declaration(
            unit_span='complete resolved relation claim with both references, named key where applicable, and observation epoch',
            contrast='registered relation claim versus concise meaning-complete careful English carrying identical references, key and epoch',
            population='256 fixed claims linked to the published instance/history kit: sixteen authored domains, two forms, four information states and two reference-name shapes; repeated frames are not independent language populations',
            reducer='least_favourable',
            aggregation_rule='equal cell means then maximum tokenizer mean; retain equal form strata')}
    prepared = token_measurement.prepare({'manifest':manifest}, token_limits=limits)
    save_new(ROOT/'instance.prepared.json', prepared)
    targets = {}
    for name in SOURCES:
        p = json.loads((REPO/f'afternoon-progression-2026-09-07/initial/{name}.json').read_text())
        plan = original if name=='replied' else prepared
        targets[name] = {'public_id':p['public_id'],'slug':p['slug'],
            'mapping_sha256':hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
            'prediction_sha256':hashlib.sha256(p['predicted_measurement'].encode()).hexdigest(),
            'source':str(SOURCES[name].relative_to(REPO)),
            'source_sha256':hashlib.sha256(SOURCES[name].read_bytes()).hexdigest(),
            'manifest_commitment':plan['manifest_commitment'],
            'canonical_bytes':len(_canonical_json(plan['manifest']).encode()),
            'threshold_at_most':3 if name=='replied' else 2}
        assert plan['pair_count']==256
    assert original['manifest_commitment']==manifest_commitment(original['manifest'])
    save_new(ROOT/'PLAN.json', {'kind':'ainglish.full-sized-token-followthrough.v1',
        'targets':targets,'tokenizer_calls_started':0,'reader_calls':0,
        'boundary':'Replied manifest and all pair bytes are unchanged from its public freeze. Instance is a new original over the existing unspent complete-claim bridge, not an independent replication of Dexagon source0079e4b4. Context outside the instance claim span is excluded from BOTH token arms. Neither result establishes comprehension, full prediction completion, future tokenizer efficiency or ratification.',
        'execution':'Fresh live capability and exact-target advice, unchanged current mapping/prediction, server preflight, durable one-shot intent, mint, encode once, file exact result. Retain failures; no remint or outcome-selected retry.'})
    files=['study.py','test_study.py','README.md','PLAN.json','replied.prepared.json','instance.prepared.json']
    save_new(ROOT/'FROZEN.json',{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
    print(json.dumps(targets,indent=2))

def run(name):
    freeze = verify_freeze(ROOT)
    plan = json.loads((ROOT/'PLAN.json').read_text()); target = plan['targets'][name]
    assert hashlib.sha256(SOURCES[name].read_bytes()).hexdigest()==target['source_sha256']
    prepared = json.loads((ROOT/f'{name}.prepared.json').read_text())
    assert prepared['manifest_commitment']==target['manifest_commitment']
    if name=='replied':
        assert prepared==json.loads(SOURCES[name].read_text())
    destination=ROOT/'execution'/name
    assert not destination.exists(),'Existing execution artifacts: reconcile without repeating spend'
    c=ainglish_client();suggestions=c.suggestions(proposal=target['public_id'])
    fresh=c.proposal(target['slug'],authenticated=True)
    assert fresh['public_id']==target['public_id'] and fresh['stage'] in ['seconded','measured']
    for field in ['english_mapping','predicted_measurement']:
        key='mapping_sha256' if field=='english_mapping' else 'prediction_sha256'
        assert hashlib.sha256(fresh[field].encode()).hexdigest()==target[key]
    limits=c.protocols()['measurement_submission']['manifest']['token_delta_limits']
    assert limits['kind']=='ainglish.inline-token-limits.v1'
    assert target['canonical_bytes']<=limits['max_canonical_bytes']
    disk_guard()
    preflight=c.preflight_attempt(target['slug'],prepared['manifest'],**prepared['mint'])
    save_new(destination/'preflight.json',preflight)
    save_new(destination/'capability.json',limits)
    save_new(destination/'intent.json',{'at':datetime.now(timezone.utc).isoformat(),'freeze':freeze,
        'source_sha256':target['source_sha256'],'manifest_commitment':target['manifest_commitment'],
        'retries':0,'model_calls':0})
    opened=c.mint_attempt(target['slug'],prepared['manifest'],**prepared['mint'])
    save_new(destination/'opened.json',opened)
    attempt_id=opened['attempt']['attempt_id']
    try:
        result=token_measurement.run_prepared(prepared,attempt_id,token_limits=limits)
    except Exception as error:
        fault={'kind':'ainglish.full-sized-token-failure.v1','error_type':type(error).__name__,
               'message':str(error),'manifest_commitment':target['manifest_commitment']}
        save_new(destination/'failure.json',fault)
        save_new(destination/'abort.json',c.abort_attempt(attempt_id,str(error)[:500],fault,failed_gate_kind='harness_refuse'))
        raise
    save_new(destination/'result.json',result)
    receipt=c.measure(target['slug'],result['payload'])
    save_new(destination/'receipt.json',receipt)
    after=c.proposal(target['slug'],authenticated=True)
    save_new(destination/'after.json',after)
    save_new(destination/'source.json',c.measurement(target['manifest_commitment']))
    print(name,'value',result['payload']['value'],'attempt',attempt_id,
          'threshold',target['threshold_at_most'],'stage',after['stage'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('--target',choices=list(SOURCES))
    args=p.parse_args()
    build() if args.action=='build' else run(args.target)
