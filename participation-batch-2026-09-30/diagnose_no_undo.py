"""Post-filing diagnostic of two retained banks; NOT another measurement."""
import hashlib
import importlib.util
import json
import argparse
from collections import defaultdict
from pathlib import Path
import tiktoken

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--packet', type=Path, required=True,
                    help='Retained no-undo-draft directory containing both banks, pinned renderer and prior digests')
PACKET = parser.parse_args().packet
renderer = PACKET / 'noundo_rstar.py'
assert hashlib.sha256(renderer.read_bytes()).hexdigest() == 'b1cd2787af86de587058fb7914e959a66ddaaedbf974f1f6b440f43832dbeed8'
spec = importlib.util.spec_from_file_location('rstar', renderer)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
banks = {k: json.loads((PACKET / f).read_text()) for k, f in [('source', 'source-bank.json'), ('replica', 'bank.json')]}
expected = {'source': 'f7e05fd81e90786610de559ad3c8ae4d29477180b8051cff20552d1610ef04de', 'replica': '5372bafd3ef511182f754806a8f655b80ae9a5857c494c339d50f479b7924195'}
for name, bank in banks.items():
    digest = hashlib.sha256(json.dumps(bank, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    assert digest == expected[name], (name, digest)
    assert len(bank) == 32
    assert all(r.render_rstar(r.parse_marked(p['ainglish'])) == p['english'] for p in bank)
assert r.sampling_profile(banks['source']) == r.sampling_profile(banks['replica'])

report = {'kind': 'post-filing-descriptive-diagnostic', 'new_measurement': False,
          'selection': 'entire two already-filed banks, unchanged; not a new independent sample',
          'source_hash': 'b9572064b47bf2fe82f88dc56097292cb8dccee4775f94b6875e80f146eb3a88',
          'replica_hash': '4620b8885048023be93d04c9307a14218d45ff8f72e33654cce4c3e0d4e3f7b6',
          'bank_digests': expected, 'tokenizers': {}}
for tokenizer in r.TOKENIZERS:
    enc = tiktoken.get_encoding(tokenizer)
    groups = {name: defaultdict(list) for name in banks}
    summaries = {}
    for name, bank in banks.items():
        vals = defaultdict(list)
        for p in bank:
            f = r.parse_marked(p['ainglish'])
            key = json.dumps((r.category(f), p['shape'], len(f['action'].split()), len(f.get('path', '').split()), len(f.get('holder', '').split()), f.get('window', ''), f.get('cost', '')))
            delta = len(enc.encode(p['ainglish'])) - len(enc.encode(p['english']))
            groups[name][key].append({'marked': p['ainglish'], 'english': p['english'], 'delta': delta,
                                     'marked_pieces': [enc.decode([t]) for t in enc.encode(p['ainglish'])],
                                     'english_pieces': [enc.decode([t]) for t in enc.encode(p['english'])]})
            vals[f['stratum']].append(delta)
        summaries[name] = {'headline_member_mean': sum(sum(v) for v in vals.values())/32,
                           'strata': {k: sum(v)/len(v) for k, v in vals.items()}}
    differences = []
    for key in sorted(groups['source']):
        a, b = groups['source'][key], groups['replica'][key]
        assert len(a) == len(b)
        diff = sum(v['delta'] for v in b) - sum(v['delta'] for v in a)
        if diff:
            differences.append({'joint_cell': json.loads(key), 'net_token_change': diff, 'source': a, 'replica': b})
    report['tokenizers'][tokenizer] = {'summaries': summaries, 'changed_cells': differences,
        'total_token_change': sum(d['net_token_change'] for d in differences)}
assert report['tokenizers']['p50k_base']['total_token_change'] == 3
assert len(report['tokenizers']['p50k_base']['changed_cells']) == 5
report['settlement'] = {'source_headline': -.6875, 'replica_headline': -.59375,
    'headline_absolute_difference': .09375, 'headline_tolerance': .06875,
    'source_can_undo': -.375, 'replica_can_undo': -.1875,
    'can_undo_absolute_difference': .1875, 'can_undo_tolerance': .0375,
    'rule_changed': False, 'result': 'eligible disagreement retained'}
(ROOT / 'no-undo-diagnostic.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: {'summaries': v['summaries'], 'total_token_change': v['total_token_change']} for k, v in report['tokenizers'].items()}, indent=2))
