"""Preregister and execute one bounded token prerequisite; no reader/GPU calls."""
import json
from pathlib import Path
from unittest.mock import patch
from ainglish import token_measurement
from local_colony_auth import ainglish_client
ROOT=Path(__file__).resolve().parent
def save(name,value):
    with (ROOT/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2)
if __name__=='__main__':
    assert not (ROOT/'since-token.opened.json').exists(),'mint exists; recover, never repeat counting under a new attempt'
    c=ainglish_client();s=c.suggestions()
    ns=c.proposal_slug_history('a-hjhq14a5ew4khaqp');p=c.proposal(ns['current_slug'],authenticated=True)
    assert p['stage'] in ['seconded','measured'] and 'token_delta' not in p['evidence_readiness']['satisfied']
    plan=json.loads((ROOT/'since-token.plan.json').read_text())
    preflight=c.preflight_attempt(p['slug'],plan['manifest'],**plan['mint'])
    save('since-token.preflight.json',preflight)
    opened=c.mint_attempt(p['slug'],plan['manifest'],**plan['mint'])
    save('since-token.opened.json',opened)
    aid=opened['attempt']['attempt_id'];print('MINTED BEFORE COUNTS',aid,flush=True)
    with patch('tiktoken.load.read_file',side_effect=RuntimeError('Downloads prohibited; cached encodings only')):
        result=token_measurement.run_prepared(plan,aid)
    save('since-token.result.json',result)
    response=c.measure(p['slug'],result['payload'])
    save('since-token.submitted.json',response)
    print('FILED',aid,result['payload']['value'],result['payload']['per_member'],flush=True)
