"""Read-only local model identity binding. No inference, qualification run, or attempt mint.

Unlike build.py's file-only preview, this explicitly reads the current Ollama registry. Only
GET /api/tags is permitted. It uses the SDK's real preparation path, then forbids all sockets
while deriving the proposed manifest. Repeat before any eventual authorized launch.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from unittest.mock import patch

from ainglish import panel, reader_qualification

ROOT = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def main(items_url):
    if not re.fullmatch(r'https://raw\.githubusercontent\.com/dexagon-ai/ainglish-evidence/[0-9a-f]{40}/choose-any-final-package-2026-09-15/items\.json', items_url):
        raise SystemExit('Requires this package items.json at an immutable full Git commit URL')
    spec = json.loads((ROOT/'reader-config-review.json').read_text())
    spec['items_url'] = items_url
    catalog_reads = []
    wanted = {e['model'] for e in spec['panel']}
    def catalog_only(req, timeout=None):
        if req.get_method() != 'GET' or req.full_url != 'http://127.0.0.1:11434/api/tags':
            raise AssertionError('Only local read-only model catalog requests are permitted')
        raw = panel._fetch(req)
        rows = [{k: row.get(k) for k in ['name', 'model', 'digest', 'details']}
                for row in raw['models'] if row.get('name') in wanted or row.get('model') in wanted]
        catalog_reads.append({'url': req.full_url, 'method': req.get_method(), 'selected_models': rows})
        return raw
    bound = panel.prepare_reader_instruments(deepcopy(spec), fetch_fn=catalog_only)
    now = datetime.now(timezone.utc)
    qualifications = {q['roster_id']: q for q in bound['reader_qualifications']}
    checks = []
    for endpoint in bound['panel']:
        receipt = panel.reader_receipt(endpoint)
        roster = endpoint['name'] + '@' + endpoint['precision']
        q = reader_qualification.validate(qualifications[roster])
        sha = hashlib.sha256(canonical(receipt)).hexdigest()
        assert q['settings_sha256'] == sha, 'Qualification settings changed'
        assert q['reader']['model_digest'] == receipt['model_digest']
        assert q['result']['passed']
        assert datetime.fromisoformat(q['qualified_at']) <= now < datetime.fromisoformat(q['valid_until'])
        checks.append({'roster_id': roster, 'model_digest': receipt['model_digest'],
                       'settings_sha256': sha, 'qualification_matches': True,
                       'qualified_at': q['qualified_at'], 'valid_until': q['valid_until']})
    items = json.loads((ROOT/'items.json').read_text())
    assert hashlib.sha256(canonical(items)).hexdigest() == bound['items_sha256']
    remote_items, remote_digest = panel.fetch_items(items_url, bound['items_sha256'])
    assert remote_items == items and remote_digest == bound['items_sha256']
    with patch('socket.socket', side_effect=AssertionError('Network forbidden during preview')):
        planned = panel._planned_panel_manifest(dict(deepcopy(bound), items=items))
    assert planned['instrument_preparation']['binding'] != 'unbound'
    assert 'items' not in planned and planned['items_url'] == items_url
    assert all(r['model_digest'] and r['digest_source'] == 'ollama:/api/tags' for r in planned['readers'])
    for name, value in [('prepared-reader-config-review.json', bound), ('planned-manifest.json', planned),
                        ('LIVE-IDENTITY-CHECK.json', {
                            'kind': 'choose-any.live-identity-check.v1', 'checked_at': now.isoformat(),
                            'status': 'EXISTING_QUALIFICATIONS_MATCH_CATALOG_NOT_LAUNCH_APPROVAL',
                            'checks': checks, 'catalog_reads': catalog_reads,
                            'immutable_items_url': items_url, 'remote_items_sha256_verified': remote_digest,
                            'target_reader_calls': 0, 'new_qualification_calls': 0, 'minted_attempts': 0})]:
        (ROOT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'BOUND_EXISTING_QUALIFICATIONS_MATCH', 'checked_at': now.isoformat(),
                      'catalog_gets': len(catalog_reads), 'reader_calls': 0, 'attempts_minted': 0}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--items-url', required=True)
    main(ap.parse_args().items_url)
