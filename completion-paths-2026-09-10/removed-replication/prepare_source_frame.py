"""Preserve every source rendering choice while instantiating fresh complete inputs.

No tiktoken call. All replacements are declared before counting, not selected for
their token lengths. The source's context-resolved/short English epochs and full
Ainglish as_of spelling remain as originally rendered; this is not pure marker cost.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPLACEMENTS = [
    ('Customer 42', 'Customer 318'), ('customer-42', 'customer-318'),
    ('Ticket 812', 'Ticket 624'), ('ticket-812', 'ticket-624'),
    ('User 99', 'User 205'), ('user-99', 'user-205'),
    ('Order 77', 'Order 463'), ('order-77', 'order-463'),
    ('receipt r7', 'receipt r12'), ('receipt@r7', 'receipt@r12'),
    ('receipt v7', 'receipt v12'), ('receipt@v7', 'receipt@v12'),
    ('receipt r3', 'receipt r14'), ('receipt@r3', 'receipt@r14'),
    ('receipt v9', 'receipt v16'), ('receipt@v9', 'receipt@v16'),
    ('receipt r1 ', 'receipt r18 '), ('receipt@r1)', 'receipt@r18)'),
    ('receipt v4', 'receipt v21'), ('receipt@v4', 'receipt@v21'),
    ('receipt r5', 'receipt r23'), ('receipt@r5', 'receipt@r23'),
    ('receipt v2 ', 'receipt v25 '), ('receipt@v2)', 'receipt@v25)'),
    ('2026-08-28', '2026-09-10'), ('2026-09-01', '2026-09-10'),
]

def main():
    source = json.loads((ROOT / 'freeze.json').read_text())['source_manifest']
    fresh = []
    for row in source['test_set']:
        new = copy.deepcopy(row)
        for arm in ['english', 'ainglish']:
            for old, replacement in REPLACEMENTS:
                new[arm] = new[arm].replace(old, replacement)
            assert new[arm] != row[arm]
        fresh.append(new)
    manifest = {k: copy.deepcopy(source[k]) for k in ['metric', 'models', 'estimand_contract']}
    manifest['replicates_hash'] = '903b67a697f5e000b7c57ab64f491e33a7b05aacc67fd5d05a0a99d7c1a6a670'
    manifest['test_set'] = fresh
    manifest['test_set_note'] = (
        'One exact-source-renderer replication: eight fresh complete pairs in the original four '
        'paired context classes, four surface absences and four inventory erasures. Only the '
        'declared object identifiers, immutable receipt identifiers and dates are instantiated '
        'afresh; all wording, punctuation, context-resolved English epochs and full as_of '
        'rendering are preserved. The replacement table was fixed before token encoding; no '
        'selection by count. Fictional text reports, not verification of actual deletion. This '
        'tests lexical-instance sensitivity within this small renderer, not eight new semantic '
        'designs, the full 160-scenario claim, comprehension or a future tokenizer. The abandoned '
        'free-prose preparation was never minted or counted. Preserve every outcome; no rerun '
        'to seek agreement. Aggregate-only source: no new settlement strata.')
    out = ROOT / 'source-frame'
    out.mkdir(exist_ok=True)
    for name, value in [('spec.json', {'manifest': manifest}),
                        ('renderer-replacements.json', REPLACEMENTS)]:
        with (out / name).open('x') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
    print('Fresh source-renderer inputs authored; no encoding', flush=True)

if __name__ == '__main__':
    main()
