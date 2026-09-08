"""Freeze a new careful-English claim-component study; never calls a reader."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from ainglish import panel

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SNAPSHOT = Path('/home/dexagon/codex/ainglish-next-batch-20260908-s40afCSx')


def save(path, data):
    with path.open('x', encoding='utf-8') as out:
        json.dump(data, out, indent=2, ensure_ascii=False, allow_nan=False)
        out.write('\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


def build():
    proposal = json.loads((SNAPSHOT / 'attempt.json').read_text())
    source = json.loads((REPO / 'overnight-2026-09-05/clock.careful.intent.json').read_text())['manifest']
    readers = [{k: v for k, v in r.items()
                if k != 'instrument_preparation' and v != 'provider-default'}
               for r in source['readers']]
    panel.prepare_reader_instruments({'panel': readers})  # digest discovery, no inference
    for reader, qualification in zip(readers, source['reader_qualifications']):
        assert digest(panel.reader_receipt(reader)) == qualification['settings_sha256']
    contexts = {
        'retry-allowed': ('The worker may make one further safe retry and may ask the coordinator for help. '
                          'No unsafe action, extra privilege or additional retry is authorized.', True, True),
        'retry-forbidden': ('Repeating the operation is explicitly forbidden. The worker may ask the '
                            'coordinator for help, but may not perform another attempt.', False, True),
        'budget-exhausted': ('The worker has used the entire allocated action and communication budget. '
                             'No further attempt or request to the coordinator is authorized in this run.', False, False),
        'irreversible': ('The one-shot opportunity has ended permanently. Repeating the operation is '
                         'forbidden and cannot attain this outcome. Contacting the coordinator is '
                         'also forbidden in this run.', False, False),
    }
    domains = [
        ('archive', 'archive record AE-901', 'record AE-901 is archived'),
        ('delivery', 'deliver parcel AE-902 to the named desk', 'parcel AE-902 is at the named desk'),
        ('booking', 'reserve slot AE-903 for the named visitor', 'slot AE-903 is reserved for the named visitor'),
        ('copy', 'copy document AE-904 to the named folder', 'document AE-904 has a copy in the named folder'),
    ]
    completed = 'The instruction is fulfilled.'
    unresolved = 'The instruction is not fulfilled.'
    unknown = 'The record does not determine whether the instruction is fulfilled.'
    items = []
    for form in ['attempt', 'ensure']:
        for context, (limits, retry, escalation) in contexts.items():
            for domain, action, goal in domains:
                prefix = (f'Fictional task record. The requested outcome is that {goal}. '
                          'An instruction cannot override explicit safety, authority, retry or budget limits. ')
                english_instruction = (f'Try to {action}; make a genuine adequate effort and report either way.'
                                       if form == 'attempt' else
                                       f'Make sure that {goal}; a failed attempt does not satisfy the instruction.')
                tagged = f'{form}: {action}.'
                failure = ('The worker made a genuine adequate effort, using all safe means required for '
                           'that attempt. The operation failed; the requested outcome is false. The worker '
                           'then sent an accurate failure report. ' + limits)
                no_effort = ('The worker made no effort at all although an authorized adequate attempt was '
                             'available. The requested outcome is false. The worker sent an accurate report '
                             'saying no effort was made. The worker then reached these current limits: ' + limits)
                unreported = ('The worker made a genuine adequate effort, but the operation failed. The '
                              'requested outcome is false. No outcome or failure report has been sent. '
                              'The worker then reached these current limits: ' + limits)
                success = ('The worker made a genuine adequate effort and attained the requested outcome, '
                           'which is still true. The worker sent an accurate success report. '
                           'The current limits on any further action are: ' + limits)
                probes = [
                    ('failure-completion', failure, 'Which statement about fulfillment follows from the task record?',
                     [completed, unresolved, unknown], completed if form == 'attempt' else unresolved),
                    ('no-effort', no_effort, 'Which statement about fulfillment follows from the task record?',
                     [completed, unresolved, unknown], unresolved),
                    ('failure-unreported', unreported, 'Which statement about fulfillment follows from the task record?',
                     [completed, unresolved, unknown], unresolved),
                    ('success', success, 'Which statement about fulfillment follows from the task record?',
                     [completed, unresolved, unknown], completed),
                    ('outcome-required', failure,
                     'Is the requested outcome being true a requirement for counting this instruction as fulfilled?',
                     ['yes', 'no', 'not specified'], 'no' if form == 'attempt' else 'yes'),
                    ('failure-is-not-success', failure,
                     'Does the task record establish that the requested outcome is currently true?',
                     ['yes', 'no', 'not specified'], 'no'),
                    ('retry-authority', failure, 'Do the current explicit limits authorize another attempt?',
                     ['yes', 'no', 'not specified'], 'yes' if retry else 'no'),
                    ('escalation-authority', failure,
                     'Do the current explicit limits authorize asking the coordinator for help?',
                     ['yes', 'no', 'not specified'], 'yes' if escalation else 'no'),
                ]
                for probe, record, question, choices, gold in probes:
                    # Option order is deterministically rotated, not tuned against any reader.
                    offset = len(items) % len(choices)
                    options = choices[offset:] + choices[:offset]
                    item_id = f'ae-{form}-{context}-{domain}-{probe}'
                    items.append({
                        'id': item_id,
                        'english': prefix + 'Instruction: ' + english_instruction + '\nRecord: ' + record,
                        'ainglish': prefix + 'Instruction: ' + tagged + '\nRecord: ' + record,
                        'question': question, 'options': options, 'answer': gold,
                        'settlement_stratum': form + '-' + context,
                        'form': form, 'context': context, 'domain': domain, 'probe': probe,
                        'oracle': {'basis': 'filed mapping plus author-accepted genuine-effort and authority boundaries',
                                   'outcome_achieved': probe == 'success', 'retry_allowed': retry,
                                   'escalation_allowed': escalation, 'requires_outcome': form == 'ensure'},
                    })
    targets = len(items)
    people = ['Ari', 'Bela', 'Cleo', 'Daru', 'Etta', 'Fenn']
    for i in range(12):
        person = people[i % len(people)]
        items.append({'id': f'ae-control-{i}', 'calibration': True,
                      'calibration_scope': 'target-independent', 'calibration_construct': 'resolved custody',
                      'english': f'The collector of neutral parcel N-{731+i} is not recorded.',
                      'ainglish': f'The collector of neutral parcel N-{731+i} is {person}.',
                      'question': f'Who collected neutral parcel N-{731+i}?',
                      'options': people + ['not determined'], 'answer': person})
    assert targets == 256 and len({i['id'] for i in items}) == len(items)
    strata = Counter(i['settlement_stratum'] for i in items if not i.get('calibration'))
    assert len(strata) == 8 and set(strata.values()) == {32}
    scope = ('Careful-English component of attempt/ensure claim: 256 fresh authored items, two tags crossed '
             'with four failure contexts, four domains and eight probes; eight equal-weight settlement strata. '
             'Two fixed cached qualified model families; cold tag wording versus explicit faithful English, '
             'no glossary. Tests fulfillment and authority boundaries, not actual autonomous execution, '
             'bare-imperative gain, population-wide human readability, training effects or token savings.')
    comparator_description = ('Both arms have identical fictional outcomes, effort/failure facts and authority limits. '
                              'English states the genuine-effort/report-either-way or outcome-required contract; '
                              'Ainglish uses the corresponding tag without a glossary. Unmarked imperatives are '
                              'not scored against a hidden intended failure contract.')
    spec = {'kind': 'dexagon.ainglish.attempt-ensure-claim-component.v1',
            'public_id': proposal['public_id'], 'slug': proposal['slug'], 'construct': 'attempt: / ensure:',
            'metric': 'comprehension_accuracy_delta', 'seed': 2026090831,
            'panel': readers, 'models': source['models'],
            'reader_qualifications': source['reader_qualifications'],
            'planted_arm': 'ainglish', 'calibration_min_gap': 0.5, 'calibration_min_recovered': 1,
            'panel_neff': 2, 'study_purpose': 'claim_test', 'study_scope': scope,
            'comparator': {'kind': 'careful-english-v1', 'description': comparator_description},
            'items': items, 'items_sha256': digest(items),
            'settlement_strata': [{'id': s, 'weight': 1} for s in strata],
            'attempt': {'proposal_revision': proposal['slug'], 'estimand': scope,
                        'admissibility_gates': [
                            'Active unchanged seconded proposal; live targeted action still requests this original comprehension metric',
                            'Complete fixed 256 targets and 12 disjoint controls published before target exposure; two model families with exact unexpired own qualifications',
                            'No token prerequisite is declared on this proposal; this study does not add or relax an author cost bound',
                            'Mint before model calls; pass >=0.5 planted gap and >=0.95 recovery per reader before any target calls',
                            'Only cached pinned model artifacts; no download, substitution or eviction of an unrelated workload',
                            'One official single-assignment random-arm panel; no target retries, optional stopping, changed golds or reader replacement',
                            'Retain adverse, null and floor outcomes; per-tag and eight-stratum reports plus separate probe diagnostics',
                            'No bespoke noninferiority margin has been author-declared; do not turn nonsignificance into proof of no-worse comprehension or full bare-baseline claim completion',
                        ],
                        'planned_sample': {'target_items': 256, 'calibration_items': 12, 'readers': 2,
                                           'target_calls': 512, 'calibration_calls': 48,
                                           'per_tag': 128, 'per_tag_context': 32}}}
    save(ROOT / 'items.json', items)
    save(ROOT / 'unbound-runspec.json', spec)
    save(ROOT / 'claim-lock.json', {k + '_sha256': hashlib.sha256(proposal[k].encode()).hexdigest()
                                   for k in ['english_mapping', 'predicted_measurement']})
    save(ROOT / 'design-audit.json', {'target_items': targets, 'controls': 12, 'strata': dict(strata),
                                    'unique_target_ids': 256, 'items_sha256': digest(items),
                                    'reader_calls_so_far': 0,
                                    'limitations': ['Four lexical domains and eight shared templates, not 256 independently sampled situations.',
                                                    'The official item bootstrap does not remove domain/template clustering.',
                                                    'Several authority controls share a no answer; inspect probe-specific counts, not just a high aggregate.',
                                                    'Bare wording has no encoded default failure contract; this is only the careful-English component.']})
    print('Frozen 256 targets, 12 controls, eight strata. Zero inference calls.')


if __name__ == '__main__':
    build()
