"""Explicit preflight/mint/run/submit phases for the frozen token prerequisite."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ainglish import token_measurement
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent
PUBLIC_ID = 'a-ahnft6b6kb8qwkz1'
COMMITMENT = '396ffbe251fac5bbf3bb1ad0776148caa756ff54b831090a29a05c28ce51d902'


def write(name, value):
    (ROOT / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['preflight', 'mint', 'run', 'submit'])
    phase = parser.parse_args().phase
    plan = json.loads((ROOT / 'with-attachment-token-plan.json').read_text())
    assert plan['manifest_commitment'] == manifest_commitment(plan['manifest']) == COMMITMENT
    client = ainglish_client()
    original = json.loads((ROOT / 'inputs/proposals' / (PUBLIC_ID + '.json')).read_text())
    fresh = client.proposal(PUBLIC_ID, authenticated=True)
    assert fresh['public_id'] == PUBLIC_ID and fresh['stage'] in ['seconded', 'measured']
    for field in ['form', 'english_mapping', 'predicted_measurement', 'evidence_contract']:
        if fresh[field] != original[field]:
            raise SystemExit('STOP: proposal scientific fields changed: ' + field)
    if fresh['author_work_notices']['active'] is not None:
        raise SystemExit('STOP: review the new author notice before proceeding')
    suggestions = client.suggestions(proposal=PUBLIC_ID)
    eligible = [r for r in suggestions['suggestions'] if r.get('tier') == 'measurements'
                and r.get('evidence_work', {}).get('metric') == 'token_delta'
                and r.get('evidence_work', {}).get('state') == 'submit_original']
    if not eligible:
        raise SystemExit('STOP: no current original token prerequisite suggestion')
    slug = fresh['slug']
    limits = client.protocols()['measurement_submission']['manifest']['token_delta_limits']
    if phase in ['preflight', 'mint']:
        preflight = client.preflight_attempt(slug, plan['manifest'], **plan['mint'], proposal_revision=slug)
        write('with-attachment-preflight', preflight)
        assert preflight['accepted'] is True and preflight['manifest_commitment'] == COMMITMENT
        print('PREFLIGHT', preflight['accepted'], preflight['manifest_commitment'])
        if phase == 'preflight':
            return
        receipt_path = ROOT / 'with-attachment-attempt.json'
        if receipt_path.exists():
            raise SystemExit('STOP: an attempt receipt already exists; do not mint twice')
        receipt = client.mint_attempt(slug, plan['manifest'], **plan['mint'], proposal_revision=slug)
        write('with-attachment-attempt', receipt)
        print('MINT', json.dumps(receipt, ensure_ascii=False)[:2500])
        return
    receipt = json.loads((ROOT / 'with-attachment-attempt.json').read_text())
    attempt_id = receipt['attempt']['attempt_id']
    if phase == 'run':
        if (ROOT / 'with-attachment-payload.json').exists():
            raise SystemExit('STOP: a result already exists; do not rerun it')
        payload = token_measurement.run_prepared(plan, attempt_id, token_limits=limits)
        write('with-attachment-payload', payload)
        print('RUN', json.dumps({k:payload['payload'].get(k) for k in ['metric', 'value', 'value_lo', 'value_hi', 'per_member', 'attempt_id']}))
        return
    if (ROOT / 'with-attachment-submission.json').exists():
        raise SystemExit('STOP: a submission receipt already exists')
    payload = json.loads((ROOT / 'with-attachment-payload.json').read_text())['payload']
    assert payload['attempt_id'] == attempt_id
    result = client.measure(slug, payload)
    write('with-attachment-submission', result)
    after = client.proposal(PUBLIC_ID)
    write('with-attachment-after', after)
    client.suggestions(proposal=PUBLIC_ID)
    print('SUBMIT', json.dumps(result, ensure_ascii=False)[:2200])
    print('AFTER', after['stage'], after['evidence_readiness']['note'])


if __name__ == '__main__':
    main()
