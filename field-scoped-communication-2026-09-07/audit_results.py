"""Post-run integrity and declared-score reconstruction, not a changed scorer."""
from collections import defaultdict
import json
from study import ROOT, Journal, decode, reader_messages, verify_freeze
from runtime import digest, save_new

commit = verify_freeze(ROOT)
plan = json.loads((ROOT / 'PLAN.json').read_text())
events = Journal._validate((ROOT / 'execution/calls.jsonl').read_text())
begins = {e['data']['call_id']: e['data'] for e in events if e['kind'] == 'begin'}
ends = {e['data']['call_id']: e['data'] for e in events if e['kind'] == 'end'}
assert len(begins) == len(ends) == 264 and set(begins) == set(ends)
for key in begins:
    assert begins[key]['request_hash'] == digest(begins[key]['request']) == ends[key]['request_hash']
    assert ends[key]['input_tokens'] == len(ends[key]['input_ids'])
    assert ends[key]['output_tokens'] == len(ends[key]['output_ids'])
    assert ends[key]['ended']
neutral = json.loads((ROOT / 'controls.json').read_text())
controls = defaultdict(list)
for c in neutral:
    key = 'qualification/' + c['id']
    assert begins[key]['request']['messages'] == c['messages']
    controls[c['dimensions']].append(decode(ends[key]['raw'], c['brief']) == c['brief'])
qualified = {d: sum(rows) >= 14 for d, rows in controls.items()}
assert qualified == {1: False, 2: True, 5: True}
cases = json.loads((ROOT.parent / 'communication-diagnostics-2026-09-06/cases.json').read_text())
groups = defaultdict(list)
for c in cases:
    for arm in ['ainglish', 'english']:
        key = 'target/' + c['id'] + '/' + arm
        if not qualified[c['dimensions']]:
            assert key not in begins
            continue
        assert begins[key]['request']['messages'] == reader_messages(c, arm, c['messages'][arm])
        groups[(c['dimensions'], arm)].append(decode(ends[key]['raw'], c['brief']) == c['brief'])
summary = [{'dimensions': d, 'arm': arm, 'correct': sum(rows), 'total': len(rows)}
           for (d, arm), rows in groups.items()]
audit = {'kind': 'ainglish.field-scoped-declared-score-audit.v1', 'freeze': commit,
         'begin_end_pairs': 264, 'control_calls': 48, 'target_calls': 216,
         'truncated': 0, 'qualified_dimensions': qualified, 'joint_accuracy': summary,
         'governance_evidence': False, 'post_run_audit': True}
save_new(ROOT / 'AUDIT.json', audit)
print(json.dumps(audit, indent=2))
