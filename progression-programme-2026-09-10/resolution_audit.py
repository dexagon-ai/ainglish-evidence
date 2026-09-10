"""Public read-only audit, not a measurement or a proposed settlement-rule activation.

Never use 100/item_count as a universal step. Verified scored-cell attestations can
support an arithmetic lattice for this particular pooled accuracy estimator. Its
step is NOT an uncertainty bound, effect-size threshold or licence to widen a gate.
"""
import collections
import datetime
import json
import math
from pathlib import Path
from ainglish.client import AinglishClient


def lattice(cells):
    counts = collections.Counter(c['arm'] for c in cells)
    a, e = counts['ainglish'], counts['english']
    if not a or not e:
        return None
    correct = collections.Counter(c['arm'] for c in cells if c['correct'])
    return {'scored_cells': {'english': e, 'ainglish': a},
            'one_cell_pp': {'english': 100/e, 'ainglish': 100/a},
            'delta_grid_step_pp': 100/math.lcm(e, a),
            'rederived_pooled_value': 100*(correct['ainglish']/a-correct['english']/e)}


def resolutions(row):
    pin = row.get('interval_provenance') or {}
    att = row.get('interval_provenance_attestation') or {}
    if pin.get('verified') is not True or not isinstance(att.get('cells'), list):
        return {'basis': 'unknown; no verified scored-cell attestation', 'aggregate': None, 'strata': {}}
    mapping = {i['id']: i.get('stratum') for i in att.get('items', [])}
    grouped = collections.defaultdict(list)
    for cell in att['cells']:
        grouped[mapping.get(cell['item_id'])].append(cell)
    values = {s['id']: s['value'] for s in (row.get('stratum_results') or [])}
    strata = {}
    for key, cells in grouped.items():
        result = lattice(cells)
        if key is not None and result is not None:
            result['matches_served_point'] = key in values and abs(result['rederived_pooled_value']-values[key]) <= .011
            strata[key] = result
    total = lattice(att['cells'])
    if total:
        total['matches_served_point'] = abs(total['rederived_pooled_value']-row['value']) <= .011
    return {'basis': 'verified public scored-cell attestation; pooled estimator checked',
            'content_sha256': pin.get('content_sha256'), 'aggregate': total, 'strata': strata}


def compare_slice(comp, a, b):
    tol = comp.get('tolerance')
    if isinstance(tol, dict):
        tol = tol.get('effective')
    known = a is not None and b is not None and a['matches_served_point'] and b['matches_served_point']
    return {'tolerance': tol, 'absolute_difference': comp.get('absolute_difference'),
            'reproduced_ok': comp.get('reproduced_ok'), 'original': a, 'replication': b,
            'tolerance_below_either_one_cell_step': bool(known and tol is not None and
                tol < max(*a['one_cell_pp'].values(), *b['one_cell_pp'].values())),
            'tolerance_below_either_delta_grid': bool(known and tol is not None and
                tol < max(a['delta_grid_step_pp'], b['delta_grid_step_pp'])),
            'unknown_or_different_estimator': not known}


def main():
    client = AinglishClient(use_env=False)
    pages = list(client.measurement_pages(metric='comprehension_accuracy_delta', page_size=200))
    rows = [r for p in pages for r in p['measurements']]
    out, cache = [], {}
    def detail(h):
        if h not in cache:
            cache[h] = client.measurement(h)
        return cache[h]
    for row in rows:
        target = row.get('replicates_hash') or (row.get('replicates') or {}).get('hash')
        if not target:
            continue
        rep = detail(row['manifest_hash']); source = detail(target)
        comp = rep.get('replication_comparison') or {}
        a, b = resolutions(source), resolutions(rep)
        slices = []
        for s in (comp.get('strata') or []):
            slices.append({'id': s['id'], **compare_slice(s, a['strata'].get(s['id']), b['strata'].get(s['id']))})
        out.append({'original_hash': target, 'replication_hash': rep['manifest_hash'],
                    'proposal': row.get('proposal'), 'settlement_eligible': rep.get('settlement_eligible'),
                    'reproduced_ok': rep.get('reproduced_ok'), 'evidence_state': rep.get('evidence_state'),
                    'rule_applied': comp.get('rule_applied'), 'point_effect': comp.get('point_effect'),
                    'strata_effect': comp.get('strata_effect'),
                    'aggregate_reproduced_ok': comp.get('aggregate_reproduced_ok'),
                    'aggregate': compare_slice(comp, a['aggregate'], b['aggregate']), 'strata': slices,
                    'original_resolution_basis': a['basis'], 'replication_resolution_basis': b['basis']})
        print('read', len(out), rep['manifest_hash'][:12], flush=True)
    operative = [r for r in out if r['settlement_eligible'] is True]
    summary = {'public_cad_rows': len(rows), 'replications': len(out),
               'eligible_replications': len(operative),
               'eligible_disagreements': sum(r['reproduced_ok'] is False for r in operative),
               'aggregate_agrees_but_required_strata_disagree': sum(
                   r['aggregate_reproduced_ok'] is True and r['reproduced_ok'] is False and r['strata_effect']=='required_all' for r in operative),
               'eligible_strata_with_checked_grids': sum(not s['unknown_or_different_estimator'] for r in operative for s in r['strata']),
               'eligible_strata_tolerance_below_either_grid': sum(s['tolerance_below_either_delta_grid'] for r in operative for s in r['strata'])}
    report = {'kind': 'ainglish.public.resolution-audit.v1', 'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Public CAD cursor snapshot; independent read times for detail, not an atomic database snapshot.',
              'sweep': pages[0].get('sweep'), 'summary': summary, 'comparisons': out,
              'boundary': 'Report only. A lattice is not uncertainty or a recommended tolerance. Unknown is not zero. No historic row, rule, vote or lifecycle was changed.'}
    Path(__file__).with_name('resolution-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
