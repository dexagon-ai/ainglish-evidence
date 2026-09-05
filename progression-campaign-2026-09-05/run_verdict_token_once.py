"""Execute exactly one frozen canonical cost original, retaining failures and receipts."""
import json
from pathlib import Path
from unittest.mock import patch
from ainglish import token_measurement
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent

def save(name, value):
    with (ROOT / name).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False); f.write('\n')

def main():
    assert not (ROOT / 'verdict-token.opened.json').exists(), 'Existing attempt: recover it, do not re-mint'
    c = ainglish_client()
    s = c.suggestions(proposal='a-6974j2deetg3rcb5')
    p = c.proposal(c.proposal_slug_history('a-6974j2deetg3rcb5')['current_slug'], authenticated=True)
    assert p['stage'] in ['seconded', 'measured'] and not p.get('superseded_by')
    assert any(x['metric'] == 'token_delta' and x['state'] == 'submit_original' for x in p['evidence_readiness']['work_items'])
    plan = json.loads((ROOT / 'verdict-token.plan.json').read_text())
    save('verdict-token.before.json', {'proposal': p, 'suggestions': s})
    preflight = c.preflight_attempt(p['slug'], plan['manifest'], **plan['mint'])
    save('verdict-token.preflight.json', preflight)
    opened = c.mint_attempt(p['slug'], plan['manifest'], **plan['mint'])
    save('verdict-token.opened.json', opened)
    attempt = opened['attempt']['attempt_id']
    print('MINTED BEFORE COUNTS', attempt, flush=True)
    try:
        with patch('tiktoken.load.read_file', side_effect=RuntimeError('Only cached encodings; no downloads')):
            result = token_measurement.run_prepared(plan, attempt)
    except Exception as exc:
        save('verdict-token.aborted.json', c.abort_attempt(attempt, 'Cached encoding/countability gate failed',
            {'exception': type(exc).__name__, 'message': str(exc)}, failed_gate_kind='harness_error'))
        raise
    save('verdict-token.result.json', result)
    response = c.measure(p['slug'], result['payload'])
    save('verdict-token.submitted.json', response)
    print('FILED', attempt, result['payload']['value'], result['payload']['per_member'], flush=True)

if __name__ == '__main__':
    main()
