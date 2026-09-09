"""Recount already-public observations, not a new preregistered measurement."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import statistics

import tiktoken
from ainglish.client import AinglishClient, manifest_commitment

ROOT = Path(__file__).resolve().parent
HASHES = [
    'e2ff808e72df863f2c403344843ac1f8e81cd6ae3b55ed3150e05ff922de5842',
    '6993626206277d87d1b2531f7a5214d091a76eacb9e1614501271dc46090cee7',
    'a8fd5fc27114b7d7b36d1baa0e01178c5b5ba60fe2115ef428006a711a6150c5',
]

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

def audit():
    records = [json.loads((ROOT / 'replacement-sources' / (h + '.json')).read_text()) for h in HASHES]
    source = records[0]['manifest']
    summaries, pair_sets = [], []
    for h, record in zip(HASHES, records):
        m = record['manifest']
        assert manifest_commitment(m) == h
        assert m['models'] == source['models']
        assert m['comparison_identity'] == source['comparison_identity']
        assert m['estimand_contract'] == source['estimand_contract']
        assert m['settlement_strata'] == source['settlement_strata']
        pairs = m['test_set']
        assert len(pairs) == 64
        assert Counter(x['stratum'] for x in pairs) == dict.fromkeys(['request','report','proposal','simulation'], 16)
        assert len({(x['english'], x['ainglish']) for x in pairs}) == 64
        pair_sets.append({(x['english'], x['ainglish']) for x in pairs})
        by_context = defaultdict(list)
        for x in pairs:
            e = re.fullmatch(r'(.*): remove (.+) from that slot and put (.+) there instead\.', x['english'])
            a = re.fullmatch(r'(.*): replace\(old=(.+), new=(.+)\)\.', x['ainglish'])
            assert e and a and e.groups() == a.groups(), 'Meaning/prefix/argument mapping differs'
            assert e[2] != e[3], 'Old and new are not distinct'
            by_context[(e[2], e[3])].append(x)
        assert len(by_context) == 16 and all(len(v) == 4 for v in by_context.values())
        members = []
        for model in m['models']:
            enc = tiktoken.get_encoding(model)
            cells = [len(enc.encode(x['ainglish'])) - len(enc.encode(x['english'])) for x in pairs]
            mean = statistics.mean(cells)
            stored = next(r['value'] for r in record['per_member'] if r['model'] == model)
            assert mean == stored, (model, mean, stored)
            strata = {s: statistics.mean(d for x,d in zip(pairs,cells) if x['stratum'] == s)
                      for s in ['request','report','proposal','simulation']}
            context_invariance = all(len({len(enc.encode(x['ainglish'])) - len(enc.encode(x['english']))
                                          for x in xs}) == 1 for xs in by_context.values())
            members.append({'model': model, 'mean': mean, 'strata': strata,
                            'pair_delta_counts': dict(sorted(Counter(cells).items())),
                            'four_forces_have_same_delta_within_every_reference_tuple': context_invariance})
        assert max(x['mean'] for x in members) == record['value']
        comparison = record.get('replication_comparison') or {}
        summaries.append({'manifest_hash': h, 'submitter': record['submitter']['name'],
                          'value': record['value'], 'pair_count': 64, 'reference_tuple_count': 16,
                          'exact_mapping_checks_pass': True, 'member_recounts_match': True,
                          'all_member_means_at_most_zero': all(x['mean'] <= 0 for x in members),
                          'per_member': members, 'settlement_eligible': record.get('settlement_eligible'),
                          'reproduced_ok': record.get('reproduced_ok'),
                          'absolute_difference': comparison.get('absolute_difference'),
                          'tolerance': comparison.get('tolerance'),
                          'interval_kind': m['interval_kind']})
    overlaps = [{'left': HASHES[i], 'right': HASHES[j], 'complete_pair_overlap': len(pair_sets[i] & pair_sets[j])}
                for i in range(3) for j in range(i+1,3)]
    assert all(x['complete_pair_overlap'] == 0 for x in overlaps)
    output = {'kind': 'ainglish.public-observation-recount.v1',
              'scope': 'Historical forensic audit only; no new experiment, gate change, or independent confirmation.',
              'rows': summaries, 'pair_overlap': overlaps,
              'limits': ['The tokenizer-member span is not a confidence interval over authored messages.',
                         'Four force prefixes repeat sixteen old/new reference tuples in each sample.',
                         'Matching declared construction does not pin a probability distribution over reference bytes.',
                         'Three samples satisfying a threshold does not establish population-wide equivalence or authorise changing settlement.']}
    save(ROOT / 'replacement-audit.json', output)
    print(json.dumps({'rows': [{k:r[k] for k in ['submitter','value','member_recounts_match','all_member_means_at_most_zero','reference_tuple_count']} for r in summaries], 'overlap': overlaps}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch', action='store_true', help='Save public API source artifacts, without authentication')
    args = parser.parse_args()
    if args.fetch:
        c = AinglishClient(use_env=False)
        for h in HASHES:
            save(ROOT / 'replacement-sources' / (h + '.json'), c.measurement(h))
    audit()
