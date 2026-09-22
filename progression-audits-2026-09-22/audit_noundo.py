"""Independent CPU-only witnesses; argv[1] is the pinned packet directory."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location('noundo_packet', Path(sys.argv[1]) / 'noundo_rstar.py')
packet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packet)
packet.selftest()
results = {}
for name, arm in {
    'empty_holder': 'Deleted the branch, can-undo(reflog; ).',
    'closing_parenthesis_in_holder': 'Deleted the branch, can-undo(reflog; oper)ator).',
    'exclusive_uppercase_holder': 'Deleted the branch, can-undo(reflog; ONLY operator).',
    'punctuated_no_undo_action': 'Deleted the branch.; now wait, no-undo.',
}.items():
    try:
        fields = packet.parse_marked(arm)
        results[name] = {'accepted': True, 'roundtrip': packet.render_marked(fields) == arm,
                         'rendered': packet.render_rstar(fields)}
    except ValueError as e:
        results[name] = {'accepted': False, 'reason': str(e)}

bank = packet.synthetic_bank()
# Mutate a real holder slot while preserving every scheduled count and ACTION.
for pair in bank:
    fields = packet.parse_marked(pair['ainglish'])
    if fields.get('holder'):
        fields['holder'] = 'oper)ator'
        pair.update(ainglish=packet.render_marked(fields), english=packet.render_rstar(fields))
        break
try:
    packet.validate_bank(bank)
    results['whole_bank_invalid_holder'] = 'ACCEPTED'
except ValueError as e:
    results['whole_bank_invalid_holder'] = str(e)

bank = packet.synthetic_bank()
# All ACTIONs keep the same words and lengths, but report/instruction labels are inverted.
for pair in bank:
    pair['shape'] = 'instruction' if pair['shape'] == 'report' else 'report'
try:
    packet.validate_bank(bank)
    results['inverted_shape_labels'] = 'ACCEPTED'
except ValueError as e:
    results['inverted_shape_labels'] = str(e)
print(json.dumps(results, indent=2))
assert results['whole_bank_invalid_holder'] == 'ACCEPTED'
assert results['closing_parenthesis_in_holder']['roundtrip']
