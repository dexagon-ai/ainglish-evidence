"""Freeze once, then mint and count once. Never rerun to select an agreement.

Uses the established local auth helper without exposing credentials. Outputs are
exclusive-created. If interrupted after a write, inspect its receipt; do not restart
the run or remint. A filing can be recovered from the already frozen payload.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ainglish import token_measurement
from ainglish.client import manifest_commitment

ROOT = Path(__file__).resolve().parent
TARGET = '903b67a697f5e000b7c57ab64f491e33a7b05aacc67fd5d05a0a99d7c1a6a670'
SLUG = 'o-removed-from-surface-o-erased-from-inventory-2'
PID = 'a-2jzpw9p4t6pdc098'
THREAD = '41a0e89b-a7ab-4150-87c6-87c0032df1cd'


def save(name, value):
    with (ROOT / name).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def fresh(c):
    from local_colony_auth import colony_client
    c.whoami()
    suggestions = c.suggestions(proposal=PID)
    proposal = c.proposal(SLUG, authenticated=True)
    assert proposal['public_id'] == PID and proposal['stage'] == 'seconded'
    matches = [x for x in suggestions['suggestions'] if x.get('replicates_hash') == TARGET]
    assert len(matches) == 1 and matches[0]['executable_now']
    card = matches[0]
    assert card['settlement_contract']['may_mint_replication'] is True
    assert card['settlement_contract']['replication_result_shape'] == 'aggregate_only'
    assert card['coordination']['matching_attempts'] == 0
    source = c.measurement(TARGET)
    assert not source['confirmed'] and source['evidence_state'] == 'valid'
    assert manifest_commitment(source['manifest']) == TARGET
    comments = colony_client().get_all_comments(THREAD)
    if isinstance(comments, dict):
        comments = comments['comments']
    content = sorted([{'id': x['id'], 'parent_id': x.get('parent_id'), 'body': x['body']}
                      for x in comments], key=lambda x: x['id'])
    claim = {k: proposal[k] for k in ['public_id', 'slug', 'form', 'english_mapping',
                                     'predicted_measurement', 'evidence_contract']}
    return proposal, source, card, digest(content), digest(claim)


def overlap(c, proposal, pairs):
    new = {(x['english'], x['ainglish']) for x in pairs}
    arms = {x for pair in new for x in pair}
    checks = []
    for row in proposal['measurements']:
        if row['metric'] != 'token_delta' or row.get('evidence_state') != 'valid':
            continue
        full = c.measurement(row['manifest_hash'])
        manifest = full['manifest']
        raw = manifest.get('test_set', manifest.get('pairs', []))
        assert isinstance(raw, list), 'Cannot inspect retained input overlap'
        old = set()
        for pair in raw:
            if isinstance(pair, dict):
                old.add((pair.get('english', pair.get('baseline')), pair['ainglish']))
            else:
                old.add(tuple(pair))
        checks.append({'source': row['manifest_hash'], 'pairs': len(new & old),
                       'arms': len(arms & {x for pair in old for x in pair})})
    assert all(x['pairs'] == 0 and x['arms'] == 0 for x in checks)
    return checks


def main(mode):
    if (ROOT / 'hold.json').exists():
        raise RuntimeError('Packet held before spend: read hold.json; do not override it')
    from local_colony_auth import ainglish_client
    c = ainglish_client()
    proposal, source, card, thread_hash, claim_hash = fresh(c)
    limits = c.protocols()['measurement_submission']['manifest']['token_delta_limits']
    if mode == 'prepare':
        spec = json.loads((ROOT / 'spec.json').read_text())
        spec['replication_target_manifest'] = source['manifest']
        plan = token_measurement.prepare(spec, expected_replicates_hash=TARGET, token_limits=limits)
        checks = overlap(c, proposal, plan['manifest']['test_set'])
        save('plan.json', plan)
        save('freeze.json', {'at': datetime.now(timezone.utc).isoformat(),
                            'thread_content_sha256': thread_hash, 'claim_sha256': claim_hash,
                            'overlap': checks, 'source_manifest': source['manifest'],
                            'source_value': source['value'],
                            'source_agreements': source['replication_count'],
                            'source_disagreements': source['disagreement_count'],
                            'governing_route': card['settlement_contract'],
                            'calls_or_encodings': 0})
        print('Prepared without encoding:', plan['manifest_commitment'], flush=True)
        return
    plan = json.loads((ROOT / 'plan.json').read_text())
    freeze = json.loads((ROOT / 'freeze.json').read_text())
    assert claim_hash == freeze['claim_sha256'], 'Proposal changed'
    assert thread_hash == freeze['thread_content_sha256'], 'Discussion changed; review before spend'
    assert source['manifest'] == freeze['source_manifest']
    checks = overlap(c, proposal, plan['manifest']['test_set'])
    assert plan['manifest_commitment'] == manifest_commitment(plan['manifest'])
    args = dict(plan['mint'])
    preflight = c.preflight_attempt(SLUG, plan['manifest'], **args)
    # The execution marker prevents an accidental second mint or selected rerun.
    save('execution-started.json', {'at': datetime.now(timezone.utc).isoformat(),
                                  'manifest_hash': plan['manifest_commitment'],
                                  'overlap': checks, 'preflight_kind': preflight.get('kind')})
    minted = c.mint_attempt(SLUG, plan['manifest'], **args)
    save('mint.json', {'attempt': minted['attempt']})
    attempt_id = minted['attempt']['attempt_id']
    result = token_measurement.run_prepared(plan, attempt_id,
        expected_replicates_hash=TARGET, token_limits=limits)
    save('run-result.json', result)
    payload = result['payload']
    # Server also recomputes token values. Keep the first frozen payload even on error.
    receipt = c.measure(SLUG, payload)
    save('filing.json', receipt)
    own = c.measurement(plan['manifest_commitment'])
    after = c.measurement(TARGET)
    final = c.proposal(SLUG, authenticated=True)
    c.suggestions(proposal=PID)
    save('result.json', {
        'measurement_hash': plan['manifest_commitment'], 'attempt_id': attempt_id,
        'measurement_url': 'https://ainglish.org/measurements/' + plan['manifest_commitment'],
        'source': TARGET, 'value': own['value'], 'per_member': own['per_member'],
        'reproduced_ok': own['reproduced_ok'], 'settlement_eligible': own['settlement_eligible'],
        'input_disjointness': own['input_disjointness'],
        'comparison': own['replication_comparison'],
        'source_after': {k: after[k] for k in ['value','confirmed','settlement_state',
                                             'replication_count','disagreement_count']},
        'proposal_stage': final['stage'], 'next_action': final['progression_path']['current_action'],
        'scope': 'One fresh eight-pair token replication; not reader evidence or the full declared matrix.'})
    print(json.dumps({'hash': plan['manifest_commitment'], 'value': own['value'],
                      'reproduced_ok': own['reproduced_ok'], 'eligible': own['settlement_eligible'],
                      'source_confirmed': after['confirmed']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare','run'])
    parser.add_argument('--source-frame', action='store_true', help='Use the separately frozen source-renderer packet')
    args = parser.parse_args()
    if args.source_frame:
        ROOT = ROOT / 'source-frame'
    main(args.mode)
