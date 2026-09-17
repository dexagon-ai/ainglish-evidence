"""Report-only grouped sensitivity; never calls readers, an API, or a filing method.

Four domains are FIXED. Within each domain/policy block, sample four of its
four progress groups with replacement. Keep both question variants and all
reader cells together. The 32 sampled groups preserve the two policy weights.
This finite-battery diagnostic does not validate nominal population coverage.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ALGORITHM = 'resume-domain-fixed-group-sensitivity-v1'
DOMAINS = ['media', 'reading', 'review', 'simulation']
POLICIES = ['resume-core', 'redo-core']
DRAWS = 2000
SEED = 2026091702
ARMS = ['english', 'ainglish']


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def arm_for(seed, reader, item):
    return 'ainglish' if hashlib.sha256(f'{seed}|{reader}|{item}'.encode()).digest()[0] % 2 else 'english'


def group_index(items, readers, allocation_seed):
    core = [x for x in items if not x.get('calibration')]
    if len(core) != 64 or len({x['id'] for x in core}) != 64:
        raise ValueError('Need exactly 64 distinct core items.')
    if len(readers) != 2 or len(set(readers)) != 2:
        raise ValueError('Need two distinct exact reader aliases.')
    groups = defaultdict(list)
    for item in core:
        st = item['strata']
        if (st.get('block') != 'core' or st.get('domain') not in DOMAINS
                or st.get('form') not in ['resume', 'redo']
                or type(st.get('progress')) is not int or st['progress'] not in range(4)
                or item['settlement_stratum'] != st['form']+'-core'):
            raise ValueError('Core domain/policy/progress contract changed.')
        groups[(st['domain'], st['form'], st['progress'])].append(item)
    if len(groups) != 32:
        raise ValueError('Need all 32 declared groups.')
    result = []
    for (domain, form, progress), rows in sorted(groups.items()):
        if len(rows) != 2 or {r['strata']['lamp_condition'] for r in rows} != {'performed', 'unperformed'}:
            raise ValueError('Each group needs its two complementary question variants.')
        ids = sorted(r['id'] for r in rows)
        result.append({'id': f'{domain}:{form}:{progress}', 'domain': domain,
                       'policy': form+'-core', 'progress': progress, 'items': ids,
                       'cells': [{'item_id': iid, 'reader': reader,
                                  'arm': arm_for(allocation_seed, reader, iid)}
                                 for iid in ids for reader in sorted(readers)]})
    return {'kind': 'ainglish.resume-group-index.v1', 'core_items_sha256': digest(core),
            'allocation_seed': allocation_seed, 'readers': sorted(readers), 'groups': result}


def validate_index(index):
    if (index.get('kind') != 'ainglish.resume-group-index.v1'
            or len(index.get('readers', [])) != 2 or len(set(index['readers'])) != 2):
        raise ValueError('Wrong index kind or reader roster.')
    groups = index['groups']
    expected = {(d, p, i) for d in DOMAINS for p in POLICIES for i in range(4)}
    actual = {(g['domain'], g['policy'], g['progress']) for g in groups}
    if len(groups) != 32 or actual != expected or len({g['id'] for g in groups}) != 32:
        raise ValueError('Incomplete or duplicate group index.')
    all_items = []
    for g in groups:
        form = g['policy'].removesuffix('-core')
        if g['id'] != f"{g['domain']}:{form}:{g['progress']}" or len(g['items']) != 2:
            raise ValueError('Malformed group identity.')
        all_items.extend(g['items'])
        expected_cells = {(i, r, arm_for(index['allocation_seed'], r, i))
                          for i in g['items'] for r in index['readers']}
        cells = {(c['item_id'], c['reader'], c['arm']) for c in g['cells']}
        if len(g['cells']) != 4 or cells != expected_cells:
            raise ValueError('Group does not preserve every allocated reader/item cell.')
    if len(all_items) != 64 or len(set(all_items)) != 64 or len(set(index['readers'])) != 2:
        raise ValueError('Repeated or omitted item/reader.')


def blocks(index):
    validate_index(index)
    return [(f'{d}:{p}', sorted(g['id'] for g in index['groups']
                               if g['domain'] == d and g['policy'] == p))
            for d in DOMAINS for p in POLICIES]


def sample_groups(index, draw):
    selected = []
    for block, members in blocks(index):
        for position in range(4):
            preimage = '\0'.join([ALGORITHM, str(SEED), block, str(draw), str(position)]).encode()
            selected.append(members[int.from_bytes(hashlib.sha256(preimage).digest()[:8], 'big') % 4])
    return selected


def verified_cells(index, receipt):
    """Accept a complete SDK raw interval-provenance receipt, not its public summary.

    Checks receipt integrity/identity, not model authenticity or server attestation.
    """
    raw = {k: v for k, v in receipt.items() if k != 'content_sha256'}
    if receipt.get('kind') != 'ainglish.panel.bootstrap-items-attestation.v1' or digest(raw) != receipt.get('content_sha256'):
        raise ValueError('Missing, malformed or hash-mismatched raw SDK receipt.')
    if receipt.get('metric') != 'comprehension_accuracy_delta' or receipt.get('seed') != index['allocation_seed']:
        raise ValueError('Receipt metric or allocation seed differs.')
    items = [{'id': iid, 'stratum': g['policy']} for g in index['groups'] for iid in g['items']]
    if sorted(receipt.get('items', []), key=lambda x: x['id']) != sorted(items, key=lambda x: x['id']):
        raise ValueError('Receipt item/stratum index differs.')
    if sorted(receipt.get('readers', [])) != index['readers']:
        raise ValueError('Receipt reader roster differs.')
    return receipt['cells']


def analyse(index, cells):
    validate_index(index)
    expected = {(c['item_id'], c['reader']): c['arm'] for g in index['groups'] for c in g['cells']}
    observed = {}
    for cell in cells:
        key = (cell['item_id'], cell['reader'])
        if key not in expected or key in observed or cell['arm'] != expected[key]:
            raise ValueError('Unplanned, duplicate or misallocated reader cell.')
        if cell['correct'] is not None and type(cell['correct']) is not bool:
            raise ValueError('Correctness must be boolean or an explicit absent-cell null.')
        observed[key] = cell
    if set(observed) != set(expected):
        raise ValueError('Do not analyse a partial journal as a complete panel.')
    groups = {g['id']: g for g in index['groups']}
    totals = {}
    for g in groups.values():
        count = {arm: {'live': 0, 'correct': 0} for arm in ARMS}
        for planned in g['cells']:
            cell = observed[(planned['item_id'], planned['reader'])]
            if cell['correct'] is not None:
                count[cell['arm']]['live'] += 1
                count[cell['arm']]['correct'] += int(cell['correct'])
        totals[g['id']] = count

    def estimate(selected):
        counts = {p: {a: {'live': 0, 'correct': 0} for a in ARMS} for p in POLICIES}
        for gid in selected:  # Repeated groups retain their full multiplicity.
            for arm in ARMS:
                for key in ('live', 'correct'):
                    counts[groups[gid]['policy']][arm][key] += totals[gid][arm][key]
        missing = [f'{p}:{a}' for p in POLICIES for a in ARMS if counts[p][a]['live'] == 0]
        if missing:
            return None, counts, missing
        values = {p: 100 * (counts[p]['ainglish']['correct']/counts[p]['ainglish']['live']
                            - counts[p]['english']['correct']/counts[p]['english']['live']) for p in POLICIES}
        values['aggregate'] = sum(values.values()) / 2
        return values, counts, []

    point, point_counts, point_missing = estimate(sorted(groups))
    estimates = {k: [] for k in ['aggregate', *POLICIES]}
    invalid = []; missing_reasons = Counter(); draw_hash = hashlib.sha256(); accepted_mask = bytearray()
    # Precompute selections once; no draws are retried or replaced.
    for draw in range(DRAWS):
        selected = sample_groups(index, draw)
        draw_hash.update(canonical(selected)+b'\n')
        result, _, missing = estimate(selected)
        accepted_mask.append(int(result is not None))
        if result is None:
            invalid.append(draw); missing_reasons.update(missing)
            continue
        for name, value in result.items():
            estimates[name].append(value)
    accepted = DRAWS-len(invalid)
    intervals = {}
    if accepted:
        for name, values in estimates.items():
            ordered = sorted(values)
            lo, hi = ordered[25*accepted//1000], ordered[975*accepted//1000]
            intervals[name] = {'lo': lo, 'hi': hi, 'degenerate': lo == hi}
    return {'kind': 'ainglish.resume-cluster-sensitivity.v1', 'algorithm': ALGORITHM,
            'status': 'report_only' if accepted else 'held_no_jointly_observable_draw',
            'governance_effect': 'none', 'fileable_measurement': False,
            'group_index_sha256': digest(index), 'cells_sha256': digest(sorted(cells, key=lambda x:(x['item_id'],x['reader']))),
            'sampling_seed': SEED, 'draws': DRAWS, 'accepted_draws': accepted,
            'invalid_draws': len(invalid), 'invalid_draw_indices': invalid,
            'missing_policy_arm_counts': dict(missing_reasons),
            'accepted_mask_sha256': hashlib.sha256(accepted_mask).hexdigest(),
            'draw_selection_sha256': draw_hash.hexdigest(), 'point_unrounded_pp': point,
            'point_arm_counts': point_counts, 'point_missing_arms': point_missing,
            'absent_cells_retained': sum(c['correct'] is None for c in cells),
            'nominal_95_percentile_intervals_pp': intervals,
            'limits': 'Fixed four-domain battery; 32 related groups are not independent sampled natural worlds. No validated population coverage, equivalence or settlement claim. Shared domain frames and reader artifacts remain limitations. An absent cell is retained, not silently turned into an error or excluded from the planned journal.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group-index', required=True, type=Path)
    parser.add_argument('--measurement', required=True, type=Path,
                        help='Official local measurement JSON with the complete raw interval_provenance receipt.')
    args = parser.parse_args()
    index = json.loads(args.group_index.read_text())
    measurement = json.loads(args.measurement.read_text())
    receipt = measurement['interval_provenance']
    print(json.dumps(analyse(index, verified_cells(index, receipt)), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
