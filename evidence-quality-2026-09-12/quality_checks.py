"""Narrow pre-spend checks. Unsupported meanings are unassessed, not a pass."""
from collections import Counter
import re

def exposure_counts(items, readers, metric):
    if type(readers) is not int or readers < 1:
        raise ValueError('Need a positive exact roster count, not n_eff')
    if metric not in {'learnability', 'comprehension_accuracy_delta'}:
        raise ValueError('This counter does not cover robustness quartets or custom designs')
    if any('calibration' in x and type(x['calibration']) is not bool for x in items):
        raise ValueError('Calibration flag must be boolean')
    targets = [x for x in items if not x.get('calibration', False)]
    controls = [x for x in items if x.get('calibration', False)]
    arms = 2 if metric == 'learnability' else 1
    return {'kind': 'reference-panel-planned-exposure', 'metric': metric,
        'target_items': len(targets), 'calibration_items': len(controls), 'reader_roster_count': readers,
        'planned_target_calls': len(targets)*readers*arms,
        'planned_calibration_calls': len(controls)*readers*2,
        'per_target_arm_calls': len(targets)*readers if arms == 2 else None,
        'per_calibration_arm_calls': len(controls)*readers,
        'target_forms': dict(Counter(x.get('strata',{}).get('form','undeclared') for x in targets)),
        'observed_calls': None, 'independent_trials': None,
        'boundary': 'Planned reference-harness calls, not observed yield or independent trials. '
                    'Qualification calls are separate. CAD arm allocation must be read from actual journals.'}

def rent_learning_oracle(row):
    """Only the published RL indicator grammar, parsed from visible facts, not row gold."""
    if row.get('calibration'):
        return {'status': 'unassessed', 'reason': 'Control, not a rent target'}
    if row.get('english') != row.get('ainglish'):
        return {'status': 'unassessed', 'reason': 'Entry-only intervention requires identical cold/loaded marked text'}
    text = row.get('ainglish',''); question = row.get('question','')
    clause = re.search(r'\. ([A-Za-z]+) will rent-(borrow|lend) the (.+?)(?: from ([A-Za-z]+)| to ([A-Za-z]+))?\.$', text)
    if not clause:
        return {'status': 'unassessed', 'reason': 'Unrecognised positive rental clause'}
    subject, form = clause[1], clause[2]
    if (clause[4] and form != 'borrow') or (clause[5] and form != 'lend'):
        return {'status': 'unassessed', 'reason': 'Contradictory counterparty direction'}
    if question == f"Should the desk switch on {subject}'s amber indicator for this booking?":
        acquiring = 'for the party that obtains temporary use of the asset, and leaves the other party\'s indicator off.'
        providing = 'for the party that makes the asset available for temporary use, and leaves the other party\'s indicator off.'
        if (acquiring in text) == (providing in text):
            return {'status': 'unassessed', 'reason': 'Indicator rule absent or ambiguous'}
        yes = (form == 'borrow') == (acquiring in text)
    elif question == 'Should this booking have the jade indicator switched on?':
        paid = 'for arrangements in which temporary use is acquired for a fee, and leaves it off for the other kind.'
        free = 'for arrangements in which temporary use is provided free of charge, and leaves it off for the other kind.'
        if (paid in text) == (free in text):
            return {'status': 'unassessed', 'reason': 'Fee indicator rule absent or ambiguous'}
        yes = paid in text
    else:
        return {'status': 'unassessed', 'reason': 'Question outside supported indicator grammar'}
    options = row.get('options',[])
    expected = 'Yes' if yes else 'No'
    return {'status': 'checked', 'form': form, 'derived_answer': expected,
        'exact_binary_choice_set': sorted(options) == ['No','Yes'],
        'unique_correct_option': options.count(expected) == 1,
        'key_agrees': row.get('answer') == expected,
        'scope': 'Positive future-modal rental and explicit indicator rule; not general semantic certification'}
