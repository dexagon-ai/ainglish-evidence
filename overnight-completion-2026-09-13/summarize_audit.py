"""Render bounded public source/contract audits. No inference, live state change or verdict."""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SELF = '52b1883a-464e-403c-9059-d57afe91a13c'
# Editorial classification of the reviewed published predictions, not a parser or new rule.
CAREFUL_PRIMARY = {
    'a-5p0ywh1y1ec555wc', 'a-ppyzdf5qk6z67aty', 'a-1jkr3e780a3pcszn',
    'a-1v2tfbyk5zc0g40w', 'a-f34mb0zf8xp2pkwm', 'a-v7argdk2hebtextg',
    'a-3fmyebhemzm02fds', 'a-2tme3vb0embtpd8y', 'a-b4mw22e4g8tv0hqv',
    'a-ys608z0vv63gpc3y',
}


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def text_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def main():
    snapshot = json.loads((ROOT / 'public-snapshot.json').read_text())
    sources = json.loads((ROOT / 'source-audit.json').read_text())
    inputs = {row['public_id']: row for row in json.loads((ROOT / 'contract-inputs.json').read_text())['rows']}
    warnings = snapshot['evidence_contract_audit']['success_criteria_reviews']
    assert len(warnings) == len({w['public_id'] for w in warnings}) == 32
    contracts = []
    for warning in warnings:
        p = inputs[warning['public_id']]
        carrier = p['evidence_contract']['claim_carrier']
        assert 'comprehension_accuracy_delta' in carrier
        notices = p.get('author_work_notices', {})
        notice = notices.get('active')
        contracts.append({
            'public_id': p['public_id'], 'title': p['title'], 'author': p['proposer']['name'],
            'stage': p['stage'], 'evidence_contract': p['evidence_contract'],
            'prediction_excerpt': warning['evidence_sentences'],
            'comparison_plan_review': 'careful-English primary; bare wording descriptive'
                if p['public_id'] in CAREFUL_PRIMARY else 'separate bare-word benefit and careful-English preservation questions',
            'author_notice': notice,
            'next_action': 'Author and reviewers must name the carrier comparator and its success criterion. Preserve every promised safety/benefit obligation; use prospective governance for any rule change, not a retrospective pass.',
            'changes_readiness': False,
        })
    save('contract-dispositions.json', {'snapshot_at': snapshot['captured_at'],
        'count': len(contracts), 'rows': contracts,
        'boundary': 'Contract/excerpt review, not full scientific certification of 32 proposals. No amendment or automatic rejection.'})
    lines = ['# Thirty-two contract warnings: decisions, not automatic failures', '',
        'The live audit snapshot names 32 noninferiority/superiority alignment reviews and',
        'zero contradictions under its narrow automatic rule. All 32 have an unbounded',
        'comprehension carrier. That currently requires positive support relative to zero;',
        'the quoted predictions also allow small careful-English losses. An inconclusive',
        'difference proves neither superiority nor noninferiority.', '',
        'Ten reviewed plans explicitly make careful English the primary comparator and',
        'keep bare ambiguity descriptive. The other 22 combine a bare-word benefit question',
        'with a separate careful-English preservation question. These are editorial groups',
        'for review, not an automatic classifier or new eligibility rule. Some comparisons',
        'still need a more explicit estimand; a true unknown must not be scored as an error.', '',
        'A new replication cannot repair an unresolved definition of success. Name the',
        'comparator, exposure, margin, uncertainty method, per-form requirements and',
        'separate benefit before spending. Retain all existing adverse/null results and',
        'the present comprehension-harm veto. Future Ainglish training may alter performance',
        'but is a research hypothesis, not observed evidence or a reason to erase current costs.', '',
        '| Proposal | Author | Comparator decision to preserve |', '| --- | --- | --- |']
    for row in contracts:
        lines.append(f"| [{text_cell(row['title'])}](https://ainglish.org/proposals/{row['public_id']}) | {row['author']} | {row['comparison_plan_review']} |")
    lines += ['', 'The [machine-readable rows](contract-dispositions.json) retain the exact quoted',
        'sentences, structured contracts and captured author notices. Existing public holds',
        'on replied-no and time-total still matter. Same-one has an additional public author',
        'no-run decision in its discussion; absence of a structured notice is not consent.', '',
        'The [comparator v2 review](COMPARATOR-V2-REVIEW.md) gives exact remaining wording',
        'conflicts and possible repairs. No draft has been treated as ratified. For a',
        'careful-English preservation claim, choose prospectively between a justified',
        'noninferiority-plus-separate-benefit route and an honestly revised superiority',
        'claim. Do not silently switch an already exposed study between these questions.']
    (ROOT / 'CONTRACT-REVIEW.md').write_text('\n'.join(lines) + '\n')

    dispositions = []
    for row in sources['rows']:
        recount = row.get('token_recount')
        reader = row['metric'] in {'comprehension_accuracy_delta', 'robustness_delta'}
        own = row['source_submitter_sub'] == SELF
        if recount and recount.get('status') == 'recounted_retained_pairs' and not recount['equal_within_0_0005_tokens']:
            route = 'existing_result_correction_needs_available_independent_reviewer'
        elif row.get('structural_audit') is None:
            route = 'recover_exact_retained_bank_before_scientific_review'
        elif reader and own:
            route = 'another_principal_required_to_replicate_own_original'
        elif reader:
            route = 'source_reader_roster_not_available_on_this_host'
        else:
            route = 'arithmetic_reproduces_semantic_and_replication_contract_review_still_needed'
        dispositions.append({k: row[k] for k in ['proposal_public_id', 'title',
            'source_manifest_hash', 'source_attempt_id', 'source_author', 'source_submitter_sub',
            'metric', 'value', 'readers']} | {'diagnostic_next_route': route,
            'role_boundary': 'No current independent eligibility is inferred from this snapshot.',
            'bank_status': row.get('bank', {}).get('source', row.get('audit_error_type'))})
    save('source-dispositions.json', {'snapshot_at': sources['at'], 'count': len(dispositions),
        'by_route': dict(Counter(r['diagnostic_next_route'] for r in dispositions)), 'rows': dispositions,
        'boundary': 'Source triage only. Reader availability is local, not a claim that nobody can measure. No substitute readers or self-confirmation.'})
    print(json.dumps({'contract_rows': len(contracts), 'source_rows': len(dispositions),
                      'source_routes': dict(Counter(r['diagnostic_next_route'] for r in dispositions))}))


if __name__ == '__main__':
    main()
