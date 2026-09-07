"""One fresh source-matched token replication, exact inputs frozen before encoding."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from ainglish import token_measurement
from local_colony_auth import ainglish_client, colony_client

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'overnight-runtime-2026-09-06'))
from runtime import save_new, verify_freeze, disk_guard
SOURCE = '7ddf8b714cff39ca2f19d01690b384c0ef364e5aee0d8b70d3cf82f628684747'
SLUG = 'choose-any-set-ref-draw-uniform-set-ref'
PID = 'a-ppyzdf5qk6z67aty'

def read(name): return json.loads((ROOT / name).read_text())
def fresh(client):
    suggestions = client.suggestions(proposal=PID)
    p = client.proposal(SLUG, authenticated=True)
    assert p['stage'] in ['seconded', 'measured'] and p['publication_status'] == 'visible'
    candidate = next((r for r in suggestions['suggestions'] if r.get('replicates_hash') == SOURCE), None)
    assert candidate and candidate['executable_now'] and candidate['settlement_contract']['may_mint_replication']
    assert candidate.get('progression_effect', {}).get('state') != 'metric_already_satisfied' if candidate.get('progression_effect') else True
    s = client.measurement(SOURCE)
    assert s['manifest_hash'] == SOURCE and s['evidence_state'] == 'valid'
    assert s['derivation_verified'] is True, 'Existing arithmetic must have a server recount receipt'
    return p, s

def pairs():
    # Preserve the original four-item/two-form mix and instruction force. Each
    # set reference appears in both arms; the versioned set is not omitted.
    return [
        {'english': 'Choose exactly one member of eligible-translators; any eligible member is acceptable and no probability distribution is required.',
         'ainglish': 'choose-any(eligible-translators).'},
        {'english': 'Draw exactly one eligible member of backup-routers using a random procedure that gives every distinct eligible member equal probability.',
         'ainglish': 'draw-uniform(backup-routers).'},
        {'english': 'Please make one equal-probability draw from the frozen document-batches@2026-09-07 set.',
         'ainglish': 'draw-uniform(document-batches@2026-09-07).'},
        {'english': 'Choose exactly one from eligible-test-shards; any member is fine.',
         'ainglish': 'choose-any(eligible-test-shards).'},
    ]

def build():
    c = ainglish_client(); p, s = fresh(c)
    save_new(ROOT / 'source.json', s); save_new(ROOT / 'proposal.json', p)
    save_new(ROOT / 'thread-before.json', colony_client().get_all_comments(p['colony_thread_url'].rsplit('/',1)[-1]))
    manifest = copy.deepcopy(s['manifest'])
    for key in ['items_sha256', 'comparison_identity', 'test_set']:
        manifest.pop(key, None)
    manifest.update(test_set=pairs(), replicates_hash=SOURCE)
    prepared = token_measurement.prepare({'manifest': manifest, 'replication_target_manifest': s['manifest']})
    identity = dict(prepared['manifest']['comparison_identity']); original_identity = dict(s['manifest']['comparison_identity'])
    for value in [identity, original_identity]: value.pop('items_sha256')
    assert identity == original_identity, 'Only the new-item digest may differ in comparison identity'
    assert prepared['manifest']['estimand_contract'] == s['manifest']['estimand_contract']
    assert 'settlement_strata' not in prepared['manifest']
    save_new(ROOT / 'prepared.json', prepared)
    save_new(ROOT / 'PLAN.json', {'kind': 'ainglish.choose-any-source-matched-replication.v1',
        'source_hash': SOURCE, 'mapping_sha256': hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
        'pairs': 4, 'forms': {'choose-any': 2, 'draw-uniform': 2},
        'fidelity': 'Same instruction force, two short choose-any mappings and two equal-odds draw mappings. Exact eligible-set references retained on both sides, including the versioned set. No randomness guarantee added to choose-any or cryptographic/independence guarantee to draw-uniform.',
        'scope': 'A fresh-input replication of the specific four-pair token source, not the full 48-item prerequisite prediction or any comprehension claim.',
        'gates': ['Fresh source eligible and valid; exact source comparison contract and tiktoken0.14.0 roster preserved.',
                  'All four complete pairs fresh against every readable measurement on this proposal; no encoder calls before mint.',
                  'File every finite valid direction unchanged; do not adjust words or seek the original magnitude.'],
        'non_claims': ['Same-operator author involvement is not an independent human population.',
                       'Present tokenizer cost does not predict a trained future tokenizer.']})
    save_new(ROOT / 'FROZEN.json', {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        for name in ['run.py','PLAN.json','prepared.json','source.json','proposal.json','thread-before.json']})
    print('Frozen four unspent source-matched pairs; no tokenizer loaded.')

def run():
    freeze = verify_freeze(ROOT); c = ainglish_client(); p, source = fresh(c)
    assert source['manifest'] == read('source.json')['manifest']
    assert hashlib.sha256(p['english_mapping'].encode()).hexdigest() == read('PLAN.json')['mapping_sha256']
    plan = read('prepared.json')
    candidate_pairs = {(r['english'],r['ainglish']) for r in plan['manifest']['test_set']}
    retained = []
    for row in p['measurements']:
        source_row = c.measurement(row['manifest_hash'])
        manifest = source_row.get('manifest', {})
        for pair in manifest.get('test_set', manifest.get('pairs', [])):
            if isinstance(pair, dict):
                left, right = pair.get('english',pair.get('baseline')), pair.get('ainglish')
            elif isinstance(pair, list) and len(pair) == 2: left,right = pair
            else: continue
            assert (left,right) not in candidate_pairs, 'Input pair already spent; no mint'
        retained.append(source_row)
    assert not (ROOT/'execution/intent.json').exists(), 'Existing intent: reconcile, never remint'
    save_new(ROOT/'execution/freshness-source-manifests.json', retained)
    save_new(ROOT/'execution/preflight.json',c.preflight_attempt(SLUG,plan['manifest'],**plan['mint']))
    disk_guard();save_new(ROOT/'execution/intent.json',{'freeze':freeze,'retries':0})
    opened = c.mint_attempt(SLUG,plan['manifest'],**plan['mint']);save_new(ROOT/'execution/opened.json',opened)
    result = token_measurement.run_prepared(plan,opened['attempt']['attempt_id'])
    save_new(ROOT/'execution/result.json',result)
    save_new(ROOT/'execution/receipt.json',c.measure(SLUG,result['payload']))
    save_new(ROOT/'execution/after.json',c.proposal(SLUG,authenticated=True))
    print('Filed fresh replication',result['payload']['value'],opened['attempt']['attempt_id'])

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);a=p.parse_args()
    build() if a.action == 'build' else run()
