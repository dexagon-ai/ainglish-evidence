"""Software regression only: dictionary order/metadata must not change encoded text cost."""
import hashlib
import json
from pathlib import Path
import subprocess
from unittest.mock import patch
from ainglish import measure
from audit import pairs_from

ROOT = Path(__file__).resolve().parent

def main():
    results, skipped = [], []
    with patch('tiktoken.load.read_file', side_effect=RuntimeError('No downloads permitted')):
        for path in sorted((ROOT / 'public-inputs').glob('*.json')):
            source = json.loads(path.read_text())
            try:
                pairs = pairs_from(source['manifest'])
            except ValueError as exc:
                skipped.append({'source': path.name, 'reason': str(exc)})
                continue
            expected = measure.token_delta(pairs, ['cl100k_base', 'o200k_base', 'p50k_base'])
            shapes = [
                [tuple(x) for x in pairs],
                [{'english': e, 'ainglish': a} for e, a in pairs],
                [{'ainglish': a, 'english': e} for e, a in pairs],
                [{'stratum': 'metadata-is-not-text', 'ainglish': a, 'english': e, 'id': i}
                 for i, (e, a) in enumerate(pairs)],
            ]
            for rows in shapes:
                assert measure.token_delta(rows, ['cl100k_base', 'o200k_base', 'p50k_base']) == expected, path.name
            results.append({'source': path.name, 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'pairs': len(pairs), 'equivalent_shapes': 5})
    rejected = 0
    for invalid in ['ab', {'english': 'text'}, {'english': 3, 'ainglish': 'text'},
                    [None, 'text'], ['one'], ['one', 'two', 'three']]:
        with patch('tiktoken.get_encoding', side_effect=AssertionError('Invalid row reached encoder')):
            try:
                measure.token_delta([['valid first', 'valid other'], invalid], ['cl100k_base'])
            except (ValueError, TypeError):
                rejected += 1
            else:
                raise AssertionError('Malformed row was accepted')
    commit = subprocess.run(['git', '-C', str(Path(measure.__file__).parents[2]), 'rev-parse', 'HEAD'],
                            check=True, text=True, capture_output=True).stdout.strip()
    report = {'kind': 'ainglish.token-row-shape-regression.v1', 'sdk_source_commit': commit,
        'measure_file_sha256': hashlib.sha256(Path(measure.__file__).read_bytes()).hexdigest(),
        'source_records_tested': len(results), 'pairs_tested': sum(x['pairs'] for x in results),
        'shape_variants': 5, 'malformed_rows_refused_before_encoder': rejected,
        'fixed_software_test_roster': ['cl100k_base', 'o200k_base', 'p50k_base'],
        'skipped': skipped, 'results': results,
        'boundary': 'Software input-normalisation regression over retained text, not a new measurement, independent replication, semantic audit or replay of each source tokenizer roster.'}
    with (ROOT / 'row-shape-regression.json').open('x') as f:
        json.dump(report, f, indent=2); f.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['results', 'skipped']}))

if __name__ == '__main__':
    main()
