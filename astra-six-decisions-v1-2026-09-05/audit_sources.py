#!/usr/bin/env python3
"""Recount retained public inputs; no API writes, reader calls, or new experiments.

Run in the existing developer environment with its three cached tiktoken encodings.
Generated reports are diagnostic receipts, not fresh-input replications.
"""
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path

import tiktoken

ROOT = Path(__file__).resolve().parent
TOKEN_HASHES = (
    'fc4685f26b41e8b97cf85660cc4139d103e8ca9de63b2d73b1ff0c24426e6f7f',
    'dadbc20f490757f3a43a8e9185c01a9b01b5a3a770ced34223fa998a1c377d88',
)


def read(name):
    return json.loads((ROOT / name).read_text())


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    sources = []
    for path in sorted(ROOT.glob('*.measurement.json')):
        if len(path.name.split('.')[0]) != 64:
            continue  # Saved submission payloads are not served source-measurement records.
        m = read(path.name)
        manifest = m['manifest']
        item_path = ROOT / (m['manifest_hash'] + '.source-items.json')
        items = manifest.get('items', manifest.get('test_set'))
        source_kind = 'manifest.items' if 'items' in manifest else 'manifest.test_set'
        if items is None and item_path.exists():
            items = read(item_path.name)
            source_kind = 'retained items_url response'
        if items is not None and not item_path.exists():
            write(item_path.name, items)
        real = [r for r in (items or []) if not r.get('calibration')]
        sources.append({
            'manifest_hash': m['manifest_hash'], 'attempt_id': m['attempt_id'],
            'source_file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'metric': m['metric'], 'value': m['value'], 'submitter': m['submitter'],
            'backfilled': m['attempt'].get('backfilled'),
            'comparison_identity': manifest.get('comparison_identity'),
            'estimand_contract': manifest.get('estimand_contract'),
            'input_source': source_kind if items is not None else 'not retained here',
            'source_recoverable': items is not None,
            'items': len(items) if items is not None else None,
            'real_items': len(real) if items is not None else None,
            'calibration_items': len(items) - len(real) if items is not None else None,
            'comparator_item_counts': dict(Counter(
                r.get('strata', {}).get('comparator', 'not item-declared') for r in real)),
            'identical_real_arm_texts': sum(r.get('english') == r.get('ainglish') for r in real),
        })
    write('source-audit.json', {
        'kind': 'ainglish.retained-source-audit.v1', 'sources': sources,
        'boundary': 'Input availability and declared scope only. Missing modern declarations do not invalidate legacy evidence.',
    })

    # Correct an earlier local diagnostic which missed the legacy inline test_set key.
    # The actual downloaded measurement bytes and their historical pins remain untouched.
    snapshot = read('snapshot.json')
    by_hash = {r['manifest_hash']: r for r in sources}
    for proposal in snapshot['proposals'].values():
        for target in proposal['targets']:
            audit = by_hash[target['manifest_hash']]
            target['source_recoverable'] = audit['source_recoverable']
            target['items'] = audit['items']
            target['input_source'] = audit['input_source']
    snapshot['local_diagnostic_correction'] = (
        'Input recoverability was re-derived by audit_sources.py, including legacy manifest.test_set. '
        'The original live-state timestamp and served source records are unchanged.')
    write('snapshot.json', snapshot)

    replays = []
    for h in TOKEN_HASHES:
        m = read(h + '.measurement.json')
        cells = {}
        for name in ('cl100k_base', 'o200k_base', 'p50k_base'):
            enc = tiktoken.get_encoding(name)
            deltas = [len(enc.encode(r['ainglish'])) - len(enc.encode(r['english']))
                      for r in m['manifest']['test_set']]
            cells[name] = {'deltas': deltas, 'mean': sum(deltas) / len(deltas)}
        replays.append({'manifest_hash': h, 'attempt_id': m['attempt_id'],
                        'filed_value': m['value'], 'per_tokenizer': cells,
                        'pooled_mean': sum(r['mean'] for r in cells.values()) / len(cells)})
    assert replays[0]['pooled_mean'] == 0.5
    assert replays[1]['pooled_mean'] == 5.0
    assert all(r['pooled_mean'] != r['filed_value'] for r in replays)
    write('token-recount.json', {
        'kind': 'ainglish.same-input-diagnostic.v1',
        'tiktoken_version': importlib.metadata.version('tiktoken'),
        'formula': 'mean(count(Ainglish) - count(English)) over the published pairs and named encodings',
        'replays': replays,
        'boundary': 'Same-input diagnostic only, not an independent fresh-input replication or authority to alter either record.',
    })
    print(json.dumps({'sources_audited': len(sources), 'token_recounts': len(replays)}))


if __name__ == '__main__':
    main()
