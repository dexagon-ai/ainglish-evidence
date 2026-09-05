"""Freeze a matched cold/reference transfer design; no readers, counts or governance writes."""
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent / 'frozen-v2'

GUIDES = {
    'fact-choice': '''Brief reference (the same card is supplied with either wording):
fact-not-known means an answer is already fixed by facts or a governing criterion, but the speaker lacks the evidence needed to state it. Finding or calculating the relevant information can close that gap without a new authorised choice.
choice-not-made means no operative selection yet exists. Evidence can help, but a permitted chooser must select before an answer governs. A preference is not a selection. After a selection is operative but unread by the speaker, its content is fact-not-known, not choice-not-made.
Example outside the test domains: the gardener has chosen an orchard row but I have not read the note: fact-not-known. The gardener has not chosen a row: choice-not-made. These labels describe a state; neither requests action or gives the recipient authority. They do not cover every kind of uncertainty.
End of reference. Apply the definition to the new case below.''',
    'delegation': '''Brief reference (the same card is supplied with either wording):
no-delegation forbids assigning completion-bearing work to another principal. It does not forbid deterministic tools, advice or retrieving existing reports when the responsible principal still performs the assigned work.
one-hop-delegation-allowed permits one or many direct delegates, but none may pass the work onward. Hop means depth, not number of direct workers. The original responsible principal remains accountable to the issuer. A named group is level zero: sharing within that group is not a downstream hop.
Example outside the test domains: a musician may use a metronome under no-delegation. Under one-hop-delegation-allowed, two direct arrangers are allowed, but an arranger may not hire another arranger to do the assigned work. Neither qualifier expands permissions, authorises credential sharing or overrides an external prohibition.
End of reference. Apply the definition to the new case below.''',
}

def canonical(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

def save(name, data):
    with (ROOT / name).open('x') as f:
        json.dump(data, f, indent=2, ensure_ascii=False); f.write('\n')

def rotate(options, answer, position):
    shift = (options.index(answer) - position) % len(options)
    return options[shift:] + options[:shift]

def positions(size, choices, seed):
    result = [i % choices for i in range(size)]
    random.Random(seed).shuffle(result)
    return result

def controls(name):
    rows = []
    for i, (a, b) in enumerate([('Iven', 'Nola'), ('Sarin', 'Eda'), ('Orla', 'Kavi'), ('Tarin', 'Luma'),
                              ('Yara', 'Oren'), ('Bela', 'Faris'), ('Enna', 'Rafi'), ('Miro', 'Zena')]):
        ref = f'TR-{name}-{840+i}'
        rows.append({'id': f'{name}-control-{i}', 'calibration': True,
            'english': f'The sealed parcel {ref} is with either {a} or {b}.',
            'ainglish': f'The sealed parcel {ref} is with {a}, not {b}.',
            'question': f'Who has parcel {ref}?', 'answer': a,
            'options': rotate([a, b, 'the information does not determine who', 'neither person'], a, i % 4)})
    return rows

def fact_choice():
    domains = ['deployment region', 'payment destination', 'shift assignment', 'policy option',
               'procurement supplier', 'inventory allocation', 'analysis threshold', 'release date']
    contexts = [
        'Only the current operative answer matters here, not a prediction.',
        'One colleague has expressed a preference; a preference alone is not binding.',
        'A published finality rule distinguishes tentative progress from a governing outcome.',
        'Implementation is a separate task; this issue concerns the operative answer, not whether it was applied.',
        'Other participants may have information that the speaker does not have.',
        'Several earlier drafts exist. The issue concerns the current case, not a superseded draft.',
        'The issue is which option is excluded, rather than which option is favoured.',
        'This issue belongs to a named subtask; decisions about the parent task do not answer it.',
    ]
    rows = []
    deals = [positions(128, 6, 2026090550 + j) for j in range(2)]
    for i, (domain, context, authority) in enumerate(itertools.product(domains, contexts, ['human coordinator', 'authorised software agent'])):
        issue = (f'which {domain} is excluded for case F{9400+i}' if contexts.index(context) == 6
                 else f'which {domain} applies to case F{9400+i}')
        prefix = f'The {authority} is the relevant chooser. {context} The speaker reports one unresolved issue.\n'
        for j, form in enumerate(['fact-not-known', 'choice-not-made']):
            english = (f'For {issue}, a governing answer already exists, but I lack the evidence to state it; finding or calculating the relevant information can settle the gap without a new selection.'
                       if j == 0 else f'For {issue}, no operative selection has been made; information may help, but the authorised chooser must select to settle the gap.')
            existence = 'yes' if j == 0 else 'no'
            route = 'finding out' if j == 0 else 'an authorised chooser deciding'
            options = [f'1: {e}; 2: {r}' for e, r in [
                ('yes', 'finding out'), ('no', 'an authorised chooser deciding'),
                ('yes', 'an authorised chooser deciding'), ('no', 'finding out'),
                ('cannot tell', 'neither step'), ('cannot tell', 'finding out')]]
            answer = f'1: {existence}; 2: {route}'
            question = '1. Is there already a governing answer to discover? 2. Which next step closes the reported gap? Choose the complete pair.'
            rows.append({'id': f'fact-choice-{i:03}-{j}', 'english': prefix + english,
                'ainglish': prefix + form + ' — ' + issue + '.', 'question': question,
                'options': rotate(options, answer, deals[j][i]), 'answer': answer,
                'settlement_stratum': form, 'strata': {'form': form, 'domain': domain,
                    'context': contexts.index(context), 'authority': authority, 'frame_cluster': i}})
    return rows

def delegation():
    domains = ['review the database migration', 'audit the private-data export', 'check the research citations',
               'reconcile the invoice batch', 'inspect the equipment inventory', 'review the moderation queue',
               'prepare the publication bundle', 'check the access-policy change']
    operations = ['direct-one', 'direct-many', 'second-hop', 'deterministic-tool',
                  'advice', 'existing-report', 'inside-team', 'credential-sharing']
    rows = []
    deals = [positions(128, 8, 2026090552 + j) for j in range(2)]
    for i, (task, operation, plural) in enumerate(itertools.product(domains, operations, [False, True])):
        root = 'the named team Neris and Toma' if plural else 'Neris'
        action = f'{root} must {task} for issuer Mira, case D{10400+i}'
        prefix = 'Neris and Toma are different principals. Jori and Vale are outside the named responsible principal or team. '
        prefix += 'Ordinary instruments and advice are available. An external policy forbids sharing credentials.\n'
        for j, form in enumerate(['no-delegation', 'one-hop-delegation-allowed']):
            english = (action + '. No completion-bearing part may be assigned to a different principal. Deterministic tools, advice and existing reports do not count as delegation unless responsibility for an assigned subtask is transferred. Work inside a named responsible team is internal. The original principal or team remains accountable; no new authority is granted.'
                       if j == 0 else action + '. Completion-bearing work may be assigned to one or several immediate delegates, but none may pass it onward. Work inside a named responsible team is internal. The original principal or team remains accountable to the issuer, under the same constraints; no new authority is granted.')
            op_text = {
                'direct-one': 'assign a completion-bearing part to Jori as a direct delegate',
                'direct-many': 'split completion-bearing parts between Jori and Vale as two direct delegates',
                'second-hop': 'have direct delegate Jori pass a completion-bearing part onward to Vale',
                'deterministic-tool': 'use a deterministic calculator under the responsible principal\'s control, without giving another principal a subtask',
                'advice': 'ask Jori for advice while the responsible principal independently performs the whole assigned task',
                'existing-report': 'retrieve a report Jori already published, without assigning Jori any part of this task',
                'inside-team': 'give Toma a completion-bearing part as work inside the named responsible team' if plural else 'give Toma a completion-bearing part although Toma is outside the named responsible principal',
                'credential-sharing': 'give Jori the original principal\'s private credential despite the external prohibition',
            }[operation]
            allowed = (j == 1 if operation in ['direct-one', 'direct-many'] else
                       False if operation in ['second-hop', 'credential-sharing'] else
                       (plural or j == 1) if operation == 'inside-team' else True)
            options = [f'1: {a}; 2: {b}; 3: {c}' for a, b, c in itertools.product(
                ['yes', 'no'], ['yes', 'no'], ['the original principal or team', 'the external helper'])]
            answer = f"1: {'yes' if allowed else 'no'}; 2: no; 3: the original principal or team"
            question = (f'1. May the participants {op_text}? 2. Does this instruction permit an immediate delegate to pass assigned work to a further outside principal? '
                        '3. Who still owes Mira the completed result? Choose the entire three-part answer.')
            rows.append({'id': f'delegation-{i:03}-{j}', 'english': prefix + english,
                'ainglish': prefix + action + ', ' + form + '.', 'question': question,
                'options': rotate(options, answer, deals[j][i]), 'answer': answer,
                'settlement_stratum': form, 'strata': {'form': form, 'domain': task,
                    'operation': operation, 'plural_root': plural, 'frame_cluster': i}})
    return rows

def main():
    ROOT.mkdir(exist_ok=True)
    audit = {}
    for name, builder in [('fact-choice', fact_choice), ('delegation', delegation)]:
        real = builder()
        assert len(real) == 256 and len({r['id'] for r in real}) == 256
        assert len({(r['english'], r['ainglish'], r['question']) for r in real}) == 256
        assert sorted(Counter(r['settlement_stratum'] for r in real).values()) == [128, 128]
        assert len({r['strata']['frame_cluster'] for r in real}) == 128
        assert all(r['answer'] in r['options'] and len(set(r['options'])) == len(r['options']) for r in real)
        assert all(x not in r['english'] + r['ainglish'] for r in real for x in ['orchard', 'musician', 'metronome', 'arranger'])
        for exposure in ['cold', 'brief-reference']:
            data = json.loads(json.dumps(real + controls(name)))
            if exposure == 'brief-reference':
                for row in data:
                    for arm in ['english', 'ainglish']:
                        row[arm] = GUIDES[name] + '\n\n' + row[arm]
            save(name + '.' + exposure + '.items.json', data)
            audit[name + '.' + exposure] = {'scientific_items': 256, 'calibration_items': 8,
                'fixed_readers': 2, 'planned_real_calls': 512, 'planned_calibration_calls': 32,
                'items_sha256': hashlib.sha256(canonical(data)).hexdigest(),
                'form_counts': dict(Counter(r['settlement_stratum'] for r in real)),
                'answer_positions': dict(Counter(r['options'].index(r['answer']) for r in real)),
                'answer_positions_by_form': {form: dict(Counter(r['options'].index(r['answer']) for r in real if r['settlement_stratum'] == form)) for form in sorted({r['settlement_stratum'] for r in real})},
                'guide_words': len(GUIDES[name].split()) if exposure != 'cold' else 0,
                'reader_calls_so_far': 0, 'tokenizer_calls_so_far': 0}
        # The only between-condition change is a common reference prefix on BOTH arms.
        cold = json.loads((ROOT / (name + '.cold.items.json')).read_text())
        guided = json.loads((ROOT / (name + '.brief-reference.items.json')).read_text())
        for left, right in zip(cold, guided):
            for key in left:
                assert right[key] == (GUIDES[name] + '\n\n' + left[key] if key in ['english', 'ainglish'] else left[key])
    save('design-audit.json', audit)
    save('guides.json', GUIDES)
    print(json.dumps(audit, indent=2))

if __name__ == '__main__':
    main()
