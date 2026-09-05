"""Same-input audit of existing cost evidence, not a new scientific replication."""
from collections import Counter
import importlib.metadata
import json
from pathlib import Path
import re
from ainglish.measure import token_delta

ROOT = Path(__file__).resolve().parent
GROUPS = {
    'mean': ['d00a55dadec550f4a7f30a8c2e40b5a49a5f0a6c62a9b035df305b3dc2e5c2ba',
             '6ae4b8af604365ad032e697ec658e640bc4f1b5ee5ee4ae1b691c32095ac7106'],
    'verdict': ['ac8f363ace9768fd85b84b096599a99911887a1ae51946cc1e62da8c6106b448',
                '8cb89a8795ce543cca6c6e2983d0e7646b09c74cef8d7b533e927ffab754f9c5'],
}

def main():
    report = {'kind': 'same-input-software-and-comparator-audit-not-replication',
              'tiktoken': importlib.metadata.version('tiktoken'), 'sources': []}
    for kind, hashes in GROUPS.items():
        complete = []
        for h in hashes:
            row = json.loads((ROOT / 'sources' / (h + '.json')).read_text())
            manifest = row['manifest']; pairs = manifest['test_set']
            assert manifest['models'] == ['cl100k_base', 'o200k_base', 'p50k_base']
            labels = Counter(pair['stratum'] for pair in pairs)
            assert len(labels) == 2 and len(set(labels.values())) == 1
            for pair in pairs:
                e, a = pair['english'], pair['ainglish']
                if kind == 'mean':
                    match = re.fullmatch(r'(mean-of|median-of)\(([^)]+)\) = (.+)\.', a)
                    assert match and match[1] == pair['stratum']
                    desc = 'unweighted arithmetic mean' if match[1] == 'mean-of' else 'median'
                    assert e == f'The {desc} of every numeric observation in the exact finite population {match[2]} is {match[3]}.'
                else:
                    form = pair['stratum']; assert a.endswith(': ' + form + '.')
                    prefix = a[:-len(form)-1]
                    suffix = 'completed; judged the target defective.' if form == 'verdict-fail' else 'no target judgment.'
                    assert e == prefix + suffix and prefix.startswith('Scheduled ')
            recount = token_delta(pairs, manifest['models'])
            assert abs(recount['floor'] - row['value']) < 1e-12
            complete.append({(p['english'], p['ainglish']) for p in pairs})
            report['sources'].append({'manifest_hash': h, 'role': 'original' if h == hashes[0] else 'replication',
                'actual_pairs': len(pairs), 'actual_strata': dict(labels), 'value': row['value'],
                'recount': recount, 'semantic_check': 'exact registered statistic/reference/value or check/target outcome preserved in both complete arms',
                'declaration_note': ('Actual 16-pair / 8-population replication; inherited report-only population prose says 32 / 16. '
                    'Report actual sample, request author clarification; not an arithmetic error or an invented 32-pair observation.'
                    if kind == 'mean' and h == hashes[1] else None)})
        assert not (complete[0] & complete[1]), 'Complete-pair reuse found'
    with (ROOT / 'cost-audit.json').open('x') as f:
        json.dump(report, f, indent=2); f.write('\n')
    print('Four exact-source counts and complete comparator checks pass; two disjoint source pairs; sample-description qualification retained.')

if __name__ == '__main__':
    main()
