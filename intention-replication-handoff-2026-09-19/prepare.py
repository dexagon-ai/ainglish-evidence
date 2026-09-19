#!/usr/bin/env python3
"""Build and audit a prospective input candidate. No networking, readers, or submissions."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'intention-reader-review-2026-09-18' / 'items.json'
TARGET = 'cd045604bc95ddc33befcdeb1185ea4f73fb2f5af192767b735fb6824254950c'
SEED = 2026091911
READERS = (
    'mistral-small3.2-24b-opaque-choice-q4_k_m@q4_k_m',
    'gemma3-12b-opaque-choice-q4_k_m@q4_k_m',
)
ANCHORS = ('plan-a', 'plan-b', 'unforeseen', 'accepted-risk')
FRAMES = ('first-active', 'first-passive', 'third-active', 'third-passive')
STRATA = ('on-purpose-plan-match', 'by-accident-unforeseen-slip', 'by-accident-accepted-risk')
PREFIX = ("Fictional completed incident. Treat the anchor and report as jointly true. "
          "The anchor fixes the doer's prior aim; do not infer intention from benefit, "
          "harm, blame, or foreseeability. ")

# Six new domains, each containing sixteen distinct fictional action outcomes.
# Each line is a past participle | singular object | complement. Do not use results
# from any reader to select an action, its id, options, or arm.
DOMAINS = [
    ('museum_conservation', 'the conservator', '''
moved|the bronze figurine|to the isolation cabinet
removed|the linen backing|from the portrait
covered|the display label|with the protective sheet
rotated|the ceramic mask|toward the south window
sealed|the storage case|with the paper strip
detached|the silver clasp|from the display mount
lowered|the tapestry rail|to the inspection height
exposed|the pencil inscription|beneath the paper flap
transferred|the glass bead|to the numbered tray
folded|the tissue wrapper|over the painted surface
attached|the blue inventory tag|to the picture frame
placed|the plaster cast|on the padded shelf
darkened|the gallery window|with the removable screen
tilted|the wooden model|toward the camera
opened|the specimen drawer|during the inventory
swapped|the display stand|for the shorter support
'''),
    ('theatre_stagecraft', 'the stage technician', '''
lowered|the painted backdrop|behind the platform
shifted|the amber spotlight|toward the empty chair
muted|the foyer speaker|during the rehearsal
closed|the side curtain|before the final cue
raised|the centre rostrum|above the surrounding floor
disconnected|the smoke machine|from the control desk
covered|the exit sign prop|with black fabric
reversed|the scenery panel|to show its blank side
removed|the brass door handle|from the set
dimmed|the balcony lamp|during the scene change
locked|the rolling staircase|beside the orchestra pit
rotated|the mirror prop|away from the audience
relabelled|the lighting channel|as the spare circuit
shortened|the recorded pause|in the sound cue
lifted|the trapdoor cover|during the technical check
replaced|the red tablecloth|with the white cloth
'''),
    ('botanical_nursery', 'the nursery worker', '''
moved|the fern tray|under the shade net
opened|the eastern vent|above the seed bench
covered|the citrus pot|with the mesh sleeve
redirected|the mist nozzle|toward the empty rack
removed|the bamboo support|from the young vine
lowered|the hanging basket|onto the workbench
transferred|the orchid label|to the reserve pot
closed|the irrigation valve|beside the propagation bed
rotated|the cactus display|away from the doorway
replaced|the sand layer|with fine gravel
folded|the thermal screen|above the herb trough
isolated|the seedling batch|behind the partition
detached|the moisture probe|from the planter
raised|the mobile bench|to the upper stop
relocated|the empty watering can|to the storage alcove
trimmed|the trailing stem|above the yellow tie
'''),
    ('pottery_workshop', 'the potter', '''
moved|the clay bowl|onto the drying board
covered|the plaster mould|with a damp cloth
removed|the jug handle|before the clay dried
turned|the decorated tile|toward the work light
thinned|the blue glaze|with the measured water
closed|the cupboard door|beside the glazing table
transferred|the test cup|to the lower shelf
smoothed|the vase rim|with the sponge
lifted|the plate support|from the turntable
replaced|the wooden rib|with the flexible tool
stamped|the clay medallion|with the square mark
trimmed|the pedestal foot|to the pencil line
opened|the reclaim bin|during the clean-up
wrapped|the unfinished teapot|in the plastic sheet
labelled|the sample jar|as the transparent glaze
separated|the tile spacer|from the prepared stack
'''),
    ('audio_production', 'the sound editor', '''
muted|the room microphone|during the spoken introduction
moved|the vocal clip|to the second track
shortened|the fade-out|at the end of the theme
lowered|the percussion level|under the dialogue
removed|the count-in|from the exported mix
renamed|the ambience track|as the garden recording
duplicated|the closing chord|on the spare channel
reversed|the cymbal sample|in the preview clip
shifted|the interview marker|to the next sentence
disabled|the echo effect|on the announcement
inserted|the silence gap|before the final line
replaced|the left-channel take|with the backup recording
split|the rehearsal recording|at the applause marker
locked|the reference track|against timeline edits
filtered|the low hum|from the workshop recording
copied|the narration segment|into the alternate version
'''),
    ('community_kitchen', 'the kitchen volunteer', '''
moved|the flour tub|to the lower cupboard
covered|the prepared dough|with the clean towel
removed|the serving label|from the bread tray
transferred|the soup ladle|to the rinsing bowl
closed|the pantry window|above the storage shelf
replaced|the small colander|with the larger sieve
divided|the pastry sheet|along the marked line
lowered|the mixer guard|over the empty bowl
relocated|the recipe folder|to the noticeboard shelf
folded|the linen napkin|around the cutlery
opened|the spare carton|during the stock check
attached|the green order slip|to the lunch basket
swapped|the wooden spoon|for the silicone spatula
labelled|the biscuit tin|as the afternoon batch
placed|the empty cake stand|beside the serving hatch
turned|the cooling rack|toward the open workspace
'''),
]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def arm(seed, reader, item_id):
    return ('ainglish' if hashlib.sha256(f'{seed}|{reader}|{item_id}'.encode()).digest()[0] % 2
            else 'english')


def balanced_id(base, first_arm):
    # Minimum nonnegative suffix meeting content-only planned assignment. No target
    # answers have been obtained; this is not seed/assignment selection by outcomes.
    other = 'english' if first_arm == 'ainglish' else 'ainglish'
    for serial in range(100000):
        candidate = f'{base}-{serial:04d}'
        if [arm(SEED, r, candidate) for r in READERS] == [first_arm, other]:
            return candidate
    raise AssertionError('No assignment id found')


def anchor_text(anchor, doer):
    return {
        'plan-a': f'Before acting, {doer} selected a plan whose stated objective was exactly the result described in the report, and then followed that plan.',
        'plan-b': f'A signed work order called for exactly the result in the report; before acting, {doer} adopted that result as the objective.',
        'unforeseen': f'Before acting, {doer} had neither predicted nor sought the reported result. {doer[0].upper() + doer[1:]} learned that it had happened only after the action ended.',
        'accepted-risk': f'Before acting, {doer} listed the reported result as an unwanted possible side effect, accepted that risk, and did not seek that result.',
    }[anchor]


def make_bank():
    items = []
    for d, (domain, actor, source) in enumerate(DOMAINS):
        events = [line.split('|') for line in source.strip().splitlines()]
        assert len(events) == 16 and all(len(e) == 3 for e in events)
        for t, anchor in enumerate(ANCHORS):
            for f, frame in enumerate(FRAMES):
                verb, obj, rest = events[4 * t + f]
                positive = t < 2
                first_person = frame.startswith('first')
                doer = 'the speaker' if first_person else actor
                subject = 'I' if first_person else actor[0].upper() + actor[1:]
                report = f'{subject} {verb} {obj} {rest}'
                if frame.endswith('passive'):
                    agent = 'me' if first_person else actor
                    report = f'{obj[0].upper() + obj[1:]} was {verb} by {agent} {rest}'
                core = PREFIX + anchor_text(anchor, doer) + ' Report: ' + report
                form = 'on-purpose' if positive else 'by-accident'
                gold = 'yes' if positive else 'no'
                gold_position = (d // 2 + f + t) % 3
                options = [x for x in ('yes', 'no', 'cannot-tell') if x != gold]
                options.insert(gold_position, gold)
                desired = 'ainglish' if (d + t + f) % 2 else 'english'
                ident = balanced_id(f'DEX-INTENTION-20260919-{domain}-{anchor}-{frame}', desired)
                items.append({
                    'id': ident, 'domain': domain, 'anchor_class': anchor, 'frame': frame,
                    'settlement_stratum': STRATA[0] if positive else STRATA[t - 1],
                    'english': core + (' deliberately.' if positive else ' by mistake, without intending that outcome.'),
                    'ainglish': core + ' ' + form + '.', 'bare': core + '.',
                    'question': 'Was this outcome something the doer meant to bring about?',
                    'options': options, 'answer': gold, 'form': form,
                    'oracle': {'intended': positive, 'basis': 'shared prospectively authored anchor',
                               'bare_arm_status': 'prepared but not to be run or pooled in this two-arm candidate'},
                })
    names = ['Aster', 'Bran', 'Cleo', 'Daro', 'Edda', 'Fenn']
    for n in range(12):
        options = names + ['not specified']
        rotation = n % 7
        options = options[rotation:] + options[:rotation]
        items.append({
            'id': f'dex-intention-20260919-calibration-{n:02d}',
            'english': f'Exhibition card EC-{6310+n}: its custodian is not specified.',
            'ainglish': f'Exhibition card EC-{6310+n}: its custodian is {names[n % 6]}.',
            'question': f'Who is the custodian of exhibition card EC-{6310+n}?',
            'options': options, 'answer': names[n % 6], 'calibration': True,
            'calibration_construct': 'named exhibition custodian', 'calibration_scope': 'target-independent',
        })
    controls = []
    qnames = ['Galen', 'Hester', 'Ivo', 'Jessa', 'Kellan', 'Liora']
    for n in range(24):
        options = qnames + ['not specified']
        rotation = n % 7
        options = options[rotation:] + options[:rotation]
        controls.append({
            'id': f'dex-intention-20260919-qualification-{n:02d}',
            'detectable': f'Dispatch docket DD-{7420+n}: the receiving clerk is {qnames[n % 6]}.',
            'other': f'Dispatch docket DD-{7420+n}: the receiving clerk is not specified.',
            'question': f'Who is the receiving clerk on dispatch docket DD-{7420+n}?',
            'options': options, 'answer': qnames[n % 6],
        })
    return {'kind': 'dexagon.intention-replication-input-candidate.v1',
            'status': 'prepared_not_execution_authorised', 'target_hash': TARGET,
            'seed': SEED, 'readers': list(READERS), 'items': items,
            'sha256': digest(items), 'qualification_controls': controls}


def audit(bank):
    assert bank['seed'] == SEED and bank['readers'] == list(READERS)
    assert bank['target_hash'] == TARGET and bank['status'] == 'prepared_not_execution_authorised'
    old = json.loads(SOURCE.read_text())
    real = [i for i in bank['items'] if not i.get('calibration')]
    controls = [i for i in bank['items'] if i.get('calibration')]
    assert len(real) == 96 and len(controls) == 12 and len(bank['qualification_controls']) == 24
    for i in controls + bank['qualification_controls']:
        assert len(i['options']) == len(set(i['options'])) == 7
        assert i['answer'] in i['options'] and i['answer'] != 'not specified'
    assert len({i['id'] for i in bank['items']}) == 108
    assert all(' Report: ' in i['bare'] for i in real)
    assert len({i['bare'].split(' Report: ')[1] for i in real}) == 96
    assert Counter(i['settlement_stratum'] for i in real) == dict(zip(STRATA, (48, 24, 24)))
    assert Counter(i['anchor_class'] for i in real) == dict.fromkeys(ANCHORS, 24)
    assert Counter(i['frame'] for i in real) == dict.fromkeys(FRAMES, 24)
    old_pairs = {(i['english'], i['ainglish']) for i in old['items']}
    new_pairs = {(i['english'], i['ainglish']) for i in bank['items']}
    assert not old_pairs & new_pairs
    old_sides = {i[k] for i in old['items'] for k in ('english', 'ainglish')}
    new_sides = {i[k] for i in bank['items'] for k in ('english', 'ainglish')}
    assert not old_sides & new_sides
    predecessor = json.loads((ROOT.parent / 'language-progression-comprehension-wave-v1-2026-09-04'
                              / 'actor-intention.items.json').read_text())['items']
    assert digest(predecessor) == '4c2661fe16c36c1093f4042d1cf9bbcc6cd2f4519474b2b81d9a476c7370f987'
    assert not new_pairs & {(i['english'], i['ainglish']) for i in predecessor}
    assert not new_sides & {i[k] for i in predecessor for k in ('english', 'ainglish')}
    assert not {i['domain'] for i in real} & {i['domain'] for i in old['items'] if not i.get('calibration')}
    old_q = {i[k] for i in old['qualification_controls'] for k in ('detectable', 'other')}
    assert not old_q & {i[k] for i in bank['qualification_controls'] for k in ('detectable', 'other')}
    exposure = defaultdict(Counter)
    gold = defaultdict(Counter)
    domain_counts = defaultdict(Counter)
    plan = []
    for i in real:
        positive = i['anchor_class'] in ('plan-a', 'plan-b')
        assert i['answer'] == ('yes' if positive else 'no')
        assert i['oracle']['intended'] is positive
        assert set(i['options']) == {'yes', 'no', 'cannot-tell'}
        suffix = ' deliberately.' if positive else ' by mistake, without intending that outcome.'
        assert i['english'][:-len(suffix)] == i['ainglish'][:-len(' ' + i['form'] + '.')] == i['bare'][:-1]
        arms = [arm(SEED, r, i['id']) for r in READERS]
        assert set(arms) == {'english', 'ainglish'}
        for r, a in zip(READERS, arms):
            key = '/'.join((r, i['anchor_class'], i['frame']))
            exposure[key][a] += 1
            gold[key + '/' + a][i['options'].index(i['answer']) + 1] += 1
            domain_counts['/'.join((r, i['settlement_stratum'], i['domain']))][a] += 1
            plan.append({'reader': r, 'item_id': i['id'], 'arm': a,
                         'stratum': i['settlement_stratum'], 'domain': i['domain'],
                         'anchor_class': i['anchor_class'], 'frame': i['frame'],
                         'gold_position': i['options'].index(i['answer']) + 1})
    assert len(exposure) == 32 and all(x == {'english': 3, 'ainglish': 3} for x in exposure.values())
    assert len(gold) == 64 and all(x == {1: 1, 2: 1, 3: 1} for x in gold.values())
    assert all(x['english'] == x['ainglish'] for x in domain_counts.values())
    assert digest(bank['items']) == bank['sha256']
    # Exact original roster only. This candidate does not inherit its qualification receipts.
    return {'kind': 'dexagon.intention-replication-design-audit.v1',
            'status': 'cpu_preparation_only_raw_audit_and_executor_gates_pending',
            'target_hash': TARGET, 'items_sha256': bank['sha256'], 'seed': SEED,
            'scientific_items': 96, 'panel_controls': 12, 'qualification_controls': 24,
            'distinct_report_cores': 96, 'original_complete_pair_overlap': 0,
            'original_individual_arm_overlap': 0, 'original_qualification_side_overlap': 0,
            'known_predecessor_complete_pair_overlap': 0, 'known_predecessor_individual_arm_overlap': 0,
            'known_predecessor_items_sha256': digest(predecessor),
            'freshness_scope': 'Compared against cd045604 public original and the 48-item 7fa32b59 source served on its sole live predecessor. Unfiled or external campaign inputs are not covered; executor must refresh before mint.',
            'reader_anchor_frame_arm_counts': dict(sorted(exposure.items())),
            'reader_anchor_frame_arm_gold_counts': dict(sorted(gold.items())),
            'reader_stratum_domain_arm_counts': dict(sorted(domain_counts.items())),
            'planned_scientific_cells': 192, 'planned_panel_calls_including_controls': 240,
            'planned_qualification_calls_if_both_rosters_need_new_receipts': 96,
            'reader_calls_performed': 0, 'attempts_minted': 0, 'measurements_filed': 0,
            'assignment_plan': plan}


if __name__ == '__main__':
    bank = make_bank()
    report = audit(bank)
    original = json.loads((SOURCE.parent / 'measurement.json').read_text())['manifest']
    handoff = {
        'kind': 'dexagon.intention-replication-handoff.v1',
        'status': 'preparation_only_not_an_attempt_payload',
        'proposal': 'a-ef4rsdm2ksnkdz2r', 'canonical_slug': 'on-purpose-by-accident-2',
        'replicates_hash': TARGET, 'metric': 'comprehension_accuracy_delta',
        'seed': SEED, 'items_sha256': bank['sha256'],
        'readers': original['readers'], 'comparator': original['comparator'],
        'settlement_strata': original['settlement_strata'],
        'settlement_item_field': original['settlement_item_field'],
        'interval_estimator': {k: v for k, v in original['interval_estimator'].items()
                               if k != 'items_index_sha256'},
        'prerequisite_stop': 'Original retained-response audit unresolved; no inference or mint authorised by this packet.',
        'qualification_receipts': None,
        'qualification_note': 'Executor supplies their own current exact-roster receipts; source submitter receipts are not copied.',
        'planned_calls': {'scientific': 192, 'calibration': 48, 'qualification_if_required': 96},
        'reader_calls_performed': 0,
    }
    for name, value in [('items.json', bank), ('design-audit.json', report), ('HANDOFF.json', handoff)]:
        (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: report[k] for k in ('items_sha256', 'scientific_items',
                      'original_complete_pair_overlap', 'reader_calls_performed', 'status')}))
