"""Reconcile two retained raw-answer journals with frozen gold and served bits.

No inference. This checks scored-answer transcription, not whether the frozen gold
or questions represent the claimed semantics. Only fixed public artifact URLs are
fetched; no credentials or model endpoints are used.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from ainglish.client import manifest_commitment

CASES = {
    'eb9044ee': 'progression-studies-2026-09-05/some-primary.attempt-ae9c9975-36a7-4dbe-b6ad-8517618391a5.cells.json',
    '2f85f08c': 'night-progression-2026-09-07/readers/verdict-careful/execution/verdict-careful.attempt-b7ce3677-c684-4db9-978b-5547027e6bd5.cells.json',
}


def fetch(url):
    if not url.startswith('https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/'):
        raise ValueError('this audit only reads the named public evidence repository')
    with urlopen(url, timeout=30) as response:
        body = response.read(8_000_001)
    if len(body) > 8_000_000:
        raise ValueError('artifact exceeds the bounded audit size')
    return json.loads(body), hashlib.sha256(body).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    results = []
    for prefix, path in CASES.items():
        source = json.loads(next(args.sources.glob(prefix + '*.json')).read_text())
        manifest = source['manifest']
        artifact = 'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/a673349/' + path
        raw, raw_hash = fetch(artifact)
        item_file, file_hash = fetch(manifest['items_url'])
        items = item_file['items'] if isinstance(item_file, dict) else item_file
        content_hash = hashlib.sha256(json.dumps(items, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        index = {i['id']: i for i in items}
        journal = {(c['item_id'], c['reader']): c for c in source['interval_provenance_attestation']['cells']}
        keys = [(c['item_id'], c['reader']) for c in raw['rows']]
        errors = []
        for row in raw['rows']:
            target = index[row['item_id']]['answer']
            if row['answer'] is None:
                correct = None
            else:
                correct = str(row['answer']).casefold() == str(target).casefold()
            served = journal[(row['item_id'], row['reader'])]
            if row['expected'] != target or row['correct'] != correct or served['correct'] != correct or served['arm'] != row['arm']:
                errors.append({'item': row['item_id'], 'reader': row['reader']})
        results.append({'manifest_hash': source['manifest_hash'], 'manifest_hash_matches': manifest_commitment(manifest) == source['manifest_hash'],
                        'raw_journal_url': artifact, 'raw_file_sha256': raw_hash,
                        'items_url': manifest['items_url'], 'items_file_sha256': file_hash,
                        'items_content_hash_matches': content_hash == manifest['items_sha256'],
                        'real_cells': len(keys), 'population_matches': len(keys) == len(set(keys)) and set(keys) == set(journal),
                        'raw_gold_or_served_bit_mismatches': errors})
    with args.report.open('x') as stream:
        json.dump({'kind': 'ainglish.raw-answer-reconciliation.v1', 'reports': results, 'boundary': __doc__}, stream, indent=2)
        stream.write('\n')
    print([(r['manifest_hash'][:12], r['real_cells'], r['items_content_hash_matches'], len(r['raw_gold_or_served_bit_mismatches'])) for r in results])


if __name__ == '__main__':
    main()
