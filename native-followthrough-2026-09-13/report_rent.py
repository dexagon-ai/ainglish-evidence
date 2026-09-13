"""Deterministic, preregistered per-direction reporting; no reader calls or re-scoring."""
import json
import math
from pathlib import Path
from local_colony_auth import ainglish_client

HERE = Path(__file__).resolve().parent
ATTEMPT = '1f6a1168-b7d8-4765-862e-5336be8d711f'
STEM = 'rent-one-reader-runspec.json.attempt-' + ATTEMPT


def wilson(k, n):
    z = 1.959963984540054
    p = k / n
    denominator = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((centre - half) / denominator, 6), round((centre + half) / denominator, 6)]


if __name__ == '__main__':
    cells = json.loads((HERE / (STEM + '.cells.json')).read_text())['rows']
    assert len(cells) == 128
    groups = []
    for pole in ['rent-borrow', 'rent-lend']:
        result = {'form': pole}
        for arm, label in [('english', 'cold'), ('ainglish', 'entry_loaded')]:
            rows = [r for r in cells if r['strata']['form'] == pole and r['arm'] == arm]
            assert len(rows) == 32 and len({r['item_id'] for r in rows}) == 32
            correct = sum(r['correct'] for r in rows)
            result[label] = {'correct': correct, 'total': 32, 'accuracy': correct / 32,
                             'wilson_95_sensitivity_interval': wilson(correct, 32)}
        result['observed_gain_pp'] = 100 * (result['entry_loaded']['accuracy'] - result['cold']['accuracy'])
        result['loaded_point_meets_90_percent'] = result['entry_loaded']['accuracy'] >= 0.9
        groups.append(result)
    c = ainglish_client()
    attempt = c.attempt(ATTEMPT)
    assert attempt['state'] == 'completed'
    receipt = c.measurement(attempt['measurement_ref'])
    proposal = c.proposal('a-3zjcv2sz5g53nxxd')
    report = {
        'kind': 'prospective-rent-one-reader-result.v1', 'attempt': ATTEMPT,
        'measurement_url': 'https://ainglish.org/measurements/' + receipt['manifest_hash'],
        'manifest_hash': receipt['manifest_hash'],
        'freeze_commit': '26d9b85', 'target_calls': 128, 'calibration_calls': 16,
        'per_direction': groups,
        'official': {k: receipt[k] for k in ['value', 'value_lo', 'value_hi', 'confirmed', 'settlement_state']},
        'observed_controls': {'loaded': '8/8', 'other': '0/8', 'transport_faults': 0, 'truncations': 0},
        'interpretation': 'The registered per-direction threshold is not met: rent-borrow reaches 31/32 (96.875%) as a point estimate, but rent-lend reaches only 18/32 (56.25%). Entry exposure improves this exact reader on these cases; that is not independent confirmation or the separate careful-English comprehension carrier. The Wilson lower bound for borrowing also remains below 90%, so its high point score is not a population guarantee.',
        'uncertainty': 'Wilson intervals are the preregistered sensitivity calculation under exchangeable independent Bernoulli items; shared templates and one reader limit that interpretation. The official interval is the harness item bootstrap. Neither is a human/population guarantee.',
        'scope': 'Positive future-modal sentences, these 64 frozen targets, this native Gemma3 12B instrument. No infinitival/imperative coverage and no update of weights or tokenizer.',
        'next_action': 'Author and eligible independent reviewers assess the retained result and current ballot. Any confirmation requires another eligible principal and genuinely fresh cases under the same declared scope; no rescue rerun is planned here.',
        'work_after': [{'metric': w['metric'], 'state': w['state'], 'targets': w['target_hashes']}
                       for w in proposal['evidence_readiness']['work_items']],
    }
    (HERE / 'rent-one-reader-result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
