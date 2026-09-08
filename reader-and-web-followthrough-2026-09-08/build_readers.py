"""Prospective reader instruments; no target calls, mint, or tokenizer loading."""
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
from ainglish import panel, experiment_audit

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SNAPSHOT = Path('/home/dexagon/codex/ainglish-batch-20260908-ozDzOA')

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')

def freeze(name, target, items, scope, purpose, comparator, seed, extra_gates):
    p = json.loads((SNAPSHOT / (target + '.proposal.json')).read_text())
    readers, qualifications = [], []
    for reader_name in ['mistral', 'gemma']:
        q = json.loads((ROOT / 'qualification' / (reader_name + '.result.json')).read_text())
        assert q['status'] == 'passed'
        readers.append(json.loads((ROOT / 'qualification' / (reader_name + '.screen.json')).read_text())['reader'])
        qualifications.append(q['receipt'])
    panel.prepare_reader_instruments({'panel': readers})
    for reader, q in zip(readers, qualifications):
        assert digest(panel.reader_receipt(reader)) == q['settings_sha256']
    target_count = len(items)
    strata = Counter(x['settlement_stratum'] for x in items)
    assert len(set(x['id'] for x in items)) == target_count
    people = ['Ari', 'Bela', 'Cleo', 'Daru', 'Etta', 'Fenn']
    for i in range(12):
        person = people[i % len(people)]
        items.append({'id': name + '-control-' + str(i), 'calibration': True,
                      'calibration_scope': 'target-independent', 'calibration_construct': 'resolved custody',
                      'english': f'Neutral receipt Z-{910+i}: the collector is not recorded.',
                      'ainglish': f'Neutral receipt Z-{910+i}: the collector is {person}.',
                      'question': f'Who collected the parcel on receipt Z-{910+i}?',
                      'options': people + ['not determined'], 'answer': person})
    spec = {'public_id': p['public_id'], 'slug': p['slug'], 'construct': p['form'],
            'metric': 'comprehension_accuracy_delta', 'seed': seed, 'panel': readers,
            'models': [q['roster_id'] for q in qualifications], 'reader_qualifications': qualifications,
            'planted_arm': 'ainglish', 'calibration_min_gap': 0.5, 'calibration_min_recovered': 1,
            'panel_neff': 2, 'study_purpose': purpose, 'study_scope': scope,
            'comparator': comparator, 'items': items, 'items_sha256': digest(items),
            'settlement_strata': [{'id': s, 'weight': 1} for s in strata],
            'attempt': {'proposal_revision': p['slug'], 'estimand': scope,
                        'admissibility_gates': [
                            'Active unchanged proposal and current exact-target measurement eligibility; no superseding claim',
                            'All target items, exact golds, common definitions, comparator and analysis frozen publicly before mint and inference',
                            'Two exact cached model artifacts and unexpired endpoint/settings qualifications; no downloads or substitutions',
                            'Our isolated service is restricted to GPU 0; no eviction of unrelated workloads; physical host disk remains above 15 GiB',
                            'Mint before experiment calls; pass the official calibration gate before targets; no target retries or result-dependent stopping',
                            'Retain null, adverse, transport and floor results with exact per-cell journals; no claim of independent confirmation',
                        ] + extra_gates,
                        'planned_sample': {'target_items': target_count, 'calibration_items': 12,
                                           'readers': 2, 'target_calls': target_count * 2,
                                           'calibration_calls': 48, 'strata': dict(strata)}}}
    save(ROOT / name / 'items.json', items)
    save(ROOT / name / 'unbound-runspec.json', spec)
    save(ROOT / name / 'claim-lock.json', {k + '_sha256': hashlib.sha256(p[k].encode()).hexdigest()
                                          for k in ['english_mapping', 'predicted_measurement']})
    save(ROOT / name / 'design-audit.json', {'targets': target_count, 'controls': 12, 'strata': dict(strata),
                                           'items_sha256': digest(items), 'target_calls_so_far': 0,
                                           'limit': 'Authored crossed template grid, not an independent natural-use or human sample.'})
    print(name, target_count, 'targets frozen, no inference', flush=True)

def attempt():
    items = []
    domains = [('archive', 'archive record ND-1101', 'record ND-1101 is archived'),
               ('deliver', 'deliver parcel ND-1102', 'parcel ND-1102 has been delivered'),
               ('reserve', 'reserve slot ND-1103', 'slot ND-1103 is reserved'),
               ('copy', 'copy document ND-1104', 'document ND-1104 has been copied')]
    cases = {
        'failure-reported': (True, False, True), 'success-reported': (True, True, True),
        'failure-unreported': (True, False, False), 'success-unreported': (True, True, False),
        'no-effort-failure': (False, False, True), 'no-effort-success': (False, True, True),
    }
    opts = [f'Obligations discharged: {a}; world outcome attained: {b}.' for a,b in product(['yes', 'no'], repeat=2)]
    for form, exposure, framing, (domain, action, goal), (case, (effort, success, reported)) in product(
            ['attempt', 'ensure'], ['mapping', 'discharge-explicit'], ['neutral', 'outcome-salient'], domains, cases.items()):
        common = ('Read this fictional instruction and record. Shared definitions: attempt: asks for a genuine '
                  'adequate effort and an accurate report either way. ensure: requires the specified outcome to '
                  'be attained; a failed try is insufficient. Neither authorizes ignoring safety, authority, '
                  'retry or budget limits. The completed record below lists all required effort and reporting facts. ')
        if exposure == 'discharge-explicit':
            common += ('Discharge rule: for attempt:, adequate effort plus its accurate report completes the '
                       'obligation even if the world outcome is false. For ensure:, the world outcome must be '
                       'true; mere effort is insufficient. Attaining an outcome and discharging an obligation '
                       'are separate questions. ')
        common += (f'The requested world outcome is that {goal}. ' if framing == 'outcome-salient'
                   else f'This record concerns the instruction to {action}. ')
        english = (f'Try to {action}; make a genuine adequate effort and report either way.' if form == 'attempt'
                   else f'Make sure that {goal}; a failed attempt does not satisfy the instruction.')
        record = (' The worker made a genuine adequate effort using all safe means required for this instruction.' if effort
                  else ' The worker made no effort, although an authorized adequate attempt was available.')
        record += (f' The world outcome is now true: {goal}.' if success else f' The world outcome is false: it is not true that {goal}.')
        record += (' An accurate report of the effort and outcome was sent.' if reported else ' No report has been sent.')
        record += ' No further action is authorized in this completed run. Outcome truth is not permission to act.'
        discharged = effort and reported if form == 'attempt' else success
        answer = f'Obligations discharged: {"yes" if discharged else "no"}; world outcome attained: {"yes" if success else "no"}.'
        offset = len(items) % 4
        items.append({'id': f'nd-{form}-{exposure}-{framing}-{domain}-{case}',
                      'english': common + 'Instruction: ' + english + record,
                      'ainglish': common + f'Instruction: {form}: {action}.' + record,
                      'question': 'What does the record establish about discharge of this instruction’s obligations and attainment of its world outcome?',
                      'options': opts[offset:] + opts[:offset], 'answer': answer,
                      'settlement_stratum': form + '-' + exposure + '-' + framing,
                      'form': form, 'exposure': exposure, 'framing': framing, 'domain': domain, 'boundary': case,
                      'oracle': {'adequate_effort': effort, 'world_success': success, 'report_sent': reported,
                                 'obligations_discharged': discharged}})
    assert len(items) == 192
    freeze('attempt-discharge', 'attempt-ensure', items,
           'Prospective diagnostic: 192 authored cases crossing attempt/ensure, shared mapping versus explicit discharge explanation, neutral versus outcome-salient framing, four domains and six effort/outcome/report cases. Two fixed cached qualified reader families, 384 target calls. Both arms receive identical definitions and records. Tests obligation discharge separately from world-outcome truth; not a cold-reading replication, original-result correction, execution success study or human validation. Prior 0/12 Ainglish and 0/20 English failure-completion findings remain unchanged.',
           'diagnostic', {'kind': 'careful-english-shared-definition-v1',
                          'description': 'Faithful English versus tagged instruction with identical common definitions, effort, outcome, reporting and authority facts; definitions crossed prospectively, never taught only to one arm.'},
           2026090881, ['Report every form/exposure/framing cell and boundary; framing and instruction ambiguity are competing hypotheses, not already established causes',
                       'No bespoke noninferiority threshold or favourable adoption conclusion is inferred from this diagnostic'])

def outcome():
    definition = ('Shared definition supplied once for this stateless question: x is mean-outcome(D) asserts '
                  'that x equals the probability-weighted arithmetic mean under D. x is likeliest-outcome(D) '
                  'asserts that x has the highest aggregated outcome mass under D, with ties allowed. '
                  'These definitions also govern the corresponding English phrases. They do not guarantee a '
                  'trial result or certify the model. ')
    for name in ['outcome-careful', 'outcome-compact']:
        old = json.loads((REPO / 'night-progression-2026-09-07/full-claim' / name / 'items.json').read_text())
        items = old['items'] if isinstance(old, dict) else old
        for item in items:
            item['id'] = name + '-' + item['id']
            for arm in ['english', 'ainglish']:
                item[arm] = definition + item[arm]
        freeze(name, 'outcome', items,
               'Outcome-statistic claim component: 240 authored paired cases, 120 per predicate, six domains, five boundaries, exact rational golds, shared one-time definition exposure in each stateless cell. Two cached qualified reader families, 480 target calls. ' +
               ('Compact technical-English sensitivity comparator' if name.endswith('compact') else 'Careful-English primary comparator') +
               '. Worlds are shared across the two contrasts, not independent replications. Report every predicate, boundary, domain and reader, item-bootstrap uncertainty and critical false-guarantee responses. Majority-probability and unsupported-model probes are separate diagnostics; the whole claim is not complete without them.',
               'claim_test', {'kind': name + '-shared-definition-v1', 'description': 'Exactly shared common definitions, distribution, units, version, conditioning and tie rules; only the statistic expression differs.'},
               2026090882 if name.endswith('careful') else 2026090883,
               ['Both frozen cost originals d9bc25ff and 35874bf6 remain independently confirmed and all per-form/tokenizer/comparator means are within +6',
                'Bounded independent semantic review of the common definitions, golds and boundary questions is recorded publicly before target exposure',
                'Report >=90 percent accuracy and -3pp noninferiority separately per predicate and comparator; intervals crossing -3pp are inconclusive, not a pass; <85 percent and >10 percent critical false guarantees remain visible',
                'Even noninferiority is not evidence of a reader advantage, learnability benefit, future training effect or reason to prefer a longer spelling'])

if __name__ == '__main__':
    attempt()
    outcome()
