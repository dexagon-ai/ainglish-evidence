"""Prospective metadata repair after a zero-call dry-preview refusal; preserve v1."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = ROOT / 'postpone-careful'
target = ROOT / 'postpone-careful-v2'
target.mkdir(exist_ok=False)
spec = json.loads((source / 'unbound-runspec.json').read_text())
old_items = json.loads((source / 'items.json').read_text())
items = json.loads(json.dumps(old_items))
for item in items:
    if not item.get('calibration'):
        item['settlement_stratum'] = item['settlement_stratum'].replace(' ', '-')
for old, new in zip(old_items, items):
    assert {k: v for k, v in old.items() if k != 'settlement_stratum'} == {k: v for k, v in new.items() if k != 'settlement_stratum'}
counts = dict(Counter(i['settlement_stratum'] for i in items if not i.get('calibration')))
digest = hashlib.sha256(json.dumps(items, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
spec['items'] = items; spec['items_sha256'] = digest
for stratum in spec['settlement_strata']:
    stratum['id'] = stratum['id'].replace(' ', '-')
spec['attempt']['planned_sample']['strata'] = counts
audit = json.loads((source / 'design-audit.json').read_text())
audit['items_sha256'] = digest; audit['strata'] = counts
audit['preparation_history'] = 'v1 dry preview refused whitespace in stratum identifiers; no attempt, calibration or target call. V1 remains at ../postpone-careful and commit b8c03a7. Only metadata spelling changed; exact texts, golds, seed and readers are unchanged.'
for name, data in [('items.json', items), ('unbound-runspec.json', spec), ('design-audit.json', audit), ('claim-lock.json', json.loads((source / 'claim-lock.json').read_text()))]:
    with (target / name).open('x') as f:
        json.dump(data, f, indent=2, ensure_ascii=False); f.write('\n')
print('Prepared metadata-only v2; v1 retained; no experimental calls')
