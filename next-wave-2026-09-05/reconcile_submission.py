"""One exact-payload delivery after an HTTP 520; no new measurement or reader calls."""
import json
from pathlib import Path
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from prepare import save

ROOT = Path(__file__).resolve().parent
ATTEMPT = '3c18b2a0-c7e5-4345-94d5-a2678ab4f592'

def main():
    assert not (ROOT/'verdict.bare.delivery-reconciliation.json').exists()
    client = ainglish_client()
    state = client.attempt(ATTEMPT)
    payload = json.loads((ROOT/f'verdict.bare.attempt-{ATTEMPT}.measurement.json').read_text())
    digest = manifest_commitment(payload['manifest'])
    assert payload['attempt_id'] == ATTEMPT and digest == state['pin']['manifest_commitment']
    assert state['state'] in ['open', 'completed']
    if state['state'] == 'open':
        response = client.measure(state['proposal'], payload)
    else:
        response = {'already_completed': True}
    current = client.attempt(ATTEMPT)
    save('verdict.bare.delivery-reconciliation.json', {'before': state, 'response': response, 'after': current,
         'new_reader_calls': 0, 'payload_changed': False})
    assert current['state'] == 'completed'
    summary = {k: payload.get(k) for k in ['metric', 'value', 'value_lo', 'value_hi', 'arms', 'per_member', 'stratum_results', 'attempt_id']}
    summary.update(manifest_hash=digest, server=client.measurement(digest))
    save('verdict.bare.result.json', summary)
    print('Existing observation filed once:', digest, summary['value'])

if __name__ == '__main__': main()
