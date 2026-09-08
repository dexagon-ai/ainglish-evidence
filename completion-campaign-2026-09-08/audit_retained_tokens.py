"""Read-only reproduction of retained-source arithmetic audits; not replications.

Run with ainglish and tiktoken 0.14.0 already installed. This script makes no API
write, downloads no model, and counts only the committed public source strings.
"""
import importlib.metadata
import json
from pathlib import Path
from ainglish.measure import token_delta
from ainglish.client import manifest_commitment


def main():
    assert importlib.metadata.version('tiktoken') == '0.14.0'
    rows = []
    for path in sorted((Path(__file__).resolve().parent / 'corrections').glob('*-audit.json')):
        record = json.loads(path.read_text())
        manifest = record['source_manifest']
        assert manifest_commitment(manifest) == record['manifest_hash']
        result = token_delta([(x['english'], x['ainglish']) for x in manifest['test_set']], manifest['models'])
        assert result == record['recount'], path.name
        actual = [result['by_tokenizer'][m]['mean'] for m in manifest['models']]
        filed = [x['value'] for x in record['filed_per_member']]
        assert result['floor'] != record['filed_value'] or actual != filed
        rows.append({'approval_id': record['approval_id'], 'filed': record['filed_value'],
                     'recomputed': result['floor'], 'per_member_matches': actual == filed})
    assert len(rows) == 10
    print(json.dumps({'source_audits_reproduced': len(rows), 'independent_replications': 0, 'rows': rows}, indent=2))


if __name__ == '__main__':
    main()
