"""Post-hoc retained-input attribution only: no mint, filing or independent evidence."""
import copy
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
import tiktoken

ROOT = Path(__file__).resolve().parent
SOURCE = ['d9bc25ff', '35874bf6']
REPLICA = ['4e664b27', '1dbf3d33']
encoders = {m: tiktoken.get_encoding(m) for m in ['cl100k_base', 'o200k_base', 'p50k_base']}


def load(prefix):
    return json.loads(next(ROOT.glob('measurement-' + prefix + '*.json')).read_text())


def summarize(items):
    result = {}
    for name, enc in encoders.items():
        groups = defaultdict(list)
        for item in items:
            groups[item['stratum']].append(len(enc.encode(item['ainglish'])) - len(enc.encode(item['english'])))
        result[name] = {'strata': {k: mean(v) for k, v in groups.items()},
                        'headline_member': mean([mean(v) for v in groups.values()])}
    return result


def rebind(items, replacement):
    changed = copy.deepcopy(items)
    for i, item in enumerate(changed):
        for arm in ['english', 'ainglish']:
            text, n = re.subn(r'forecast-\d+|satdist-[ck]\d+', replacement(i // 2), item[arm])
            assert n == 1
            item[arm] = text
    return changed


audits = []
for source_prefix, replica_prefix, genre in zip(SOURCE, REPLICA, ['careful', 'compact']):
    source, replica = load(source_prefix), load(replica_prefix)
    a, b = source['manifest']['test_set'], replica['manifest']['test_set']
    observed_a, observed_b = summarize(a), summarize(b)
    for row, observed in [(source, observed_a), (replica, observed_b)]:
        assert max(v['headline_member'] for v in observed.values()) == row['value']
        for member in row['per_member']:
            assert observed[member['model']]['headline_member'] == member['value']
    rebind_a = summarize(rebind(a, lambda i: 'satdist-' + ('c' if genre == 'careful' else 'k') + f'{i:02}'))
    rebind_b = summarize(rebind(b, lambda i: f'forecast-{70+i}'))
    sample = {}
    for model, enc in encoders.items():
        sample[model] = {}
        for text in ['(forecast-70)', '(satdist-c00)', 'Under forecast-70,', 'Under satdist-c00,',
                     'under forecast-70:', 'under satdist-k00:']:
            tokens = enc.encode(text)
            sample[model][text] = {'n': len(tokens), 'pieces': [enc.decode([t]) for t in tokens]}
    audits.append({'genre': genre, 'source': source['manifest_hash'], 'replication': replica['manifest_hash'],
                   'source_retained': observed_a, 'replication_retained': observed_b,
                   'source_with_replica_reference_spelling': rebind_a,
                   'replication_with_source_reference_spelling': rebind_b,
                   'illustrative_boundary_tokens': sample,
                   'scope': 'Bidirectional reference-only counterfactuals on already observed text. Not preregistered, not independent, not a new settlement result. Values and comparison wording are otherwise unchanged.'})
    print(genre, json.dumps({k: audits[-1][k] for k in ['source_retained', 'replication_retained',
             'source_with_replica_reference_spelling', 'replication_with_source_reference_spelling']}), flush=True)
result = {'kind': 'dexagon.posthoc-token-attribution.v1', 'audits': audits}
output = ROOT / 'outcome-boundary-audit.json'
if output.exists():
    assert json.loads(output.read_text()) == result, 'Retained audit does not reproduce'
    print('Retained audit reproduced exactly; no file or measurement changed.')
else:
    with output.open('x') as out:
        json.dump(result, out, indent=2)
