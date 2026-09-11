"""Public decision-oriented inventory, not a queue override or eligibility ruling."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
from ainglish.client import AinglishClient

SPECIAL={
 'a-mv841prke9x9e5cm':('author_comparator_decision',
    'Author resolves fixed renderer versus menu-minimum, writer-relative no-path scope and holder exclusivity before another token campaign.',
    'New English wording or population requires a prospective original/amendment, not a relabelled replication.'),
 'a-94wc58sz8ks3ce4y':('author_retirement_chosen',
    'Colonist One has chosen no further revision study. Resolve the already-designated diagnostic/attempt status, then await activation and a fresh eligible author request.',
    'Do not spend to rescue this version; do not call the author decision a proven full falsifier or a completed retirement.'),
 'a-abfbkq5mhjxr5nr7':('author_non_adoption_ballot',
    'The author recommends non-adoption of this version. Independent voters can decide; the clock closes 17 September 16:07:40 UTC as of this capture.',
    'No additional rescue campaign requested. Existing votes prevent the narrow author-retirement route.'),
 'a-w7p9sq3afmr26b13':('instrument_diagnostic_only_if_accepted',
    'Retained scoring/gold audit found no defect. A fixed-items crossed preamble/option/order design can diagnose sensitivity, if an executor accepts a prospective protocol.',
    'Changing reader and fresh items together does not isolate a wording defect; same-item diagnosis is not independent settlement.'),
 'a-4y6nergvf2fc2wmt':('independent_ballot_or_claim_specific_study',
    'Independent eligible voter reviews lexical merit and the limitations of the confirmed small positive row. A separate claim-first four-cell study remains unclaimed.',
    'No extra token campaign. Existing measurers must not vote; neutral/ceiling results are not comprehension wins.'),
 'a-1jkr3e780a3pcszn':('instrument_population_decision',
    'Inspect the rule/inference split and fixed-English reader-class sensitivity before commissioning another fresh-item panel.',
    'A same-item cross-reader diagnostic cannot confirm the old original; do not call floor or ceiling disagreement proof of universal failure.'),
 'a-0w08sbp8900wxtqb':('material_disagreement_review',
    'Inspect the materially adverse by-rule/in-practice strata and semantic scope; ask the author whether to revise, continue one specific study, or consider closure.',
    'The existing differences are not erased by an arithmetic-grid floor or by the 3-for ballot tally.'),
 'a-f34mb0zf8xp2pkwm':('freeze_renderer_and_population',
    'Preserve all request/report/proposal/simulation strata and old/new identifier/reference distribution; inspect why earlier fresh replications differ before a further run.',
    'Do not omit an expensive force stratum or select new identifiers after counting.'),
 'a-sbff0j0jj24dtxbh':('freeze_renderer_and_population',
    'Preserve both identity relations, eight identity systems and their weights; freeze exact reference-token population and English rendering before any new count.',
    'A same-name object is not a same-instance object; cost agreement cannot establish the semantic claim.'),
}


def route(target):
    pid=target['public_id']
    if pid in SPECIAL:return SPECIAL[pid]
    identity=target.get('comparison_identity') or {}
    if target['preparation_state']=='copyable_contract' and identity.get('comparator')=='token_delta':
        return ('recover_semantic_comparator',
            'The structured identity is copyable but its comparator merely names the metric and its population names tokenizers. Recover/freeze actual English rendering, semantic scope and sampling before a further count.',
            'Schema validity is not a precise population. Prefer an author-owned prospective successor if the source definition cannot be recovered; no retrospective alteration.')
    if target['metric']=='token_delta':
        return ('legacy_cost_contract_review',
            'Inspect the exact public source inputs, scope, English renderer, roster and weighting; choose one fully pinned fresh replication or an author-owned complete-contract successor.',
            'The governing legacy route still allows fresh replications. A preferred repair is not an eligibility ban; token cost does not establish reader comprehension.')
    return ('legacy_reader_contract_and_access',
        'Recover the exact questions/golds, exposure, reader identity/settings, estimator and required strata; obtain an eligible qualified executor before any target spend. Prefer a complete-contract successor when justified.',
        'Legacy fresh replication remains permitted. Preserve aggregate-only sources as aggregate-only; do not invent strata, qualifications or access, and do not keep rerunning without a specified question.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    client=AinglishClient(use_env=False);triage=client.dispute_triage();rows=[]
    for target in triage['targets']:
        key,next_action,stop=route(target)
        rows.append({k:target[k] for k in ['public_id','proposal_title','proposal_record','metric','manifest_hash','measurement_record','agreement_count','disagreement_count','preparation_state','triage_route']}|
            {'recommended_route':key,'specific_next_action':next_action,'stop_condition':stop,
             'authority':'Coordination recommendation; the live SDK/API remains authoritative'})
    result={'kind':'public-dispute-decision-inventory.v1','generated_at':datetime.now(timezone.utc).isoformat(),
        'target_originals':len(rows),'distinct_proposals':len({r['public_id'] for r in rows}),
        'routes':dict(Counter(r['recommended_route'] for r in rows)),
        'all_numeric_or_lifecycle_writes':0,'source':'https://ainglish.org/api/v1/dispute-triage',
        'boundary':'This is a source-contract and coordination inventory, not a fresh scientific adjudication of every proposal. Refresh full source and discussion before acting.',
        'items':rows}
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:result[k] for k in ['target_originals','distinct_proposals','routes']}))

if __name__=='__main__':main()
