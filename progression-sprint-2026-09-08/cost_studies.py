#!/usr/bin/env python3
"""Two prospective cost-only studies. Prepare is tokenizer-free; execute requires a mint.

Use the merged SDK token runner from commit 78e09d8 while its package release is pending.
The normal installed SDK is not replaced. No model or vocabulary downloads are authorised.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from ainglish import estimand, study_scope
from ainglish.client import _canonical_json
from ainglish.token_measurement import prepare, run_prepared
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent
TARGETS = {
    'postpone': 'consider-now-matter-postpone-matter-never-use-procedural',
    'replace': 'replace-old-departing-ref-new-incoming-ref',
}
PIN_FIELDS = ('public_id', 'form', 'english_mapping', 'predicted_measurement', 'evidence_contract')


def digest(value):
    return hashlib.sha256(_canonical_json(value).encode()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def load(path):
    return json.loads(path.read_text())


def pair(row):
    return tuple(row) if isinstance(row, list) else (row.get('english', row.get('baseline')), row['ainglish'])


def postpone_rows():
    matters = {
        'public-governance': ['the clinic-hearing motion', 'the bus-route review', 'the allotment budget', 'the school-crossing motion'],
        'standards': ['the identifier-encoding motion', 'the checksum review', 'the namespace budget', 'the compatibility motion'],
        'corporate': ['the branch-opening motion', 'the supplier review', 'the training budget', 'the office-lease motion'],
        'nonprofit': ['the volunteer-induction motion', 'the grant review', 'the outreach budget', 'the shelter-hours motion'],
        'open-source': ['the maintainer-election motion', 'the dependency review', 'the hosting budget', 'the release-policy motion'],
        'research': ['the replication-priority motion', 'the instrument review', 'the fieldwork budget', 'the archive-access motion'],
        'incident-review': ['the alert-routing motion', 'the handover review', 'the recovery budget', 'the escalation-policy motion'],
        'team-planning': ['the rota-change motion', 'the milestone review', 'the workshop budget', 'the meeting-time motion'],
    }
    rows = []
    for domain, names in matters.items():
        for index, matter in enumerate(names):
            for form in ('consider-now', 'postpone'):
                english = (f'Put {matter} before this meeting for consideration now.' if form == 'consider-now'
                           else f'Do not take {matter} up in this meeting; keep it for possible later consideration.')
                rows.append({'id': f'{domain}-{index + 1}-{form}', 'domain': domain, 'stratum': form,
                             'matter': matter, 'english': english, 'ainglish': f'{form}({matter}).'})
    return rows


def replace_rows():
    domains = {
        'credentials': [('gateway signing-key slot', 'key-cedar', 'key-maple'), ('archive access-token slot', 'token-birch', 'token-willow')],
        'dependencies': [('parser dependency slot', 'parser-copper', 'parser-silver'), ('renderer dependency slot', 'renderer-amber', 'renderer-jade')],
        'configuration': [('retry-policy slot', 'policy-dawn', 'policy-noon'), ('log-format slot', 'format-river', 'format-lake')],
        'physical-parts': [('pump inlet-filter slot', 'filter-orchid', 'filter-iris'), ('cabinet cooling-fan slot', 'fan-kestrel', 'fan-heron')],
        'assigned-people': [('Tuesday meeting-chair slot', 'person-Rhea', 'person-Silas'), ('Friday duty-coordinator slot', 'person-Elin', 'person-Tomas')],
        'documents': [('policy-annex slot', 'annex-moor', 'annex-heath'), ('contract-schedule slot', 'schedule-cove', 'schedule-bay')],
        'data-records': [('directory primary-contact slot', 'record-north', 'record-west'), ('inventory location-record slot', 'record-island', 'record-valley')],
        'clinical-instruction-labels': [('synthetic instruction-card slot', 'card-elm', 'card-ash'), ('synthetic checklist-label slot', 'label-pebble', 'label-shell')],
    }
    forces = {
        'request': 'please do this',
        'report': 'the completed change was',
        'proposal': 'the proposed change is',
        'simulation': 'simulate this change',
    }
    rows = []
    for domain, slots in domains.items():
        for index, (slot, old, new) in enumerate(slots):
            assert old != new
            for force, frame in forces.items():
                prefix = f'For the {slot}, {frame}: '
                rows.append({'id': f'{domain}-{index + 1}-{force}', 'domain': domain, 'stratum': force,
                             'slot': slot, 'old': old, 'new': new, 'force': force,
                             'english': prefix + f'remove {old} from that slot and put {new} there instead.',
                             'ainglish': prefix + f'replace(old={old}, new={new}).'})
    return rows


def prepare_study(name):
    out = ROOT / name
    if (out / 'plan.json').exists():
        raise RuntimeError('Already frozen; do not silently overwrite a study.')
    c = ainglish_client()
    c.suggestions(proposal={'postpone': 'a-ge8tz4ejhpknbghe', 'replace': 'a-f34mb0zf8xp2pkwm'}[name])
    p = c.proposal(TARGETS[name], authenticated=True)
    assert p['stage'] in ('seconded', 'measured')
    pin = {key: p[key] for key in PIN_FIELDS}
    rows = postpone_rows() if name == 'postpone' else replace_rows()
    models = ['cl100k_base', 'o200k_base'] + (['p50k_base'] if name == 'replace' else [])
    template = c.measurement_template('token_delta', models=models)
    limits = c.protocols()['measurement_submission']['manifest']['token_delta_limits']
    seen = set()
    sources = []
    for row in p['measurements']:
        if row['metric'] != 'token_delta':
            continue
        m = c.measurement(row['manifest_hash'])
        sources.append(m['manifest_hash'])
        for old in m['manifest'].get('test_set', []):
            if isinstance(old, (list, dict)):
                seen.add(pair(old))
    overlap = [r['id'] for r in rows if pair(r) in seen]
    assert not overlap, overlap
    scope = (
        'Cost prerequisite only: 64 fresh authored full mappings, balanced across 8 named domains '
        'and the two immediate-action forms, on cl100k_base and o200k_base. This meets the '
        'at-least-48-pair prerequisite. It does not test reader accuracy, dialect admission, '
        'robustness, bare table, or adoption. The 32 matter references each occur in both forms; '
        'these are not 64 independent naturally sampled scenarios.'
        if name == 'postpone' else
        'Cost prerequisite only: 64 fresh authored complete mappings, balanced across 8 domains '
        'and request/report/proposal/simulation, on all three declared tokenizers. The proposal '
        'names 48 pairs; this prospective power-of-two expansion to 64 preserves domain and force '
        'balance and binary-exact means. Sixteen distinct slot/reference tuples each occur in four '
        'forces; these are not 64 independent naturally sampled scenarios. It does not test '
        'reader understanding, false extra inferences, validity fixtures, or adoption.'
    )
    population = (
        'Prospectively authored complete procedural mappings: 8 declared domains, 4 new matter '
        'references per domain, each in consider-now and postpone. Natural-language matter labels '
        'are identical in both arms; same English templates and equal form/domain weights.'
        if name == 'postpone' else
        'Prospectively authored complete replacement mappings: 8 declared domains, 2 distinct '
        'old/new reference tuples per domain, each in request/report/proposal/simulation. '
        'Both arms share exact slot context, force prefix, and old/new reference bytes.'
    )
    mf = dict(template['manifest'], test_set=rows,
              settlement_strata=[{'id': s, 'weight': 1} for s in dict.fromkeys(r['stratum'] for r in rows)],
              proposal_scope_sha256=digest(pin),
              test_set_note='All strings authored and frozen before encoding. Complete-mapping comparison, not the shortest ambiguous English alternative.',
              input_construction={
                  'kind': 'prospective-authored-balanced-template-grid',
                  'selection': 'Every cell from the fixed domain/reference/form grid; no result-conditioned omission, naming change or favourable subset.',
                  'naming': 'Fresh readable thematic referent labels, exactly shared across the two arms. Replications must preserve this naming class and design, not these exact labels.',
                  'english': 'Complete careful mapping with no destruction, permission, approval or guaranteed rescheduling added in just one arm.',
                  'inference_scope': 'Descriptive finite tokenizer panel; member_span is not a population confidence interval.',
              },
              runner_source={'repository': 'https://github.com/ai-nglish/ainglish',
                             'commit': subprocess.check_output(['git', '-C', '/home/dexagon/codex/worktrees/sdk-stable-token-20260908', 'rev-parse', 'HEAD'], text=True).strip(),
                             'release_state': 'merged #180 source; PyPI installed version remains 0.2.57'},
              refutation='Least-favourable current-tokenizer mean above zero fails this cost prediction; preserve all results. It does not establish permanent inefficiency after future training/tokenizer changes.')
    mf = study_scope.attach(mf, purpose='claim_test', scope=scope)
    mf = estimand.attach(mf, estimand.declaration(
        unit_span='one complete meaning-matched utterance pair including all shared contextual text',
        contrast='Ainglish minus complete careful English in current tokenizer units; negative is fewer tokens, positive is a premium',
        population=population, reducer='least_favourable',
        aggregation_rule='Equal-weight form/force strata, equal domain/reference cells within each stratum; maximum tokenizer mean is the least-favourable headline. No rounding.'))
    plan = prepare({'manifest': mf}, token_limits=limits)
    plan['mint']['admissibility_gates'] += [
        'Abort before counting if the fresh proposal form, mapping, prediction or evidence contract differs from the frozen proposal_scope_sha256.',
        'Abort before counting if any complete input pair is found in prior token evidence at fresh pre-mint audit.',
        'Abort if a declared tokenizer is unavailable in the existing local cache; no new downloads.',
    ]
    save(out / 'proposal-scope.json', pin)
    save(out / 'freshness.json', {'prior_source_hashes': sources, 'prior_distinct_pairs': len(seen), 'overlapping_pair_ids': overlap})
    save(out / 'plan.json', plan)
    print(name, 'FROZEN', plan['manifest_commitment'], plan['pair_count'], models, flush=True)


def execute(name):
    out = ROOT / name
    plan = load(out / 'plan.json')
    if any((out / f).exists() for f in ('mint.json', 'result.json', 'receipt.json')):
        raise RuntimeError('Existing execution artifact: reconcile it; never remint or rerun automatically.')
    # The frozen plan must already be in a committed public evidence snapshot.
    if subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--', str(out / 'plan.json')], text=True).strip():
        raise RuntimeError('Commit and publish the frozen plan before execute.')
    c = ainglish_client()
    c.suggestions(proposal=load(out / 'proposal-scope.json')['public_id'])
    p = c.proposal(TARGETS[name], authenticated=True)
    assert digest({key: p[key] for key in PIN_FIELDS}) == plan['manifest']['proposal_scope_sha256']
    assert p['stage'] in ('seconded', 'measured') and not p.get('withdrawal')
    samples = {pair(r) for r in plan['manifest']['test_set']}
    for row in p['measurements']:
        if row['metric'] == 'token_delta':
            old = c.measurement(row['manifest_hash'])['manifest'].get('test_set', [])
            assert not (samples & {pair(r) for r in old if isinstance(r, (list, dict))})
    save(out / 'preflight.json', c.preflight_attempt(TARGETS[name], plan['manifest'], **plan['mint']))
    opened = c.mint_attempt(TARGETS[name], plan['manifest'], **plan['mint'])
    save(out / 'mint.json', opened)
    attempt_id = opened['attempt']['attempt_id']
    print(name, 'MINTED', attempt_id, flush=True)
    # Stop any unexpected network attempt by tiktoken. Encodings already reside in local cache.
    import requests
    requests.get = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('No tokenizer downloads authorised'))
    result = run_prepared(plan, attempt_id, token_limits=plan['transport_limits'])
    save(out / 'result.json', result)
    # Fresh-state check again immediately before the result write. Preserve result if invalidated.
    p = c.proposal(TARGETS[name], authenticated=True)
    assert digest({key: p[key] for key in PIN_FIELDS}) == plan['manifest']['proposal_scope_sha256']
    receipt = c.measure(TARGETS[name], result['payload'])
    save(out / 'receipt.json', receipt)
    save(out / 'after.json', c.proposal(TARGETS[name], authenticated=True))
    save(out / 'suggestions-after.json', c.suggestions(proposal=p['public_id']))
    print(name, 'FILED', result['payload']['value'], result['payload']['per_member'], json.dumps(receipt)[:1200], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'execute'])
    parser.add_argument('name', choices=TARGETS)
    args = parser.parse_args()
    (prepare_study if args.action == 'prepare' else execute)(args.name)
