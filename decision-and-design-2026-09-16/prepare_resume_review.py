"""Assemble a held review inventory; never mint, qualify, infer, or file results."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys

from ainglish.panel import _validate_learnability_v2

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def main():
    proposal = json.loads(Path(sys.argv[1]).read_text())
    corrected = REPO / 'resume-boundary-correction-2026-09-16'
    receipts = json.loads((corrected/'correction-receipt.json').read_text())
    learning = json.loads((corrected/'learning-items.json').read_text())
    careful = json.loads((corrected/'careful-items.json').read_text())
    old = json.loads((REPO/'completion-paths-2026-09-10/reader-packets/resume-learning/items.json').read_text())
    controls = [r for r in old if r.get('calibration')]
    assert len(controls) == 8 and len(learning) == len(careful) == 96
    assert digest(learning) == receipts['banks']['learning-items.json']['corrected_items_sha256']
    assert digest(careful) == receipts['banks']['careful-items.json']['corrected_items_sha256']
    assert old[:64] == learning[:64]
    assert all(r['english'] == r['ainglish'] for r in learning)
    inventory = copy.deepcopy(learning + controls)
    assert len({r['id'] for r in inventory}) == 104
    text = 'Registered form: ' + proposal['form'] + '\n\n' + proposal['english_mapping']
    entry = {'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest(),
             'source_url': 'https://ainglish.org/api/v1/proposals/'+proposal['slug'],
             'proposal_revision': proposal['slug']}
    assert _validate_learnability_v2({'slug':proposal['slug'], 'form':proposal['form'],
                                     'construct':proposal['form'], 'entry':entry}, learning, controls)
    groups = Counter(r['strata']['block'] for r in learning)
    assert groups == {'core':64,'boundary':32}
    out = HERE/'resume-review'; out.mkdir(exist_ok=True)
    (out/'learning-inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n')
    plan = {
        'kind':'resume-scoped-review-inventory-v2', 'state':'HELD_NOT_EXECUTABLE',
        'public_id':proposal['public_id'], 'slug':proposal['slug'], 'entry':entry,
        'learning_inventory_sha256':digest(inventory), 'review_rows':104,
        'corrected_careful_targets_sha256':digest(careful),
        'corrected_learning_targets_sha256':digest(learning),
        'controls_sha256':digest(controls),
        'unchanged_author_accepted_core_rows':64,
        'changed_boundary_ids':receipts['changed_ids'],
        'boundary_premises_author_accepted':True,
        'boundary_acceptance_comment':'96f80d4c-685c-4220-93bb-cdd4d6b6583b',
        'author_notice_stale_on_premise_hold':True,
        'calibration_reused_without_relabeling':True,
        'not_one_official_combined_score':True,
        'proposed_separate_blocks':[
            {'metric':'comprehension_accuracy_delta','scope':'core','targets':64,
             'two_reader_real_calls':128,'two_reader_calibration_calls':32},
            {'metric':'comprehension_accuracy_delta','scope':'boundary_diagnostic','targets':32,
             'two_reader_real_calls':64,'two_reader_calibration_calls':32},
            {'metric':'learnability','scope':'core','targets':64,
             'two_reader_real_calls':256,'two_reader_calibration_calls':32},
            {'metric':'learnability','scope':'boundary_diagnostic','targets':32,
             'two_reader_real_calls':128,'two_reader_calibration_calls':32}],
        'conditional_calls_per_executor_for_all_four_blocks':704,
        'conditional_calls_two_executors':1408,
        'budget_exclusions':['qualification','retries forbidden unless prospectively specified',
                            'any new comparator or auxiliary study'],
        'reader_roster':[], 'accepted_independent_replicator':None,
        'attempt_ids':[], 'actual_reader_calls':0,
        'remaining_decisions':[
            'Refresh stale API notice to record the already-completed two-premise review; do not repeat accepted semantic checks.',
            'Author/design reviewer accept separate core and boundary reporting and filing; no automatic combined score.',
            'Choose exact future original and independently authored disjoint replication route; current inventory is not an exact replication of old CAD a9d3a180.',
            'Review uncertainty and world/frame dependence; 64 or 32 item IDs do not certify independent sampling units.',
            'Verify named model/provider/digest/settings access, qualifications, capacity and real independent role acceptance.',
            'Freeze exact execution, per-form strata/weights, cross-metric exposure ledger, preregistration sequence and stop rules before any target call.',
            'Honor author hold and unresolved CAD prerequisite before any learning spend; inspect current rules and proposal again.',
            'Check native Linux resources at execution; do not reuse obsolete WSL/Windows disk gates.'],
        'author_notice_at_read':proposal['author_work_notices']['active']['notice_id'],
        'current_evidence_contract':proposal['evidence_contract'],
        'scope_warning':'All 104 rows are a review inventory, not a runspec. Shared-rule boundary success is not isolated entry learning. Reused worlds across metrics do not create independent corroboration.',
    }
    assert sum(x['two_reader_real_calls']+x['two_reader_calibration_calls']
               for x in plan['proposed_separate_blocks']) == 704
    (out/'review-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status':plan['state'],'rows':104,'actual_reader_calls':0,
                      'inventory_sha256':digest(inventory),'entry_sha256':entry['sha256']}))


if __name__ == '__main__':
    main()
