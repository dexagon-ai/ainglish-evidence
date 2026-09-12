"""Known-truth paired binary simulations; not a language measurement or policy gate.

The current official CAD panel is counterbalanced, NOT this fully paired design.
No source outcomes are fitted; no real reader, API or tokenizer is called.
"""
import hashlib
import json
import math
from pathlib import Path
import numpy as np

PLAN = {
    'kind': 'prospective-preservation-simulation.v1', 'seed': 2026091208,
    'experiments_per_scenario': 400, 'bootstrap_draws': 399,
    'lower_quantile': .05, 'illustrative_margin': .02,
    'deltas': [-.02, 0.0], 'reader_counts': [2, 8],
    'scenarios': {'iid': 128, 'crossed': 128, 'near_ceiling': 16},
    'methods': ['naive_cells', 'items_only', 'crossed_readers_items'],
    'reducer': 'unweighted mean of paired marked-minus-English binary outcomes',
    'boundary': 'Two pp is a preview-review illustration, not a global default or adoption rule. '
                'One-sided lower > -margin is only a preservation component; independent '
                'confirmation, semantic validity, absolute floor, every critical form and '
                'separate benefit remain required. No historical result is reclassified.',
}

def probabilities(scenario, delta, reader_effect, item_effect):
    if scenario == 'near_ceiling':
        en = .995
        ai = en + delta
    elif scenario == 'iid':
        en = .8
        ai = en + delta
    elif scenario == 'crossed':
        en = .8 + .08 * item_effect
        ai = en + delta + .07 * reader_effect
    else:
        raise ValueError('unknown scenario')
    if not (0 <= en <= 1 and 0 <= ai <= 1):
        raise ValueError('No clipping: clipping would change the known truth')
    return en, ai

def generate(rng, scenario, delta, readers, items):
    reader_effect = rng.choice([-1, 1], size=readers)
    item_effect = rng.choice([-1, 1], size=items)
    en = np.empty((readers, items)); ai = np.empty_like(en)
    for r in range(readers):
        for i in range(items):
            en[r, i], ai[r, i] = probabilities(scenario, delta, reader_effect[r], item_effect[i])
    # Common uniform within each paired outcome, independent across reader/item cells.
    # Conditional means vary by both crossed factors in the crossed scenario.
    draw = rng.random((readers, items))
    return (draw < ai).astype(float) - (draw < en).astype(float)

def lower_bounds(data, rng, draws):
    readers, items = data.shape
    vals, frequencies = np.unique(data, return_counts=True)
    naive = rng.multinomial(data.size, frequencies / data.size, size=draws) @ vals / data.size
    iw = rng.multinomial(items, np.full(items, 1 / items), size=draws)
    item_only = iw @ data.mean(axis=0) / items
    rw = rng.multinomial(readers, np.full(readers, 1 / readers), size=draws)
    crossed = np.einsum('br,ri,bi->b', rw, data, iw, optimize=True) / data.size
    return {key: float(np.quantile(value, PLAN['lower_quantile'], method='linear'))
            for key, value in zip(PLAN['methods'], [naive, item_only, crossed])}

def rate(successes, n):
    # Wilson interval describes Monte Carlo uncertainty only, not a study confidence interval.
    p = successes / n; z = 1.959963984540054
    center = (p + z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return {'count': successes, 'trials': n, 'rate': p, 'mc_wilson95': [center-half, center+half]}

def run():
    rng = np.random.default_rng(PLAN['seed']); rows = []
    for scenario, items in PLAN['scenarios'].items():
        for readers in PLAN['reader_counts']:
            for delta in PLAN['deltas']:
                passed = dict.fromkeys(PLAN['methods'], 0)
                covers = dict.fromkeys(PLAN['methods'], 0)
                all_zero = 0; points = []
                n = PLAN['experiments_per_scenario']
                for _ in range(n):
                    data = generate(rng, scenario, delta, readers, items)
                    points.append(float(data.mean()))
                    all_zero += int(not np.any(data))
                    bounds = lower_bounds(data, rng, PLAN['bootstrap_draws'])
                    for method, lower in bounds.items():
                        passed[method] += int(lower > -PLAN['illustrative_margin'] + 1e-12)
                        covers[method] += int(lower <= delta + 1e-12)
                row = {'scenario': scenario, 'readers': readers, 'items': items,
                    'paired_cells': readers*items, 'true_delta': delta,
                    'observed_mean_across_experiments': sum(points)/n,
                    'all_zero_paired_differences': rate(all_zero, n),
                    'preservation_component_pass': {k: rate(v,n) for k,v in passed.items()},
                    'one_sided_lower_covers_truth': {k: rate(v,n) for k,v in covers.items()},
                    'interpretation': 'false preservation at boundary' if delta == -.02 else 'power at exact equality'}
                rows.append(row)
                print(scenario, readers, delta, {k: round(v/n,3) for k,v in passed.items()}, flush=True)
    return {'plan': PLAN, 'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'numpy_version': np.__version__, 'measurement': False, 'rows': rows}

if __name__ == '__main__':
    destination = Path(__file__).with_name('preservation-simulation.json')
    if destination.exists():
        raise SystemExit('Keep the first result; no silent overwrite or outcome-selected rerun')
    result = run()
    with destination.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
