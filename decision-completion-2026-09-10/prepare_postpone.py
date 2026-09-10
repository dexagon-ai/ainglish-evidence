"""Reconcile an unspent 0.2.58 original with 0.2.59; never mint or infer."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ainglish import panel
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client


def main(source, out):
    spec = json.loads((source / 'runspec.json').read_text())
    old = json.loads((source / 'planned-manifest.json').read_text())
    lock = json.loads((source / 'claim-lock.json').read_text())
    if (source / 'execution').exists() or out.exists():
        raise SystemExit('Inspect existing execution/preparation; never overwrite or retry.')
    c = ainglish_client()
    c.whoami()
    suggestions = c.suggestions(proposal=spec['public_id'])
    p = c.proposal(spec['slug'], authenticated=True)
    assert {k: p[k] for k in lock} == lock, 'Claim changed'
    assert p['stage'] in ('seconded', 'measured')
    assert any(x.get('metric') == spec['metric'] for x in suggestions['suggestions'])
    assert not spec.get('replicates_hash'), 'This is an additional original, not a replication'
    bound = panel.prepare_reader_instruments(spec)  # Cached metadata reads, no model calls.
    new = panel._planned_panel_manifest(bound)
    changed = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
    assert changed == ['harness'], changed
    assert old['harness'] == 'ainglish-panel/0.2.58'
    assert new['harness'] == 'ainglish-panel/0.2.59'
    preflight = c.preflight_attempt(
        spec['slug'], new,
        **panel._attempt_settings(bound['attempt'], [panel.calibration_gate_statement(bound)]),
    )
    assert preflight['accepted'] and preflight['effect'] == 'none'
    report = {
        'kind': 'ainglish.unspent-preparation-reconciliation.v1',
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'old_manifest_commitment': manifest_commitment(old),
        'new_manifest_commitment': manifest_commitment(new),
        'changed_manifest_fields': changed,
        'items_sha256': hashlib.sha256(json.dumps(bound['items'], sort_keys=True,
            separators=(',', ':'), ensure_ascii=False).encode()).hexdigest(),
        'windows_free_bytes': shutil.disk_usage('/mnt/c').free,
        'start_threshold_bytes': 22 * 1024**3,
        'stop_threshold_bytes': 15 * 1024**3,
        'qualification_valid_until': [x['valid_until'] for x in bound['reader_qualifications']],
        'preflight': {k: preflight[k] for k in ('kind', 'accepted', 'effect', 'manifest_commitment')},
        'attempt_minted': False,
        'calibration_calls': 0,
        'target_calls': 0,
        'independent_replication_executor_confirmed': False,
        'next_action': 'Confirm independent access to the exact reader roster before spending; then refresh live claim, cost, discussion, qualifications, resources and preflight, publish the complete execution freeze, mint once and execute the accepted careful-English component only.',
    }
    out.mkdir()
    for name, value in (('runspec.json', bound), ('planned-manifest.json', new), ('reconciliation.json', report)):
        with (out / name).open('x') as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    main(args.source, args.out)
