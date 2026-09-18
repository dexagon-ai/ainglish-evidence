"""Executor-side CPU inspection only; does not author, mint, or call readers."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from ainglish import panel, reader_qualification
from ainglish.client import manifest_commitment

root = Path(__file__).parent
evidence = root.parent
oldroot = evidence / 'resume-core-original-2026-09-17'
def read(path): return json.loads(path.read_text())
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
checks = []
def check(name, passed): checks.append({'check': name, 'passed': bool(passed)})

bundle = read(root/'saturnia-v2-bundle.json')
packet = read(root/'saturnia-v2-items.json')
items = packet['items']
old = read(oldroot/'saturnia-items.json')['items']
old_bundle = read(oldroot/'saturnia-bundle.json')
index = read(root/'saturnia-v2-groups.json')
old_index = read(oldroot/'saturnia-groups.json')
allocation = read(root/'saturnia-v2-allocation.json')
spec = read(oldroot/'runspec.json')
source = spec['items']
core = [r for r in items if not r.get('calibration')]
controls = [r for r in items if r.get('calibration')]
source_core = [r for r in source if not r.get('calibration')]
source_controls = [r for r in source if r.get('calibration')]

check('complete canonical item pin', digest(items) == bundle['items_sha256'] == packet['items_sha256'] == 'd2ee5b418a037e1054ccb1691bcf4c721ea2332c51ff2de6ae196bcb267ed940')
check('core pin', digest(core) == bundle['core_items_sha256'] == packet['core_items_sha256'] == '2c9ba0c3f057cd4d1baa00660c4f748802b55073691889fa474c058b80d40476')
check('control pin', digest(controls) == bundle['controls_sha256'] == packet['controls_sha256'] == '47b04e18f1c250508cd89171f5075b8762e8bdfb6fa361fa710e994edbf52a79')
check('unchanged source core and controls', digest(source_core) == 'a735c6e6fe7647cd80365b5ed7a9befa7c65e5f0b9d583cb7406a9832eceec8c' and digest(source_controls) == 'd41cb34ec0dfc9b914dcd77df39db474d4ec5ba195b5960f66f627e3360ad13e')
check('unchanged original manifest commitment', manifest_commitment(panel._planned_panel_manifest(spec)) == '763f2a4163f3813f863c8f33e7ec11f77bd5c8c74bffd16b657f24e037f46514')
check('all 72 backend IDs and ordering unchanged', [r['id'] for r in items] == [r['id'] for r in old] and len({r['id'] for r in items}) == 72 and len(core) == 64 and len(controls) == 8)

old_by = {r['id']:r for r in old}
exact_failures = []
semantic_failures = []
refs = {}
for row in core:
    prior = old_by[row['id']]
    name = re.search(r'^Fictional task ([^,]+),', row['english']).group(1)
    old_name = re.search(r'^Fictional task ([^,]+),', prior['english']).group(1)
    reconstructed = deepcopy(row)
    for arm in ('english','ainglish'):
        assert row[arm].count(name) == prior[arm].count(old_name) == 2
        reconstructed[arm] = reconstructed[arm].replace(name, old_name)
    st = reconstructed['strata']
    aliases = st.pop('block') == 'core' and st.pop('form') == st['policy'] and st.pop('lamp_condition') == st['question_variant']
    if reconstructed != prior or not aliases: exact_failures.append(row['id'])
    refs.setdefault((st['domain'],st['progress']),set()).add(name)
    text = row['ainglish']
    units = list(re.search(r'consists exactly of the four \w+ ([^,]+), ([^,]+), ([^,]+), and ([^,]+), in that order\.',text).groups())
    completed_text = re.search(r'previously completed: (.*?)\. Saved record',text).group(1)
    completed = [] if completed_text == 'none' else completed_text.split(', ')
    next_unit = re.search(r'and names (\w+) as the next unfinished',text).group(1)
    probe = st['probe_unit']
    performed = st['policy'] == 'redo' or probe not in completed
    lamp = performed if st['question_variant'] == 'performed' else not performed
    english = re.sub(r', resume-from\(([^)]+)\)\.$',r', continuing from checkpoint \1.',text).replace(', redo-from-start.',' again from the beginning.')
    if not (completed == units[:st['progress']] and next_unit == units[st['progress']] and probe in units and row['answer'] == ('Yes' if lamp else 'No') and english == row['english']): semantic_failures.append(row['id'])
check('exact narrow core diff only',not exact_failures)
check('same neutral task reference across both policies and question variants',len(refs)==16 and all(len(v)==1 for v in refs.values()) and all('resume' not in next(iter(v)) and 'redo' not in next(iter(v)) for v in refs.values()))
check('all 64 semantic golds and complete comparator transforms',not semantic_failures)

control_failures = []
for control_number, row in enumerate(controls):
    prior = old_by[row['id']]
    changed = {k for k in set(row)|set(prior) if row.get(k) != prior.get(k)}
    ci = row['control_interpretation']
    choices = prior['options'] + ['Not specified by this message']
    rotation = (2 * control_number) % len(choices)
    expected_options = choices[rotation:] + choices[:rotation]
    if not (changed == {'english','question','options','control_interpretation'}
            and row['options'] == expected_options
            and ci['english_correct_response'] == 'Not specified by this message'
            and ci['ainglish_correct_response'] == row['answer']
            and 'planted reviewer' in ci['scoring']
            and 'not a language comparison' in ci['scoring']
            and 'no assigned reviewer has been specified in this message' in row['english']
            and 'by this message?' in row['question']): control_failures.append(row['id'])
check('all eight truthful cold response contracts and unchanged planted golds',not control_failures)

mask = module('mask',oldroot/'instruction_mask_audit.py')
mask_old,mask_new,mask_source = mask.audit(old),mask.audit(items),mask.audit(source)
check('old shortcut reproduced in both arms', all(x['correct_without_instruction']==64 for x in mask_old.values()))
check('identified shortcut makes no successor or source prediction', all(x['predictions_without_instruction']==0 for x in [*mask_new.values(),*mask_source.values()]))

group = module('group',evidence/'resume-cluster-sensitivity-2026-09-17/group_sensitivity.py')
group.validate_index(index)
check('direct accepted-builder ledger reconstruction',group.group_index(items,[r['name'] for r in bundle['readers']],bundle['allocation_seed']) == index)
check('32 group memberships and reader allocations unchanged',index['groups']==old_index['groups'])
check('new group ledger hash bound',digest(index)==bundle['group_index_sha256'])
check('allocation bytes unchanged', (root/'saturnia-v2-allocation.json').read_bytes()==(oldroot/'saturnia-allocation.json').read_bytes())
check('canonical allocation pin and seed unchanged',digest(allocation)==bundle['allocation_sha256']=='900db70dd022a0578480443ca0a3e2064e9caf1a8ffbc3a950384f159c4c484e' and bundle['allocation_seed']==spec['seed']==2026091701)
for field in ('readers','comparator','settlement_strata'):
    check('unchanged '+field,bundle[field]==old_bundle[field])
analysis_fields = ('algorithm','canonical_plan_sha256','code_sha256','commit','draws','limitations','plan_file_sha256','sampling_seed','test_file_sha256')
check('unchanged scientific analysis pins and settings', all(bundle['analysis_binding'][k] == old_bundle['analysis_binding'][k] for k in analysis_fields))
check('source comparator and policy weights match replica',spec['comparator']==bundle['comparator'] and spec['settlement_strata']==bundle['settlement_strata'])
declared = [{k:v for k,v in panel.reader_receipt(ep).items() if k not in ('instrument_preparation','digest_source')} for ep in spec['panel']]
check('source scientific reader settings match replica declarations',declared==bundle['readers'])
check('call cap unchanged',bundle['maximum_calls_per_executor']==160 and allocation['target_cells']==128 and allocation['calibration_cells']==32)

overlap = {
 'pairs':len({(x['english'],x['ainglish']) for x in source}&{(x['english'],x['ainglish']) for x in items}),
 'arms':len({x[a] for x in source for a in ('english','ainglish')}&{x[a] for x in items for a in ('english','ainglish')}),
 'ids':len({x['id'] for x in source}&{x['id'] for x in items}),
}
check('zero exact source overlap',not any(overlap.values()))
dim = lambda rows: Counter((x['strata']['domain'],x['settlement_stratum'],x['strata']['progress']) for x in rows)
check('same source and replica domain policy progress distribution',dim(core)==dim(source_core))
check('same per-policy gold and position balance',Counter((x['settlement_stratum'],x['answer'],x['options'].index(x['answer'])) for x in core)==Counter((x['settlement_stratum'],x['answer'],x['options'].index(x['answer'])) for x in source_core))
now=datetime.now(timezone.utc)
qualifications=[reader_qualification.validate(q) for q in spec['reader_qualifications']]
check('retained qualifications not expired',all(datetime.fromisoformat(q['qualified_at'])<=now<datetime.fromisoformat(q['valid_until']) for q in qualifications))
check('no execution journal or frozen-original attempt yet',not (oldroot/'execution-started.json').exists() and all(x['pin']['manifest_commitment']!='763f2a4163f3813f863c8f33e7ec11f77bd5c8c74bffd16b657f24e037f46514' for x in read(root/'preparation-proposal.json')['attempts']))
report={'kind':'read-only-executor-successor-inspection','checked_at':now.isoformat(),'passed':all(c['passed'] for c in checks),'checks':checks,'overlap':overlap,'mask_successor':mask_new,'semantic_failure_ids':semantic_failures,'control_failure_ids':control_failures,'reader_calls':0,'attempts_minted':0,'execution_authorized':False,'limits':['Input and retained-qualification inspection only; live instrument preparation, current eligibility, preflight and mint remain execution-time checks.','The particular label shortcut is closed, not every conceivable shortcut. Exact disjointness is not proof of independent semantic worlds.','No population, no-loss, language-performance or ratification claim. No remote write and no hold-file change.']}
report['inspection_correction'] = 'The first inspection incorrectly required the new absence option always be last and descriptive analysis test-count metadata be identical. The reviewed successor instead uses prospectively frozen two-position rotations across nine options and preserves every scientific analysis pin. No bank or protocol was changed by this inspection correction.'
print(json.dumps(report,indent=2))

