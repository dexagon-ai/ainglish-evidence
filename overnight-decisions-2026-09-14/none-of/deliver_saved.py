"""Deliver one finished result, never rerun inference. Read-only by default.

Dexagon-local helper. --submit-after-reviewed-deployment COMMIT means the caller has
independently checked that COMMIT contains PR621 (or an equivalent reviewed fix), and
that any proxy ceiling permits this envelope. A changed health hash alone is NOT proof.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen
from ainglish.client import AinglishError, manifest_commitment
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent
PID = 'a-egz4k62p8x713bt5'
ATTEMPT = 'bd524eaf-e5de-4f3b-8808-3910f8d12b17'
MANIFEST = '03604fc182efb10175bb4598b1cff40fd606708e7a0fb8aba66e94800af92d43'
FILE_SHA = '64cd5a78a6b57ff29dc25d021a152c2d01ce92e300ae9e1222b8e4f16229ef89'
KNOWN_OLD = 'b3c0d6661d7e3747c39c26bc08793f64f87631df'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submit-after-reviewed-deployment', metavar='COMMIT')
    args = parser.parse_args()
    raw = (ROOT / f'consequences.runspec.json.attempt-{ATTEMPT}.measurement.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FILE_SHA, 'Saved result bytes changed; stop.'
    result = json.loads(raw)
    assert result['attempt_id'] == ATTEMPT and manifest_commitment(result['manifest']) == MANIFEST
    client = ainglish_client()
    attempt = client.attempt(ATTEMPT)
    assert attempt['pin']['manifest_commitment'] == MANIFEST
    if attempt['state'] == 'completed':
        assert attempt['measurement_ref'] == MANIFEST
        measured = client.measurement(MANIFEST)
        assert measured['value'] == result['value']
        print('Already delivered:', MANIFEST, 'No submission or inference performed.')
        return
    assert attempt['state'] == 'open' and attempt['measurement_ref'] is None
    with urlopen('https://ainglish.org/api/v1/health', timeout=30) as response:
        deployed = json.load(response)['deployment']['commit']
    print('Saved result:', len(raw), 'bytes; ledger:', attempt['state'], '; deployment:', deployed)
    if not args.submit_after_reviewed_deployment:
        print('Read-only: awaiting independently reviewed transport deployment. No inference or write.')
        return
    expected = args.submit_after_reviewed_deployment
    assert re.fullmatch(r'[0-9a-f]{40}', expected) and expected != KNOWN_OLD
    assert deployed == expected, 'Deployment differs from the externally reviewed commit; stop.'
    client.suggestions(proposal=PID, view='full')
    try:
        current = client.proposal(PID, authenticated=True)
    except AinglishError as error:
        if error.status != 500:
            raise
        current = client.proposal(PID)
    frozen = json.loads((ROOT / 'FROZEN-PROPOSAL.json').read_text())
    assert current['public_id'] == PID and not current.get('superseded_by')
    for field in ['slug', 'form', 'english_mapping', 'predicted_measurement', 'evidence_contract']:
        assert current[field] == frozen[field], 'Changed scientific proposal: ' + field
    assert current['stage'] in ['seconded', 'measured']
    # The proposer's later decision-request advice does not erase this already-run
    # prospective attempt. Deliver all of it; do not mint a successor or alter cells.
    receipt = client.measure(current['slug'], result)
    (ROOT / 'consequences.submission-receipt.json').write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    reconciled = client.attempt(ATTEMPT)
    assert reconciled['state'] == 'completed' and reconciled['measurement_ref'] == MANIFEST
    (ROOT / 'consequences.ledger-state.json').write_text(json.dumps(reconciled, indent=2) + '\n')
    client.suggestions(proposal=PID, view='full')
    print('Delivered unchanged result:', MANIFEST)

if __name__ == '__main__':
    main()
