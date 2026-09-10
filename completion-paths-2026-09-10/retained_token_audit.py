"""Recount already-published inputs; not a new sample or independent confirmation."""
import json
from pathlib import Path
from ainglish.measure import token_delta
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent
SOURCES = [
    '7ddf8b714cff39ca2f19d01690b384c0ef364e5aee0d8b70d3cf82f628684747',
    '0079e4b471d850d87305e84b307581f1ad25691358009c8fcaea9c87344b9746',
    '903b67a697f5e000b7c57ab64f491e33a7b05aacc67fd5d05a0a99d7c1a6a670',
    '256a92882cc54e2347488c832bbcbd6171f8027482f4e1913217bebbe470ff24',
    'e2ff808e72df863f2c403344843ac1f8e81cd6ae3b55ed3150e05ff922de5842',
]

def main():
    out = ROOT / 'retained-token-audit.json'
    if out.exists():
        raise RuntimeError('Keep the first audit; do not overwrite')
    c = ainglish_client()
    results = []
    for source in SOURCES:
        m = c.measurement(source); manifest = m['manifest']
        assert manifest_commitment(manifest) == source
        counted = token_delta(manifest['test_set'], manifest['models'])
        # These five manifests use no strata or balanced equal-weight strata.
        # Check that condition before using the unweighted reference aggregate.
        strata = manifest.get('settlement_strata')
        if strata:
            counts = [sum(x.get('stratum') == s['id'] for x in manifest['test_set']) for s in strata]
            assert len(set(counts)) == 1 and len({s.get('weight', 1) for s in strata}) == 1
        claimed = {x['model']: x['value'] for x in m['per_member']}
        actual = {k:v['mean'] for k,v in counted['by_tokenizer'].items()}
        results.append({'source':source, 'source_attempt':m['attempt_id'],
            'public_measurement':'https://ainglish.org/measurements/' + source,
            'submitter':m['submitter']['name'], 'pair_count':len(manifest['test_set']),
            'claimed_members':claimed, 'recounted_members':actual,
            'claimed_headline':m['value'], 'recounted_headline':counted['floor'],
            'all_values_match':actual == claimed and counted['floor'] == m['value'],
            'per_pair':counted['by_tokenizer'], 'settlement_state_at_read':m['settlement_state']})
        print(source[:8], results[-1]['all_values_match'], actual, flush=True)
    with out.open('x') as f:
        json.dump({'kind':'retained-input-arithmetic-audit', 'new_measurement':False,
                   'scope':'Five specified modern disputed token originals, including our own; retained-byte verification only. No inference, new sampling, confirmation or governance write.',
                   'results':results}, f, indent=2)

if __name__ == '__main__':
    main()
