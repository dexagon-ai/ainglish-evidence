"""Freeze auditable, unbound comprehension kits; no inference and no governance writes."""
from itertools import product
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAPSHOT = Path('/home/dexagon/codex/ainglish-batch-20260908-ozDzOA')

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def finish(name, items, ledger, validity, extra):
    p = json.loads((SNAPSHOT / (name + '.proposal.json')).read_text())
    assert len(items) == len(ledger) == 192
    assert len({x['id'] for x in items}) == 192
    assert all(x['answer'] in x['options'] and len(set(x['options'])) == len(x['options']) <= 26 for x in items)
    save(ROOT / (name + '-kit') / 'items.json', items)
    save(ROOT / (name + '-kit') / 'scenario-ledger.json', ledger)
    save(ROOT / (name + '-kit') / 'validity-fixtures.json', validity)
    save(ROOT / (name + '-kit') / 'plan.json', {
        'proposal': p['public_id'], 'slug': p['slug'], 'targets': 192,
        'items_sha256': hashlib.sha256(json.dumps(items, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest(),
        'english_mapping_sha256': hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
        'prediction_sha256': hashlib.sha256(p['predicted_measurement'].encode()).hexdigest(),
        'status': 'unbound prospective kit, not a preregistered or completed measurement',
        'execution_hold': 'Confirm the named full-coverage cost original first; then complete independent semantic/admissibility review and bind exact qualified readers, controls, analysis and official attempt.',
        'limits': 'Authored domain/template cells are not independent natural-use samples. Exact-vector accuracy and each critical bit must both be reported. No new models, threshold relaxation, hidden-intention golds for bare wording or claim of independent replication.',
        **extra,
    })
    print(name, '192 ledger-first targets;', len(validity), 'validity fixtures; no inference', flush=True)

def postpone():
    domains = ['public-governance', 'standards', 'corporate', 'nonprofit', 'open-source', 'research', 'incident-review', 'team-planning']
    # This component compares faithful English only. Bare table is not secretly assigned one dialect's intention.
    options = [f'Present action: {a}; instruction asserts: {b}; specific return time guaranteed: {c}.'
               for a,b,c in product(['consider now', 'set aside now'], ['neither approval nor rejection', 'approval', 'rejection'], ['yes', 'no'])]
    items, ledger, validity = [], [], []
    for form, domain, variant in product(['consider-now', 'postpone'], domains, range(12)):
        matter = f'{domain} matter CT-{1200+len(ledger)}'
        entry = {'id': f'ct-{form}-{domain}-{variant}', 'form': form, 'domain': domain,
                 'speaker_variety': ['British', 'American', 'unspecified'][variant % 3],
                 'reader_variety': ['American', 'British', 'mixed'][variant % 3],
                 'delivery': 'spoken transcript' if variant % 2 else 'written instruction',
                 'ruleset': 'effect-stated' if variant % 4 == 0 else 'not pinned',
                 'matter': matter, 'session_action': 'consider now' if form == 'consider-now' else 'set aside now',
                 'instruction_asserts': 'neither approval nor rejection', 'return_time_guaranteed': False}
        ledger.append(entry)
        prefix = (f'Fictional {domain} meeting. This is a {entry["delivery"]}; speaker variety {entry["speaker_variety"]}, '
                  f'audience variety {entry["reader_variety"]}. The chair now gives this immediate-session instruction. ')
        if entry['ruleset'] == 'effect-stated':
            prefix += 'The local procedure explicitly uses the ordinary meanings stated in this instruction; no unstated parliamentary rule changes them. '
        else:
            prefix += 'No shared parliamentary ruleset has been named. '
        prefix += ['A participant wants approval, but that wish is not a vote. ',
                   'A participant wants rejection, but that wish is not a vote. ',
                   'No earlier decision about the matter is supplied. '][variant % 3]
        english = (f'Put {matter} before this meeting for consideration now; this does not assert approval, adoption or rejection.'
                   if form == 'consider-now' else
                   f'Do not take {matter} up in this meeting; keep it for possible later consideration, without rejecting it or guaranteeing a return time.')
        gold = f'Present action: {entry["session_action"]}; instruction asserts: neither approval nor rejection; specific return time guaranteed: no.'
        offset = len(items) % len(options)
        items.append({'id': entry['id'], 'english': prefix + english, 'ainglish': prefix + f'{form}({matter}).',
                      'question': 'What immediate action does the instruction request, what approval or rejection does that instruction itself assert, and does it guarantee a specific return time?',
                      'options': options[offset:] + options[:offset], 'answer': gold,
                      'settlement_stratum': form + '-' + entry['ruleset'], **{k: entry[k] for k in ['domain', 'speaker_variety', 'reader_variety', 'delivery', 'ruleset']}})
    for sense, text in [('furniture', 'Move the table to the wall.'), ('data', 'Read the data table.'),
                        ('database', 'Create the database table.'), ('fixed-rules', 'Inside named ruleset R, table means keep pending; translate the outward summary explicitly.')]:
        for variant in range(6):
            validity.append({'id': f'ct-carve-{sense}-{variant}', 'text': text,
                             'gold': 'Do not apply the unpinned cross-dialect procedural fork to this use.'})
    finish('postpone', items, ledger, validity, {
        'cost_original': '731894e988bbb6a473703d55ba259d137fe53ace009c7e792345edd2e036161a',
        'existing_reader_original': '48eb9efde1b65dc3d0ecb7af5f5bf0ed6260659b0e323592bc2394d5b6b5cb37',
        'existing_reader_scope': 'Small 14-target signal, -28.57pp, unconfirmed; target-construct calibration and source coverage need inspection. Do not erase it or call this kit a replication.',
        'remaining_components': ['At least 144 genuinely cross-dialect-live items after an unexposed admission review, before any bare-table accuracy claim',
                                 'Bare table interpretation choices remain descriptive unless its meaning is actually supplied by the item',
                                 'Named-ruleset bare controls with an explicitly stated effect and prospective null contrast',
                                 'Prospective corruption schedule with exact independently reviewed damaged-form golds'],
        'analysis': 'Per-form, dialect-pair and ruleset estimates; -5pp noninferiority; <=5% wrong-pole and <=5pp additional approval/rejection errors, with uncertainty. Never claim the +30pp bare-dialect hypothesis was tested by the careful-English component.'})

def replace():
    domains = ['credentials', 'dependencies', 'configuration', 'physical-parts', 'assigned-people', 'documents', 'data-records', 'clinical-instructions']
    items, ledger, validity = [], [], []
    forces = ['directive', 'completed-report', 'proposal', 'quotation']
    for domain, incoming_first, force, variant in product(domains, [False, True], forces, range(3)):
        index = 2100 + len(ledger)
        old, new, slot = f'O-{index}', f'N-{index}', f'S-{index}'
        entry = {'id': f'rk-{index}', 'domain': domain, 'old': old, 'new': new, 'slot': slot,
                 'force': force, 'completed': force == 'completed-report', 'incoming_first': incoming_first,
                 'old_destroyed': False, 'exchange_asserted': False, 'compatibility_asserted': False, 'authority_asserted': False}
        ledger.append(entry)
        mention = f'{new} and {old}' if incoming_first else f'{old} and {new}'
        prefix = (f'Fictional {domain} record, not a real operational or medical instruction. The two distinct references {mention} '
                  f'resolve uniquely; slot {slot} is the only role in scope. No authority, compatibility check, deletion or two-way exchange is supplied. ')
        en = f'remove {old} from slot {slot} and put {new} in that slot instead'
        ai = f'replace(old={old}, new={new}) in slot {slot}'
        wrapper = {'directive': 'Requested action: {text}. This is a request, not a completed-action report.',
                   'completed-report': 'Completed-action report: the following action has finished: {text}.',
                   'proposal': 'Proposed action, not yet performed or approved: {text}.',
                   'quotation': 'Quoted text only, not issued or performed: “{text}.”'}[force]
        def vector(o, n, occupant, destroyed='not asserted', exchange='not asserted', compatible='not asserted', authorized='not asserted'):
            return f'Leaves {o}; enters {n}; after completion {occupant}; destroyed {destroyed}; exchange {exchange}; compatible {compatible}; authorized {authorized}.'
        gold = vector(old, new, new)
        choices = [gold, vector(new, old, old), vector(old, new, old), vector(old, new, 'both'),
                   vector(old, new, new, destroyed='asserted'), vector(old, new, new, exchange='asserted'),
                   vector(old, new, new, compatible='asserted'), vector(old, new, new, authorized='asserted')]
        offset = len(items) % len(choices)
        items.append({'id': entry['id'], 'english': prefix + wrapper.format(text=en), 'ainglish': prefix + wrapper.format(text=ai),
                      'question': 'For the replacement direction described (whether requested, reported, proposed or quoted), identify the leaving and entering references and the slot occupant IF that replacement is completed. Which extra destruction, exchange, compatibility or authority claims does the replacement relation itself assert?',
                      'options': choices[offset:] + choices[:offset], 'answer': gold,
                      'settlement_stratum': domain, 'domain': domain, 'force': force, 'incoming_first': incoming_first,
                      'oracle': entry})
    for defect in ['missing-old-label', 'empty-new', 'unresolved-old', 'same-referent', 'ambiguous-label', 'unscoped-multiple-slots']:
        for variant in range(4):
            validity.append({'id': f'rk-invalid-{defect}-{variant}', 'defect': defect,
                             'text': {'missing-old-label': 'replace(O, new=N)', 'empty-new': 'replace(old=O, new=)',
                                      'unresolved-old': 'replace(old=unresolved-reference, new=N)', 'same-referent': 'replace(old=O, new=O)',
                                      'ambiguous-label': 'replace(old=O, new=N); O names two distinct objects without resolution',
                                      'unscoped-multiple-slots': 'replace(old=O, new=N); two roles are in scope and no target role is named'}[defect],
                             'gold': 'Clarify or refuse; do not guess a direction or affected slot.'})
    finish('replace', items, ledger, validity, {
        'cost_original': 'e2ff808e72df863f2c403344843ac1f8e81cd6ae3b55ed3150e05ff922de5842',
        'existing_reader_original': 'c43ed0b19e3b852a167854dd644672a33c1d8abb03e2649cbd1bb4fd25531a6d',
        'existing_reader_scope': '32 targets across incoming/departing references; -2.94pp unconfirmed. This full 192-scenario kit is new original coverage, not an independent replication of our own source.',
        'analysis': 'Report exact-vector accuracy and each bit by domain, force and reference order. -5pp noninferiority; >=92% exact role accuracy; wrong reversals >5% or excluded-inference errors >10% per domain remain adverse. Intervals crossing a bound remain inconclusive.',
        'remaining_components': ['Independently review the complete scenario ledger and 24 validity fixture golds',
                                 'Freeze a separate descriptive bare substitute/replace interpretation-choice arm, never hidden-intention accuracy',
                                 'Expand validity fixtures into fully pinned official reader items before spending on that diagnostic'],
    })

if __name__ == '__main__':
    postpone()
    replace()
