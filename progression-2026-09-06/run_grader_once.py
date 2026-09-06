"""Mint before cached encoding counts, submit every admitted direction once."""
import hashlib
import json
from unittest.mock import patch
from ainglish import token_measurement
from local_colony_auth import ainglish_client
from since_study import ROOT, save


def main():
    assert not (ROOT/'grader.opened.json').exists(), 'Reconcile existing attempt; no recount retry'
    c = ainglish_client()
    c.suggestions(proposal='a-ta5q563ee29j9fcw')
    p = c.proposal(c.proposal_slug_history('a-ta5q563ee29j9fcw')['current_slug'],authenticated=True)
    plan = json.loads((ROOT/'grader.plan.json').read_text())
    assert p['stage'] in ['seconded','measured'] and p['publication_status'] == 'visible'
    assert hashlib.sha256(p['english_mapping'].encode()).hexdigest() == plan['mint']['planned_sample']['mapping_sha256']
    save('grader.preflight.json',c.preflight_attempt(p['slug'],plan['manifest'],**plan['mint']))
    opened = c.mint_attempt(p['slug'],plan['manifest'],**plan['mint']); save('grader.opened.json',opened)
    aid = opened['attempt']['attempt_id']; print('Minted before counts',aid,flush=True)
    try:
        with patch('tiktoken.load.read_file',side_effect=RuntimeError('Cached encodings only; no downloads')):
            result = token_measurement.run_prepared(plan,aid)
            token_measurement.verify_payload(result['payload'])
    except BaseException as exc:
        save('grader.abort.json',c.abort_attempt(aid,'Cached count gate failed',{'type':type(exc).__name__},failed_gate_kind='harness_error'))
        raise
    save('grader.result.json',result)
    save('grader.submitted.json',c.measure(p['slug'],result['payload']))
    save('grader.server.json',c.attempt(aid))
    print('Filed',result['payload']['value'],result['payload']['per_member'],flush=True)


if __name__ == '__main__':main()
