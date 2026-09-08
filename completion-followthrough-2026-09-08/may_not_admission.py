"""Create a blinded clause packet and prospective balanced consequence probes.

No calls to readers, no admission claims, no silently changed primary instrument.
The proposed two-stage interpretation of the author's gate needs clarification.
"""
import hashlib
from collections import Counter
from itertools import product

FRAMES = [
    ('transport', 'The courier', 'enter the depot'), ('transport', 'The shuttle', 'reach the island'),
    ('compute', 'The analyst', 'publish the package'), ('compute', 'The service', 'enter production'),
    ('learning', 'The student', 'finish the exercise'), ('learning', 'The teaching robot', 'enter the examination room'),
    ('workshop', 'The technician', 'start the lathe'), ('workshop', 'The delivery drone', 'reach the roof'),
    ('events', 'The speaker', 'arrive at the hall'), ('events', 'The display unit', 'activate the projector'),
    ('archive', 'The archivist', 'release the scan'), ('archive', 'The indexer', 'finish the catalogue'),
    ('garden', 'The gardener', 'open the greenhouse'), ('garden', 'The sprinkler', 'activate the valve'),
    ('port', 'The inspector', 'enter the warehouse'), ('port', 'The ferry', 'reach the quay'),
]


def blind(primary):
    unique = {}
    mapping = {}
    for row in primary:
        if row.get('calibration') or row.get('probe') != 'two-bit': continue
        clause = row['english'].rsplit('Statement: ', 1)[1]
        key = hashlib.sha256(clause.encode()).hexdigest()[:16]
        unique[key] = {'review_id': key, 'bare_clause': clause,
            'binding_prohibition_is_a_plausible_reading': None,
            'epistemic_nonoccurrence_is_a_plausible_reading': None,
            'reason_or_lexical_prior_concern': None}
        mapping.setdefault(key, []).append(row['id'])
    # Sorting by a content hash conceals the primary authoring order and intended tags.
    return [unique[k] for k in sorted(unique)], mapping


PROBES = {
    'physical-impossibility': ('Does the complete record establish that P is physically impossible?',
        'The record includes verified physical evidence that makes P impossible at the relevant time.'),
    'actual-nonoccurrence': ('Does the complete record establish that P did not actually occur?',
        'A later completed observation verifies that P did not occur in the specified interval.'),
    'permission-to-refrain': ('Does the complete record authorise the subject to refrain from P?',
        'An applicable authorising rule explicitly permits this subject to refrain from P.'),
    'absence-of-duty': ('Does the complete record rule out any applicable positive duty to perform P?',
        'The record explicitly certifies that no applicable obligation requires this subject to perform P.'),
}


def secondary(contrast):
    rows = []
    for form, (probe, (question, support)), frame, variant, licensed in product(
            ['prohibition', 'possibility'], PROBES.items(), range(16), range(5), [False, True]):
        domain, subject, predicate = FRAMES[frame]
        scope = ['during the referenced session', 'in the specified interval', 'at the appointed time',
                 'during the planned operation', 'on the referenced occasion'][variant]
        context = ('The earlier statement is an applicable conduct restriction, not a forecast.' if form == 'prohibition'
                   else 'The earlier statement is an epistemic assessment, not a conduct rule.')
        common = f'Fictional {domain} record. P means: {subject} will {predicate} {scope}. {context} '
        common += (support if licensed else 'No separate physical evidence, completed outcome, authorisation to refrain, or inventory of applicable duties is supplied.')
        common += ' Earlier statement: '
        expansion = (f'An applicable authority or rule forbids {subject.lower()} from satisfying P.' if form == 'prohibition'
                     else 'Under the speaker\'s current evidence or model, non-occurrence of P remains possible.')
        marked = f'{subject} may-not-as-{form} {predicate} {scope}.'
        bare = f'{subject} may not {predicate} {scope}.'
        answer = 'yes' if licensed else 'no'
        rows.append({'id':f'mn-balanced-{form}-{probe}-{frame}-{variant}-{int(licensed)}',
            'english':common+(expansion if contrast == 'careful' else bare),
            'ainglish':common+marked, 'question':question,
            'options':['yes','no'] if (frame+variant)%2 else ['no','yes'], 'answer':answer,
            'form':form,'probe':probe,'domain':domain,'licensed_by_separate_evidence':licensed,
            'settlement_stratum':form+'-'+probe,
            'analysis_role':'licensed-positive' if licensed else 'unsupported-inference-negative',
            'boundary':'The marked clause alone does not imply the consequence. Positive cases have separate explicit support, not a new marker meaning.'})
    return rows


def audit():
    rows=secondary('careful')
    counts=Counter((r['form'],r['probe'],r['analysis_role']) for r in rows)
    assert len(rows)==1280 and all(n==80 for n in counts.values())
    return {'secondary_items_per_comparator':1280,'per_form_per_probe':{'unlicensed':80,'licensed':80},
        'zero_error_one_sided_95_percent_upper_at_80_observations':1-.05**(1/80),
        'minimum_zero_error_denominator_for_upper_below_5_percent':59,
        'inference_run':False,'blinded_gate_passed':False,
        'analysis':'Keep primary two-bit recovery separate. Report unsupported-inference rates and positive-evidence sensitivity separately, by form, probe and exact reader. Compute bounds from actual assigned-arm denominators, not authored rows. A bound above 5% is inconclusive; never fill missing answers as correct. Single-rate intervals are not multiplicity-adjusted and correlated authored frames limit independence.'}
