"""Check the published dated census, including floor cells and non-counting misses."""
from collections import Counter
import hashlib
import json
from reconcile import classify
from snapshot import ROOT, save


def main():
    pages = json.loads((ROOT/'census/replication-pages.json').read_text())
    rows = [r for p in pages for r in p['measurements']]
    old = json.loads((ROOT/'census/RECONCILIATION.json').read_text())
    counts = dict(Counter(classify(r) for r in rows))
    assert counts == old['counts'], 'The old census would need an explicit correction'
    floor_rows = []
    misses = []
    for row in rows:
        comparison = row.get('replication_comparison') or {}
        cells = [r['id'] for r in comparison.get('strata', []) if r.get('tolerance') == 0.02]
        if cells:
            floor_rows.append({'manifest_hash': row['manifest_hash'], 'attempt_id': row['attempt_id'], 'floor_cells': cells})
        if comparison.get('aggregate_reproduced_ok') is False:
            misses.append({'manifest_hash': row['manifest_hash'], 'attempt_id': row['attempt_id'],
                'classification': classify(row), 'held_on': comparison.get('commensurability', {}).get('held_on', [])})
    corrected = next(r for r in floor_rows if r['manifest_hash'].startswith('c7f77dcd'))
    assert len(corrected['floor_cells']) == 9
    result = {'kind': 'ainglish.reconciliation-audit.v1', 'dated_sweep': old['at'], 'rows': len(rows),
        'source_census_sha256': hashlib.sha256((ROOT/'census/RECONCILIATION.json').read_bytes()).hexdigest(),
        'published_classification_counts_unchanged': True, 'counts': counts,
        'eligible_unknown_outcomes': counts.get('eligible_outcome_not_recorded', 0),
        'floor_rows': floor_rows, 'aggregate_misses': misses,
        'aggregate_misses_by_current_classification': dict(Counter(r['classification'] for r in misses)),
        'boundaries': ['Rows, not proposals; includes historical and non-counting evidence.',
            'The current sweep is not silently substituted for an earlier eight-row subpopulation.',
            'An aggregate mismatch alone cannot establish a scientific disagreement.',
            'The ninth c7f77dcd cell confirms the corrected floor recount; it does not change any observed result.',
            'Unknown reproduced_ok is now explicitly classified rather than treated as false; no row in this sweep was affected.']}
    save('census/AUDIT.json', result)
    print(json.dumps({'rows': len(rows), 'counts_unchanged': True,
        'c7f77dcd_floor_cells': len(corrected['floor_cells']),
        'aggregate_misses': result['aggregate_misses_by_current_classification']}))


if __name__ == '__main__': main()
