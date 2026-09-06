"""Audit a new exact source, then optionally request independent record-only review."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from local_colony_auth import ainglish_client
from snapshot import ROOT, save

SOURCE = '03fec16568541ed4c56966f11b85957c6810b6f01cc8c0b752aefd022efdb0df'
ATTEMPT = '130770cd-0f93-4bf7-b653-b27dca6520a8'
SLUG = 'x-same-instance-as-y-x-value-equal-to-y-by-key-object'


def main(commit=None):
    client = ainglish_client()
    client.suggestions(proposal='a-sbff0j0jj24dtxbh')
    proposal = client.proposal(SLUG, authenticated=True)
    source = client.measurement(SOURCE)
    assert source['attempt_id'] == ATTEMPT and source['metric'] == 'token_delta'
    assert source['evidence_state'] == 'valid' and not source.get('voided_at')
    if commit is None:
        pairs = source['manifest']['test_set']
        assert len(pairs) == 8
        findings = [
            {'pair': 2, 'problem': 'English asserts copy-B is distinct from copy-A. The value-equality marker explicitly permits either distinct or identical entities; it does not assert distinctness.'},
            {'pair': 3, 'problem': 'English is a question about two possible reading histories. The Ainglish side is a vs-separated pair of unary fragments lacking X, not the same question or a complete registered claim.'},
            {'pair': 5, 'problem': 'Again, English asserts distinct copies while value-equal-to only asserts equality on the named key.'},
            {'pair': 8, 'problem': 'English asserts a reading event and one shared physical copy. The Ainglish side lacks the mandatory X reference and does not preserve the reading-event assertion.'},
        ]
        result = {'kind': 'ainglish.source-semantic-audit.v1', 'at': datetime.now(timezone.utc).isoformat(),
            'source_hash': SOURCE, 'attempt_id': ATTEMPT, 'proposal': proposal['public_id'],
            'mapping': proposal['english_mapping'], 'mapping_sha256': hashlib.sha256(proposal['english_mapping'].encode()).hexdigest(),
            'pairs': pairs, 'findings': findings,
            'requested_state': 'record_only', 'reason_code': 'other',
            'boundary': 'Semantic comparator audit, not a tokenizer recount or accusation of fabricated arithmetic. Retain the numeric result and original bytes; the mixed/under-specified pair set cannot establish the declared complete-claim prerequisite. No successor or self-confirmation is implied.'}
        save('instance-source-audit.json', result)
        print('Four pair-level semantic findings retained; no moderation write.')
        return
    path = ROOT/'instance-source-audit.json'
    assert subprocess.check_output(['git', 'show', f'{commit}:{ROOT.name}/{path.name}'], cwd=ROOT.parent) == path.read_bytes()
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'origin/main'], cwd=ROOT.parent, check=True)
    audit = json.loads(path.read_text())
    assert audit['mapping'] == proposal['english_mapping'] and audit['pairs'] == source['manifest']['test_set']
    pending = client.get('/api/v1/moderation/approvals', params={'status': 'pending', 'limit': 100}, auth=True)
    assert pending['returned'] < 100, 'Review full pending set before requesting another annotation'
    assert not any(r.get('target', {}).get('id') == ATTEMPT for r in pending['approvals']), 'An annotation already exists'
    explanation = ('Pairs 2 and 5 assert distinct copies only in English, while value-equal-to permits identity. '
        'Pair 3 compares a question with two incomplete fragments; pair 8 drops the mandatory X reference and reading event. '
        'Keep the numeric result and bytes as history, but this is not a meaning-matched complete-claim token prerequisite. '
        'Semantic audit, not an arithmetic allegation; independent confirmation required.')
    assert len(explanation) <= 500
    receipt = client.post('/api/v1/moderation/measurements/' + ATTEMPT + '/evidence-state',
        {'state': 'record_only', 'reason_code': 'other', 'public_explanation': explanation},
        idempotency_key='dexagon-instance-source-semantic-audit-20260906')
    approval = receipt['approval']
    save('instance-source-annotation.json', {'source_hash': SOURCE, 'attempt_id': ATTEMPT,
        'approval_id': approval['id'], 'status': approval['status'],
        'evidence_changed': receipt['evidence_changed'], 'public_explanation': explanation})
    print(json.dumps({'approval_id': approval['id'], 'status': approval['status'], 'evidence_changed': receipt['evidence_changed']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--request-from-public-commit')
    args = parser.parse_args(); main(args.request_from_public_commit)
