"""Freeze new prospective originals before mint; no model or tokenizer calls."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from ainglish import estimand
from ainglish.reader_qualification import attach
from instrument import ROOT, PRIOR, canonical, controls, save

IDS = {'instruction': 'a-pfneg523cg48ny0c', 'clock': 'a-9zr8dzy0b5r5zcyp',
       'quantity': 'a-k2d3rxn56qysr74n', 'choice': 'a-g973ekza7973r5f2', 'probability': 'a-b46kna5nkdy1d1fq'}
ORDER = ['instruction.careful', 'clock.careful', 'quantity.cold', 'quantity.reference',
         'choice.cold', 'choice.reference', 'probability.numeric', 'probability.boundaries']


def choice_row(ident, english, ainglish, question, meanings, gold, pos, stratum, audit):
    other = [m for m in dict.fromkeys(meanings) if m != gold]
    assert len(other) >= 3
    values = other[:3]
    values.insert(pos % 4, gold)
    return {'id': ident, 'english': english, 'ainglish': ainglish,
            'question': question + ' ' + ' '.join(f'{l} = {v}.' for l, v in zip('ABCD', values)),
            'options': list('ABCD'), 'answer': 'ABCD'[pos % 4], 'settlement_stratum': stratum,
            'strata': dict(audit, semantic_gold=gold, answer_options=dict(zip('ABCD', values)))}


def clock_items():
    rows = []
    zones = ['Europe/London', 'America/New_York', 'Asia/Kolkata', 'Australia/Sydney']
    for condition in ('utc', 'civil', 'missing-date-utc', 'missing-date-civil', 'fold', 'gap', 'recurring-civil', 'recurring-utc'):
        for i in range(16):
            label = f'event ON-{condition}-{i}'
            date = ['2026-01-15', '2026-07-15'][i % 2]
            hour, minute = 9 + i % 5, (i % 4) * 15
            clock = f'{hour:02}:{minute:02}'
            zone = zones[(i // 2) % len(zones)]
            audit = {'condition': condition, 'frame_cluster': f'clock-{condition}-{i}', 'date': date, 'zone': zone, 'clock': clock}
            if condition in ('utc', 'civil'):
                common = f'The date of {label} is {date}. '
                e = common + f'It is scheduled at {clock} ' + ('UTC.' if condition == 'utc' else f'civil time in {zone}, using the offset applicable on that date.')
                a = common + f'It is scheduled at {clock}' + ('Z.' if condition == 'utc' else f'@{zone}.')
                dt = datetime.fromisoformat(date + 'T' + clock).replace(tzinfo=timezone.utc if condition == 'utc' else ZoneInfo(zone))
                gold = dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
                q = 'Which UTC instant is the event scheduled for?'
                alternatives = ['not determined', date + ' 00:00 UTC', date + ' 23:59 UTC', date + ' 12:34 UTC']
                audit['utc_instant'] = gold
            elif condition.startswith('missing-date'):
                use_utc = condition == 'missing-date-utc'
                common = f'A single future {label} is mentioned. No date, recurrence or other dating context is supplied. '
                e = common + f'Time: {clock} ' + ('UTC.' if use_utc else f'civil time in {zone}.')
                a = common + f'Time: {clock}' + ('Z.' if use_utc else f'@{zone}.')
                gold = 'no unique dated instant'; q = 'Does this message identify one unique dated instant?'
                alternatives = ['yes, exactly one instant', 'yes, always today', 'yes, always tomorrow']
            elif condition in ('fold', 'gap'):
                zone = 'Europe/London'
                date = '2026-10-25' if condition == 'fold' else '2026-03-29'
                clock = f'01:{(i % 4) * 15:02}'
                common = f'The date of {label} is {date}. No UTC offset, fold selector or gap-adjustment policy is supplied. '
                e = common + f'Time: {clock} civil time in Europe/London.'
                a = common + f'Time: {clock}@Europe/London.'
                naive = datetime.fromisoformat(date + 'T' + clock)
                instants = {naive.replace(tzinfo=ZoneInfo(zone), fold=f).astimezone(timezone.utc) for f in (0, 1)
                            if naive.replace(tzinfo=ZoneInfo(zone), fold=f).astimezone(timezone.utc).astimezone(ZoneInfo(zone)).replace(tzinfo=None) == naive}
                count = len(instants)
                assert count == (2 if condition == 'fold' else 0)
                gold = ['no matching instant', 'one matching instant', 'two matching instants'][count]
                q = 'How many actual UTC instants match that civil reading on the supplied date?'
                alternatives = ['no matching instant', 'one matching instant', 'two matching instants', 'the message guarantees a duration', 'three matching instants']
                audit.update(date=date, zone=zone, clock=clock, matching_instants=[x.isoformat() for x in sorted(instants)])
            else:
                civil = condition == 'recurring-civil'
                common = f'{label} is a daily recurring meeting in London, including 15 January and 15 July 2026. '
                e = common + f'Each meeting starts at {clock} ' + ('London civil time, using the offset applicable on each date.' if civil else 'UTC.')
                a = common + f'Each meeting starts at {clock}' + ('@Europe/London.' if civil else 'Z.')
                gold = 'the London clock reading stays fixed' if civil else 'the UTC clock reading stays fixed'
                alternatives = ['the London clock reading stays fixed', 'the UTC clock reading stays fixed', 'both clock readings stay fixed', 'neither is constrained', 'the duration stays fixed']
                q = 'Which clock reading is held fixed across those winter and summer dates?'
                january = datetime.fromisoformat('2026-01-15T' + clock).replace(tzinfo=ZoneInfo('Europe/London'))
                july = datetime.fromisoformat('2026-07-15T' + clock).replace(tzinfo=ZoneInfo('Europe/London'))
                assert january.utcoffset() != july.utcoffset()
            rows.append(choice_row(f'clock-overnight-{condition}-{i}', e, a, q, alternatives, gold, i, condition, audit))
    return rows


def capacity_items():
    rows = []
    for i in range(16):
        members = [f'R{i}-{x}' for x in 'ABC']; people = [f'P{i}-one', f'P{i}-two']
        capacity = 2 if i % 2 else 3
        assignment = [people[0]] * 3 if i % 4 < 2 else [people[0], people[1], people[0]]
        for form in ('same-for-all', 'may-vary-across'):
            bounded = f'SET-cap-{i}'
            common = f'{bounded} contains exactly {", ".join(members)}. Assign exactly one reviewer to each report. Both reviewers {" and ".join(people)} are eligible for every report. Each reviewer may handle at most {capacity} of these reports. Candidate assignment: ' + ', '.join(f'{m} to {p}' for m, p in zip(members, assignment)) + '. '
            english = common + ('All reports must use the same reviewer.' if form == 'same-for-all' else 'Reviewers may be the same or different across reports.')
            ainglish = common + f'Assign exactly one reviewer to each report, {form}({bounded}).'
            valid = [a for a in itertools.product(people, repeat=3) if max(Counter(a).values()) <= capacity and (form == 'may-vary-across' or len(set(a)) == 1)]
            gold = 'yes' if tuple(assignment) in valid else 'no'
            meanings = [gold, 'no' if gold == 'yes' else 'yes']
            if i % 2:
                meanings.reverse()
            rows.append({'id': f'choice-overnight-capacity-{i}-{form}', 'english': english, 'ainglish': ainglish,
                         'question': 'Does the candidate satisfy every stated requirement? ' + ' '.join(f'{l} = {v}.' for l,v in zip('AB',meanings)),
                         'options': list('AB'), 'answer': 'AB'[meanings.index(gold)], 'settlement_stratum': form + ':capacity',
                         'strata': {'form': form, 'probe': 'capacity', 'frame_cluster': f'capacity-{i}', 'semantic_gold': gold, 'answer_options': dict(zip('AB',meanings)),
                                    'members': members, 'values': people, 'capacity': capacity, 'candidate': assignment, 'valid_count': len(valid)}})
    return rows


def build():
    previous = importlib.util.spec_from_file_location('old_validation', PRIOR / 'validate_studies.py')
    mod = importlib.util.module_from_spec(previous); previous.loader.exec_module(mod)
    old_audit = mod.validate()
    save('previous-gold-audit.json', old_audit)
    studies = {}
    studies['instruction.careful'] = [r for r in json.loads((PRIOR / 'frozen/instruction.prospective.items.json').read_text()) if not r.get('calibration')]
    studies['clock.careful'] = clock_items()
    guides = json.loads((PRIOR / 'frozen/guides.json').read_text())
    for name in ('quantity', 'choice'):
        for exposure in ('cold', 'reference'):
            rows = [r for r in json.loads((PRIOR / 'frozen' / f'{name}.{exposure}.items.json').read_text()) if not r.get('calibration')]
            if name == 'choice':
                extra = capacity_items()
                if exposure == 'reference':
                    for row in extra:
                        for arm in ('english','ainglish'):
                            row[arm] = guides['choice'][arm] + '\n\n' + row[arm]
                rows += extra
            studies[f'{name}.{exposure}'] = rows
    probability = json.loads((PRIOR / 'token-studies/probability.comprehension-design-v2.json').read_text())
    for condition in ('numeric', 'boundaries'):
        studies['probability.' + condition] = [r for r in probability['items'] if (r['probe'] in ('probability','complement','odds-orientation')) == (condition == 'numeric')]
    save('frozen/probability-invalid-boundaries.json', probability['invalid_boundary_cases'])
    index = {}
    for stem in ORDER:
        rows = studies[stem]
        assert len({r['id'] for r in rows}) == len(rows)
        assert len({(r['english'],r['ainglish'],r['question']) for r in rows}) == len(rows)
        for row in rows:
            assert row['answer'] in row['options']
            info = row.get('strata', row.get('audit', {}))
            if 'answer_options' in info:
                assert info['answer_options'][row['answer']] == info['semantic_gold']
            elif 'answer_meanings' in info:
                assert info['answer_meanings'][row['answer']] == info['semantic_gold']
        strata = list(dict.fromkeys(r['settlement_stratum'] for r in rows))
        control_rows, truth = controls('study-' + stem, 12)
        calibrated = rows + [dict(id=r['id'], english=r['other'], ainglish=r['detectable'], question=r['question'],
            options=r['options'], answer=r['answer'], calibration=True, calibration_truth=truth[r['id']]) for r in control_rows]
        save(f'frozen/{stem}.items.json', calibrated)
        index[stem] = {'real_items': len(rows), 'control_items':12, 'strata':strata,
                       'items_sha256': hashlib.sha256(canonical(calibrated)).hexdigest(),
                       'semantic_classes': dict(Counter(r.get('strata',r.get('audit',{})).get('semantic_gold') for r in rows))}
    save('frozen/index.json', index)
    print(json.dumps(index, indent=2), flush=True)


def prepare(commit):
    assert json.loads((ROOT / 'instrument/finished.json').read_text())['state'] == 'validated'
    readers, receipts = [], []
    for name in ('mistral','gemma'):
        screen = json.loads((ROOT / 'instrument' / f'validation.{name}.screen.json').read_text())
        result = json.loads((ROOT / 'instrument' / f'validation.{name}.result.json').read_text())
        readers.append(screen['reader']); receipts.append(result['receipt'])
    index = json.loads((ROOT / 'frozen/index.json').read_text())
    for stem in ORDER:
        name, condition = stem.split('.')
        p = json.loads((ROOT / 'snapshot' / f'{name}.proposal.json').read_text())
        design = index[stem]; n = design['real_items']; strata = design['strata']
        exposure = 'brief-reference' if condition == 'reference' else 'cold-no-added-reference'
        spec = {'slug':p['slug'], 'construct':p['form'], 'metric':'comprehension_accuracy_delta', 'seed':2026090596,
                'models':[r['roster_id'] for r in receipts], 'panel':readers, 'panel_neff':2,
                'planted_arm':'ainglish', 'calibration_min_gap':.5,
                'admissibility':{'kind':'ainglish.panel.admissibility.v1','per_reader_calibration':True,
                    'max_off_option_cells':0,'max_absent_cells':0,'max_truncated_cells':0,'max_transport_fault_cells':0},
                'comparator':{'kind':'complete-careful-english-v1','description':'Identical contextual facts in both arms; direct complete English for the question asked. Scope and omitted dimensions are explicit in DESIGN.md.'},
                'comparison_identity':{'comparator_genre':'complete-careful-english-v1','exposure':exposure,
                    'form_strata':strata, 'reader_class':'two exact local digest-bound qualified Q4 readers', 'pair_rendering':stem,
                    'diagnostic_only':condition=='boundaries'},
                'settlement_strata':[{'id':s,'weight':1} for s in strata],
                'items_url':f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/frozen/{stem}.items.json',
                'items_sha256':design['items_sha256'],
                'estimand_contract':estimand.declaration_v2(population=f'{n} fixed authored {stem} cases; two named local reader configurations, not humans or random prose',
                    item_set_construction={'design':'overnight-unknown-aware-control-v1','items':n,'conditions':strata,'control_items':12,
                        'gold':'arithmetic/exhaustive assignment/date-zone checks plus explicit mapping audit','answer_format':'opaque option letters',
                        'reference_budget_words_per_arm':50 if condition=='reference' else 0},
                    reader_class='Existing Mistral Small 3.2 24B and Gemma 3 12B Q4 exact digests, temperature0, max64 output tokens, target-independent development then untouched validation',
                    window=exposure+'; stateless cells; no target retries, training or adaptive reader selection',
                    selection_rules={'weighting':'equal declared strata; all directions filed','gates':'per-reader calibration >=.5, zero malformed/absent/truncated/transport cells',
                        'stop':'any scientific abort stops remaining reader studies; independent CPU/UI work continues'}),
                'attempt':{'proposal_revision':p['slug'],
                    'estimand':f'New {stem} original, {n} items and {len(strata)} equally weighted conditions. Ainglish minus English accuracy in percentage points; not independent replication or future-trained performance.',
                    'admissibility_gates':['Published frozen design/gold before inference; no changes to earlier records',
                        'Live visible seconded/measured proposal, unchanged mapping and all declared prerequisites satisfied',
                        'Exact unexpired qualifications, already-local models only, no displacement of unrelated workloads',
                        'Each reader clears twelve target-independent controls at >=.5 planted-key gap; zero off-option, absent, truncated or transport cells',
                        'All finite admitted directions filed; any abort stops remaining scientific reader studies without retry',
                        'Reference contrasts, condition margins and cluster analyses are reported separately and do not select results'],
                    'planned_sample':{'scientific_items':n,'calibration_items':12,'readers':2,'real_calls':n*2,'calibration_calls':48,
                        'source_commit':commit,'mapping_sha256':hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
                        'analysis_seed':2026090597,'cluster_bootstrap_draws':2000,'diagnostic_only':condition=='boundaries'}}}
        save(f'{stem}.runspec.json',attach(spec,receipts))
        print(stem,n*2+48,'maximum calls',flush=True)


if __name__ == '__main__':
    {'build':build,'prepare':lambda:prepare(sys.argv[2])}[sys.argv[1]]()
