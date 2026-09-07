"""Reconcile stored receipts, without loading a tokenizer or submitting again."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def analyse():
    rows = []
    for name, bound in [('replied', 3), ('instance', 2)]:
        folder = ROOT / 'execution' / name
        result = json.loads((folder / 'result.json').read_text())
        source = json.loads((folder / 'source.json').read_text())
        payload, audit = result['payload'], result['audit']
        assert payload['value'] == source['value']
        assert audit['manifest_commitment'] == source['manifest_hash']
        assert source['derivation_verified'] is True
        server = source['token_derivation']
        assert server['pair_count'] == audit['pair_count'] == 256
        assert server['per_member'] == {r['model']: r['value'] for r in payload['per_member']}
        assert source['value'] == max(server['per_member'].values())
        rows.append(dict(study=name, bound=bound, value=source['value'],
                         within_point_bound=source['value'] <= bound,
                         attempt_id=source['attempt_id'], manifest_hash=source['manifest_hash'],
                         pair_count=256, by_tokenizer=audit['by_tokenizer'],
                         server_derivation_verified=True,
                         evidence_state=source['evidence_state'],
                         settlement_state=source['settlement_state'],
                         counts_toward_verdict=source['counts_toward_verdict']))
    return {'kind': 'ainglish.full-sized-token-results.v1', 'studies': rows,
            'scope': 'Present frozen tiktoken encodings and complete paired claims, not comprehension or future-trained efficiency.',
            'next': 'Independent fresh-input checks; author assessment of failed current cost bounds. Hold dependent comprehension execution.'}


if __name__ == '__main__':
    value = analyse()
    with (ROOT / 'ANALYSIS.json').open('x') as out:
        out.write(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value, indent=2))
