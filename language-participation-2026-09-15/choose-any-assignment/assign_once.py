"""Apply the publicly declared prospective balancing method; no model/SDK calls.

This is experimental assignment data, not a new language measure or software change.
The selected matrix and every world are retained regardless of diagnostic appearance.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SOURCE = REPO / 'choose-any-completion-2026-09-14/fresh-bank-v2'
INPUT_SHA = '171b99ef688bee8f8d642f81aab4f14095d52e6826e9dd7bf943819a6fd1abda'
SEED = 2026091501

def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()

def main():
    raw = (SOURCE / 'neutral-worlds.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == INPUT_SHA
    document = json.loads(raw)
    worlds = document['worlds']
    assert len(worlds) == 144 and digest(worlds) == document['worlds_sha256']
    assert len({w['id'] for w in worlds}) == 144
    domains = sorted({w['domain'] for w in worlds})
    sizes = list(range(2, 9))
    assert len(domains) == 6
    cells = {(d, n): sorted(w['id'] for w in worlds if w['domain'] == d and w['n'] == n)
             for d in domains for n in sizes}
    totals = [sum(len(cells[d,n]) for d in domains) for n in sizes]
    assert totals == [21,21,21,21,20,20,20]
    vectors = []
    for domain in domains:
        choices = [sorted({len(cells[domain,n]) // 2, (len(cells[domain,n]) + 1) // 2})
                   for n in sizes]
        vectors.append([v for v in itertools.product(*choices) if sum(v) == 12])
    assert [len(v) for v in vectors] == [6] * 6
    matrices = [m for m in itertools.product(*vectors)
                if all(abs(2 * sum(v[j] for v in m) - totals[j]) <= 1 for j in range(7))]
    assert len(matrices) == 1266
    method = json.loads((ROOT / 'public-method-receipt.json').read_text())
    assert method['id'] and str(SEED) in method['body']
    assert method['created_at'] < datetime.now(timezone.utc).isoformat()
    assert sys.version_info[:2] == (3, 14)
    with (ROOT / 'assignment-started.json').open('x') as handle:
        json.dump({'started_at': datetime.now(timezone.utc).isoformat(),
                   'seed': SEED, 'method_comment_id': method['id'],
                   'input_sha256': INPUT_SHA, 'python': sys.version,
                   'boundary': 'Assignment only; no reader exposure or inference.'}, handle, indent=2)
    rng = random.Random(SEED)
    selected_index = rng.randrange(len(matrices))
    selected = matrices[selected_index]
    mapping = {}
    cell_counts = []
    for i, domain in enumerate(domains):
        for j, n in enumerate(sizes):
            ids = cells[domain,n]
            chosen = set(rng.sample(ids, selected[i][j]))
            for key in ids:
                mapping[key] = 'choose-any' if key in chosen else 'draw-uniform'
            cell_counts.append({'domain': domain, 'member_count': n,
                                'choose_any': len(chosen), 'draw_uniform': len(ids)-len(chosen)})
    mapping = dict(sorted(mapping.items()))
    original = json.loads((SOURCE / 'assignment.json').read_text())['mapping']
    assert set(mapping) == set(original) == {w['id'] for w in worlds}
    assert Counter(mapping.values()) == {'choose-any': 72, 'draw-uniform': 72}
    for d in domains:
        assert sum(r['choose_any'] for r in cell_counts if r['domain'] == d) == 12
    assert all(abs(r['choose_any'] - r['draw_uniform']) <= 1 for r in cell_counts)
    global_counts = [{'member_count': n,
                      'choose_any': sum(r['choose_any'] for r in cell_counts if r['member_count'] == n),
                      'draw_uniform': sum(r['draw_uniform'] for r in cell_counts if r['member_count'] == n)}
                     for n in sizes]
    assert all(abs(r['choose_any'] - r['draw_uniform']) <= 1 for r in global_counts)
    result = {'kind': 'choose-any.prospective-balanced-assignment.v1',
              'status': 'ASSIGNMENT_ONLY_COMPARATOR_UNRESOLVED_DO_NOT_RUN',
              'created_at': datetime.now(timezone.utc).isoformat(),
              'method_comment_id': method['id'], 'seed': SEED,
              'neutral_file_sha256': INPUT_SHA, 'neutral_worlds_sha256': digest(worlds),
              'domain_order': domains, 'member_count_order': sizes,
              'feasible_matrix_count': len(matrices), 'matrix_index_zero_based': selected_index,
              'selected_choose_any_count_matrix': selected, 'mapping': mapping,
              'mapping_sha256': digest(mapping), 'cell_counts': cell_counts,
              'global_counts': global_counts,
              'changed_from_preserved_assignment': sum(mapping[k] != original[k] for k in mapping),
              'worlds_changed': 0, 'worlds_dropped': 0, 'worlds_added': 0,
              'target_calls': 0, 'minted_attempts': 0,
              'remaining': ['Exact admissible English comparator',
                            'Final item and reader identities plus actual arm allocation',
                            'Recomputed planning bounds and equal-reader-weight sensitivity',
                            'Payload review, qualification, preflight and mint before any inference'],
              'boundary': 'No rerolls, outcome-driven exclusions, cue-free claim or launch permission. '
                          'A conditional design revision, not a new scientific result.'}
    (ROOT / 'assignment.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    assert (SOURCE / 'neutral-worlds.json').read_bytes() == raw
    print(json.dumps({k:result[k] for k in ['feasible_matrix_count','matrix_index_zero_based',
                'mapping_sha256','global_counts','changed_from_preserved_assignment','target_calls']}, indent=2))

if __name__ == '__main__':
    main()
