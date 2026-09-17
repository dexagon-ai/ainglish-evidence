"""Prepare held decisions using existing inputs; never mint, qualify, infer or file."""
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from ainglish import panel, reader_qualification

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(name, value):
    (HERE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def resume(proposal):
    corrected = read(REPO/'resume-boundary-correction-2026-09-16/careful-items.json')
    learning = read(REPO/'decision-and-design-2026-09-16/resume-review/learning-inventory.json')
    core = deepcopy(corrected[:64])
    controls = deepcopy([x for x in learning if x.get('calibration')])
    assert len(controls) == 8 and len(core) == 64
    assert all(x['strata']['block'] == 'core' for x in core)
    assert Counter(x['settlement_stratum'] for x in core) == {'resume-core':32, 'redo-core':32}
    write('resume-core-items.json', core+controls)
    existing = REPO/'overnight-decisions-2026-09-14/verified-replication'
    endpoints, qualifications, access = [], [], []
    now = datetime.now(timezone.utc)
    for name in ('gemma', 'mistral'):
        screen = read(existing/(name+'.screen.json'))
        record = read(existing/(name+'.qualification.json'))
        qual = reader_qualification.validate(record['receipt'])
        endpoint = deepcopy(screen['reader'])
        # Metadata-only binding fetch; no reader/qualification request is made.
        prepared = panel.prepare_reader_instruments({'panel':[endpoint]})['panel'][0]
        settings = panel.reader_receipt(prepared)
        assert digest(settings) == qual['settings_sha256']
        assert prepared['model_digest'] == qual['reader']['model_digest']
        assert datetime.fromisoformat(qual['qualified_at']) <= now < datetime.fromisoformat(qual['valid_until'])
        endpoints.append(prepared)
        qualifications.append(qual)
        access.append({'model':prepared['model'], 'digest':prepared['model_digest'],
                       'settings_sha256':digest(settings), 'valid_until':qual['valid_until'],
                       'metadata_checked_at':now.isoformat(), 'new_reader_calls':0})
    candidate = {
        'public_id':proposal['public_id'], 'slug':proposal['slug'],
        'form':proposal['form'], 'construct':proposal['form'],
        'metric':'comprehension_accuracy_delta', 'seed':2026091701,
        'panel':endpoints, 'panel_neff':2, 'reader_qualifications':qualifications,
        'planted_arm':'ainglish', 'calibration_min_gap':0.5,
        'items':core+controls, 'items_sha256':digest(core+controls),
        'items_url':'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/5a9f85664b4edf4f84ceb1a878769e0908ddd1b4/execution-decisions-2026-09-17/resume-core-items.json',
        'settlement_strata':[{'id':'resume-core','weight':1},{'id':'redo-core','weight':1}],
        'comparator':{'kind':'complete-canonical-concise-english-v1',
                      'description':'Exact registered concise templates; task and checkpoint facts unchanged in both arms. Core-only scope.'},
        'study_purpose':'claim_test',
        'study_scope':'Fixed accepted 64-item core battery only; not boundary learning, independent world sampling, or a replication of the old differently scoped reader population.',
        'attempt':{
            'estimand':'Equal-weight mean of resume-core and redo-core Ainglish-minus-canonical-English accuracy differences, percentage points, on the frozen 64-item battery and exact two-instrument roster.',
            'admissibility_gates':[
                'Explicit author/design acceptance and independently accepted replication capacity before target exposure; no silence-as-consent.',
                'Fresh proposal/version, live exact work and full discussion are compatible; no changed source/comparator/population or unresolved design objection.',
                'Exact local model digests/settings and unexpired qualification receipts match; both distinct declared base-model lineages remain present.',
                'Original and independently authored replication inputs and scope are frozen before the first original target call; wholly disjoint complete replica pairs.',
                'No retries, model substitution, seed search, outcome-based exclusions, sample enlargement or premature learning/boundary spend.',
                'Native host resources and GPU ownership are safe; preserve all partial journals and official calibration/yield refusals.'
            ],
            'planned_sample':{'core_items':64, 'calibration_items':8, 'readers':2,
                              'target_calls':128, 'calibration_calls':32, 'total_calls':160},
            'proposal_revision':proposal['slug']
        }
    }
    contract = panel._settlement_contract(candidate, core, endpoints, candidate['seed'])
    assert contract and panel._validate_panel_declarations(candidate, endpoints)
    # The official dry oracle derives structure, not data. Do not publish mock scores as evidence.
    manifest = panel._planned_panel_manifest(candidate)
    from ainglish.client import _validate_attempt_manifest
    canonical_manifest = _validate_attempt_manifest(manifest)
    allocation = defaultdict(Counter)
    groups = defaultdict(list)
    for item in core:
        st = item['strata']
        groups[f"{st['domain']}:{st['form']}:{st['progress']}"].append(item['id'])
        for reader in endpoints:
            allocation[item['settlement_stratum']+':'+reader['name']][
                panel.arm_for(candidate['seed'],reader['name'],item['id'])] += 1
    assert len(groups) == 32 and all(len(ids) == 2 for ids in groups.values())
    plan = {'kind':'ainglish.held-execution-decision.v1', 'state':'HELD_NO_MINT_NO_READER_CALLS',
            'author_design_acceptance':None, 'accepted_independent_executor':None,
            'author_structural_decision':{
                'comment_id':'0e4ebb16-8a61-4618-bbf8-512f53fef631',
                'at':'2026-09-17T09:29:44Z',
                'accepted':'core/boundary separation in principle and proceeding to independent execution/analysis design review',
                'not_accepted':'exact inventory, analysis, reader roster, call envelope, qualification, capacity or launch',
                'notice_id':'eef02c05-4406-4387-8c22-a67c9f54c598'},
            'actual_reader_calls':0, 'attempt_ids':[], 'public_id':proposal['public_id'],
            'core_items_sha256':digest(core), 'controls_sha256':digest(controls),
            'model_access':access, 'allocation':dict(allocation),
            'analysis_groups_not_independent_world_claims':dict(groups),
            'dry_structure_check':'SDK 0.2.61 official planned-manifest derivation passed; mock scores discarded',
            'candidate_planned_manifest_sha256':digest(manifest),
            'candidate_manifest_canonical_bytes':len(canonical_manifest),
            'runspec_candidate_not_authorized':candidate,
            'remaining':['author/design scope and uncertainty acceptance',
                         'independent executor acceptance and disjoint bank',
                         'fresh eligibility, server preflight and exact attempt mint'],
            'later_learning_and_boundary_legs':'Not included or authorized; full claim remains incomplete after this core phase.'}
    write('resume-phase-one.json',plan)
    print(json.dumps({'resume_state':plan['state'], 'core_sha256':digest(core),
                      'calls_if_authorized':160,'new_reader_calls':0,'qualified_models':len(endpoints)}))


def they():
    source_path = REPO/'preservation-successor-review-2026-09-16/amendment-changes.json'
    source = read(source_path)
    source_file_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert source_file_digest == 'aba6a6195b1d20fc351eddb928aa6a6bcc9ae5e00f56e877ab540393e94ac048'
    old = 'an approved replayable simultaneous uncertainty method'
    new = ('the prospectively reviewed they-method-policy-v2: a replayable, all-required '
           'marginal-test policy, not a promise of simultaneous confidence coverage. '
           'Every prespecified aggregate, form, accuracy, safety, nonclaim and '
           'positive-control requirement must meet its named directional marginal test '
           'at one-sided level at most 0.05. Validity under the actual world/reader '
           'sampling design is a prerequisite: use independent world units or a '
           'prospectively reviewed clustered method, never count option swaps, '
           'paraphrases or repeated probes as independent worlds. Freeze each null, '
           'direction, estimator, rounding/tie rule, analysis population and actual '
           'interval coverage before exposure. Print the applied method and '
           'marginal-not-simultaneous label beside every reported bundle decision. '
           'A held or invalid component cannot support the bundle, a valid opposing '
           'component still counts, and no successful subset can become a bundle pass')
    assert source['predicted_measurement'].count(old) == 1
    candidate = deepcopy(source)
    candidate['predicted_measurement'] = source['predicted_measurement'].replace(old,new)
    assert [k for k in source if source[k] != candidate[k]] == ['predicted_measurement']
    write('they-method-choice.json',{'kind':'ainglish.author-method-choice.v2',
        'state':'PROPOSED_NOT_ACCEPTED_NOT_OPERATIVE', 'author':'Saturnia',
        'accepted_source_commit':'579560f8789811b3c29383b4165a671ff6121ada',
        'accepted_source_changes_file_sha256':source_file_digest, 'replace_exact':old, 'with_exact':new,
        'proposed_candidate':candidate, 'proposed_candidate_sha256':digest(candidate),
        'candidate_digest_encoding':'UTF-8 JSON, sorted keys, compact separators, ensure_ascii=False',
        'changed_fields':['predicted_measurement'], 'target_bank_made':False,
        'amendment_dry_run':False, 'reader_calls':0, 'author_decision':None})
    print(json.dumps({'they_candidate_sha256':digest(candidate),'author_decision':None}))


if __name__ == '__main__':
    proposal = read(Path(sys.argv[1]))
    resume(proposal.get('proposal',proposal))
    they()
