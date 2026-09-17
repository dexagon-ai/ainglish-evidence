"""Build the prospective analysis packet from existing frozen bytes. No reader calls."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from ainglish import panel
from ainglish.client import _validate_attempt_manifest
import group_sensitivity as g

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'execution-decisions-2026-09-17'


def main():
    old = json.loads((SOURCE/'resume-phase-one.json').read_text())
    spec = deepcopy(old['runspec_candidate_not_authorized'])
    index = g.group_index(spec['items'], [p['name'] for p in spec['panel']], spec['seed'])
    code_hash = hashlib.sha256((HERE/'group_sensitivity.py').read_bytes()).hexdigest()
    plan = {
        'kind': 'ainglish.resume-companion-analysis-plan.v1', 'algorithm': g.ALGORITHM,
        'analysis_code_sha256': code_hash, 'sampling_seed': g.SEED, 'draws': g.DRAWS,
        'domain_composition': 'fixed: media, reading, review, simulation; no domain resampling',
        'blocks': 'four progress groups within each of eight domain/policy blocks; sample four with replacement in each block',
        'sampling_unit': 'both complementary items and all reader cells in one domain/policy/progress group',
        'draw_index': 'first unsigned 64-bit big-endian word of SHA256(NUL-joined algorithm, decimal seed, domain:policy block, decimal draw, decimal position), modulo 4',
        'policy_weights': {'resume-core': 0.5, 'redo-core': 0.5},
        'estimator': 'Pool live correct/live totals within each policy arm, take marked minus English in percentage points, then the equal-policy mean. Unrounded ratios, as in official bootstrap draws; report raw point separately from SDK display rounding.',
        'invalid_draw': 'If either arm of either policy is unobservable, discard that draw jointly for all three intervals; report every invalid index/count and missing-arm reason; never retry or replace a draw.',
        'quantiles': 'On the common accepted-draw set, sort each of aggregate/resume/redo separately; take zero-index floor(25*n/1000) and floor(975*n/1000). No interpolation. Zero accepted draws yields a held diagnostic, not numeric bounds.',
        'degeneracy': 'Report zero-width intervals as degenerate; do not infer certainty, equality or usable evidence from them.',
        'scope': 'Report-only fixed-battery sensitivity, not validated nominal population coverage and not a substitute for official SDK bounds or current settlement.',
        'missing_cells': 'Require exactly all 128 planned cells. Preserve explicit absent-cell nulls and their count; a missing, duplicate, extra or misallocated cell refuses analysis.',
    }
    pins = {'analysis_code_sha256': code_hash, 'analysis_plan_sha256': g.digest(plan),
            'group_index_sha256': g.digest(index)}
    spec['study_scope'] += (' Report-only grouped sensitivity '+g.ALGORITHM+
        '; code_sha256='+code_hash+'; plan_sha256='+pins['analysis_plan_sha256']+
        '; group_index_sha256='+pins['group_index_sha256']+'. Fixed domains, paired items and all reader cells retained. No validated coverage or changed settlement rule.')
    assert len(spec['study_scope']) <= 1000
    spec['attempt']['planned_sample']['report_only_companion_analysis'] = pins
    spec['attempt']['admissibility_gates'].extend([
        'Design reviewer accepts the exact pinned companion analysis; original and replica group-index/code/plan digests and actual allocations are frozen before either target bank is exposed.',
        'A zero-crossing interval with a nonnegative point is not demonstrated no-loss or equivalence. Ceiling/floor/strata-unresolved remains unresolved.',
        'Learning and boundary targets remain unexposed until both CAD studies are public, live CAD is neither unresolved nor opposing, and the separate later exposure/filing design has been reviewed.',
    ])
    scientific = ['items','items_sha256','items_url','seed','metric','panel','panel_neff',
                  'reader_qualifications','settlement_strata','comparator','construct','form']
    assert all(spec[k] == old['runspec_candidate_not_authorized'][k] for k in scientific)
    manifest = panel._planned_panel_manifest(spec)
    raw = _validate_attempt_manifest(manifest)
    assert all(v in manifest['study_scope'] for v in pins.values())
    envelope = {
        'kind': 'ainglish.held-execution-decision.v2', 'state': 'HELD_FOR_ANALYSIS_REVIEW_AND_FROZEN_REPLICA_BANK',
        'reader_calls': 0, 'attempt_ids': [], 'supersedes_preparation_only': '1647b9610187c0d831a302f0433b7ef281174043/execution-decisions-2026-09-17/resume-phase-one.json',
        'author_conditional_design_acceptance': 'https://thecolony.ai/post/ec91abf8-427a-40a8-a899-7e7c4ba277ab#comment-69b9008e-eec2-4e78-9a04-14f1e92d5bca',
        'independent_conditional_design_and_replication_acceptance': 'https://thecolony.ai/post/ec91abf8-427a-40a8-a899-7e7c4ba277ab#comment-400aad4d-46b9-468e-8dd4-d7298ed3b88f',
        'analysis_revision_acceptance': None, 'frozen_replica_bank': None,
        'pins': pins, 'manifest_canonical_bytes': len(raw), 'manifest_sha256': g.digest(manifest),
        'runspec_candidate_not_authorized': spec,
    }
    for name, data in [('group-index.json',index),('analysis-plan.json',plan),
                       ('held-execution.json',envelope),('planned-manifest.json',manifest)]:
        (HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pins':pins, 'manifest_canonical_bytes':len(raw), 'reader_calls':0}))


if __name__ == '__main__':
    main()
