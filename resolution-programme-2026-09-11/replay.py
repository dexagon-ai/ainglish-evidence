"""Offline independent arithmetic replay of already-public sufficient journals.

No reader/tokenizer calls and no submission. Correctness bits are observations to
audit, not independently verified answers. Raw-answer/gold validity is a separate
check; an arithmetic match cannot establish that an experimental design is sound.
"""
import argparse
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path


def rounded(value):
    return float(Decimal(str(value)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def replay(source):
    journal = source.get('interval_provenance_attestation')
    if not isinstance(journal, dict):
        return {'status': 'no_sufficient_journal'}
    if journal['algorithm']['name'] != 'sha256-counter-modulo-v1':
        return {'status': 'unsupported_algorithm'}
    draws = journal['algorithm']['draws']
    if type(draws) is not int or not 100 <= draws <= 10000:
        raise ValueError('draw count outside the published protocol')
    cells = journal['cells']
    index = {r['id']: r.get('stratum', '') for r in journal['items']}
    readers = journal['readers']
    expected = {(i, r) for i in index for r in readers}
    actual = [(c['item_id'], c['reader']) for c in cells]
    if len(index) != len(journal['items']) or set(actual) != expected or len(actual) != len(expected):
        raise ValueError('journal item-reader population incomplete or duplicated')
    totals = {i: [0, 0, 0, 0] for i in index}
    for c in cells:
        if c['arm'] not in ('english', 'ainglish') or (c['correct'] is not None and type(c['correct']) is not bool):
            raise ValueError('invalid arm or correctness bit')
        if c['correct'] is not None:
            offset = 0 if c['arm'] == 'english' else 2
            totals[c['item_id']][offset] += int(c['correct'])
            totals[c['item_id']][offset + 1] += 1
    contract = source['manifest'].get('settlement_strata')
    if contract:
        total_weight = sum(r['weight'] for r in contract)
        weights = {r['id']: r['weight'] / total_weight for r in contract}
    else:
        weights = {'': 1}
    if set(index.values()) != set(weights):
        raise ValueError('journal strata differ from the manifest')
    groups = {s: sorted(i for i in index if index[i] == s) for s in weights}

    def effect(ids):
        e, ne, a, na = map(sum, zip(*(totals[i] for i in ids)))
        return None if not ne or not na else 100 * (a / na - e / ne)

    estimates = []
    for draw in range(draws):
        value = 0
        for stratum, ids in groups.items():
            sampled = []
            for position in range(len(ids)):
                text = '\0'.join((journal['kind'], str(journal['seed']), stratum, str(draw), str(position)))
                number = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], 'big')
                sampled.append(ids[number % len(ids)])
            part = effect(sampled)
            if part is None:
                break
            value += weights[stratum] * part
        else:
            estimates.append(value)
    if not estimates:
        raise ValueError('no draw observes both arms')
    estimates.sort()
    lo = rounded(estimates[25 * len(estimates) // 1000])
    hi = rounded(estimates[975 * len(estimates) // 1000])
    h = digest({k: v for k, v in journal.items() if k != 'content_sha256'})
    row_results = []
    top = 0
    served_rows = {r['id']: r for r in source.get('stratum_results') or []}
    for stratum, ids in groups.items():
        e, ne, a, na = map(sum, zip(*(totals[i] for i in ids)))
        eng, marked = rounded(e / ne), rounded(a / na)
        value = rounded(100 * (marked - eng))
        top += weights[stratum] * value
        served = served_rows.get(stratum)
        row_results.append({'stratum': stratum, 'english_counts': [e, ne], 'marked_counts': [a, na],
                            'value': value, 'matches_served': None if served is None else abs(value - served['value']) <= 0.00011})
    return {'status': 'replayed', 'manifest_hash': source['manifest_hash'],
            'url': 'https://ainglish.org/measurements/' + source['manifest_hash'],
            'journal_hash_matches': h == journal['content_sha256'],
            'items': len(index), 'readers': len(readers), 'cells': len(cells),
            'accepted_draws_match': len(estimates) == journal['algorithm']['accepted_draws'],
            'value': rounded(top), 'value_matches': abs(rounded(top) - source['value']) <= 0.00011,
            'interval': [lo, hi], 'interval_matches': all(abs(a - b) <= 0.00011 for a, b in zip((lo, hi), (source['value_lo'], source['value_hi']))),
            'strata': row_results}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources', type=Path, nargs='+', required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    reports = []
    for path in args.sources:
        report = replay(json.loads(path.read_text()))
        reports.append(report)
        print(path.stem[:12], report['status'], report.get('interval_matches'), flush=True)
    with args.report.open('x') as stream:
        json.dump({'kind': 'ainglish.offline-sufficient-journal-replay.v1', 'reports': reports,
                   'boundary': __doc__}, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
