"""Offline replay of published bytes, not another scientific measurement."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from ainglish.client import manifest_commitment
from ainglish.token_measurement import verify_payload

ROOT = Path(__file__).parent

def read(name):
    return json.loads((ROOT / name).read_text())

def main():
    plan = read('plan.json')
    result = read('result.json')
    source = read('source.json')
    m = result['payload']['manifest']
    assert m == plan['manifest']
    assert manifest_commitment(m) == plan['manifest_commitment']
    assert manifest_commitment(source['manifest']) == m['replicates_hash']
    assert result['payload']['replicates_hash'] == source['manifest_hash']
    rows = m['test_set']
    pairs = {(x['english'], x['ainglish']) for x in rows}
    old = {(x['english'], x['ainglish']) for x in source['manifest']['test_set']}
    assert len(rows) == len(pairs) == 64 and not pairs & old
    assert Counter(x['stratum'] for x in rows) == {'finish-started':32,'interrupt-started':32}
    assert m['settlement_strata'] == source['manifest']['settlement_strata']
    assert m['models'] == source['manifest']['models']
    for row in rows:
        form = row['stratum']
        suffix = f', {form}.'
        assert row['ainglish'].startswith('Stop ') and row['ainglish'].endswith(suffix)
        scope = row['ainglish'][5:-len(suffix)]
        ending = 'let running tasks finish.' if form == 'finish-started' else 'interrupt running tasks.'
        assert row['english'] == f'In {scope}, start no new tasks; {ending}'
    import tiktoken
    with patch('tiktoken.load.read_file', side_effect=RuntimeError('Offline audit: no downloads')):
        verify_payload(result['payload'])
        diagnostic = read('mapping-cost-diagnostic.json')
        text = m['entry_cost_diagnostic']['text']
        assert hashlib.sha256(text.encode()).hexdigest() == diagnostic['text_sha256']
        for model, observed in diagnostic['by_tokenizer'].items():
            count = len(tiktoken.get_encoding(model).encode(text))
            assert count == observed['complete_mapping_tokens']
            saving = observed['measured_average_saving']
            assert observed['mapping_only_average_break_even_uses'] == (math.ceil(count/saving) if saving>0 else None)
    readback = read('measurement-readback.json')
    assert readback['attempt']['state'] == 'completed'
    assert readback['reproduced_ok'] is True and readback['settlement_eligible'] is True
    assert readback['disjoint_from_proposer'] is False
    assert read('source-after-file.json')['confirmed'] is True
    print(json.dumps({'audit':'passed','pairs':64,'source_pair_overlap':0,'templates':2,'tokenizers':3,'manifest_commitment':plan['manifest_commitment'],'network':False,'new_measurement':False}))

if __name__ == '__main__':
    main()
