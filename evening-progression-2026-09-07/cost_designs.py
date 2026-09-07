"""Prospective authored complete-message pairs; generates no tokenizer/reader calls.

Template variants are not independent natural-language populations. Shared
reference definitions are outside both cost arms, never charged only to English.
"""
from fractions import Fraction


def no_undo():
    actions = ['Published bulletin', 'Revoked permit', 'Deleted archive', 'Replaced record',
               'Changed route', 'Removed schedule', 'Overwrote image', 'Updated policy']
    paths = ['snapshot S3', 'the signed archive, within 14 days',
             'backup B8; loses the last hour of changes', 'recovery record R6']
    pairs = []
    for i, action in enumerate(actions):
        for j, path in enumerate(paths):
            message = f'{action} E{i}{j}'
            pairs.extend([
                {'id': f'undo-{i}-{j}-n', 'stratum': 'no-undo',
                 'english': f'{message} irreversibly.', 'ainglish': f'{message}, no-undo.'},
                {'id': f'undo-{i}-{j}-y', 'stratum': 'can-undo',
                 'english': f'{message}; restorable from {path}.', 'ainglish': f'{message}, can-undo({path}).'}])
    return pairs


def durations():
    pairs = []
    for i in range(32):
        p, w = f'state-{i+40}', f'window-{i+90}'
        # Two non-abutting true stretches inside a completely known 120-minute
        # elapsed-time window; exact arithmetic, not a sampled availability claim.
        lengths = (5 + i % 8, 11 + i % 5)
        for form, value in [('time-total', sum(lengths)), ('longest-stretch', max(lengths))]:
            english = f'Total {p} time in {w}: {value}min.' if form == 'time-total' else f'Longest uninterrupted {p} stretch in {w}: {value}min.'
            pairs.append({'id': f'duration-{i}-{form}', 'stratum': form, 'english': english,
                          'ainglish': f'{form}({p},{w}) = {value}min.'})
    return pairs


def outcomes(compact=False):
    pairs = []
    for i in range(32):
        ref = f'forecast-{i+70}'
        # Positive rational masses sum to one; mean and a mode are computed
        # exactly from one fixed finite distribution, never a realised result.
        distribution = [(0, Fraction(1, 2)), (2 * (i % 4 + 1), Fraction(1, 4)),
                        (4 * (i % 4 + 1), Fraction(1, 4))]
        mean = sum(x * p for x, p in distribution)
        for form, value in [('mean-outcome', str(mean)), ('likeliest-outcome', '0')]:
            if form == 'mean-outcome':
                english = f'Mean under {ref}: {value}.' if compact else f'Under {ref}, the probability-weighted mean is {value}.'
            else:
                english = f'A most probable outcome under {ref}: {value}.' if compact else f'Under {ref}, {value} has the highest outcome probability, ties allowed.'
            pairs.append({'id': f'outcome-{i}-{form}', 'stratum': form, 'english': english,
                          'ainglish': f'{value} is {form}({ref}).'})
    return pairs


def sanctions():
    # Fresh reports in the same formal-act genres as the target; 8/8 polarities.
    permissions = [
        ('banking commission', 'the lender to open office 9', 'the lender may open office-9'),
        ('research board', 'the vaccine trial to recruit adults', 'the vaccine trial may recruit adults'),
        ('borough council', 'the fair to operate on Fridays', 'the fair may operate on Fridays'),
        ('flight regulator', 'the carrier to serve Riga', 'the carrier may serve Riga'),
        ('privacy commission', 'the clinic to release anonymised images', 'the clinic may release anonymised images'),
        ('ballot authority', 'the coalition to register its slate', 'the coalition may register its slate'),
        ('harbour board', 'the freighter to use berth 8', 'the freighter may use berth-8'),
        ('protocol council', 'edition 6 to be distributed', 'edition-6 may be distributed'),
    ]
    penalties = [
        ('finance board', 'the broker', 'trades suspended for 14 days'),
        ('ethics panel', 'the laboratory', 'grants suspended for two years'),
        ('athletics union', 'the team', 'home ground closed for three matches'),
        ('competition commission', 'the wholesaler', 'fined 3 million pounds'),
        ('licensing board', 'the dentist', 'licence suspended for four months'),
        ('water authority', 'the factory', 'effluent volume restricted to 80 litres daily'),
        ('education board', 'the instructor', 'barred from residential trips this semester'),
        ('international council', 'the territory', 'weapons imports restricted for one year'),
    ]
    rows = []
    for authority, english, marked in permissions:
        rows.append({'stratum': 'allow', 'english': f'The {authority} formally permitted {english}.',
                     'ainglish': f'sanction-allow({authority.replace(" ", "-")}): {marked}.'})
    for authority, target, penalty in penalties:
        rows.append({'stratum': 'penalize',
            'english': f'The {authority} formally imposed a penalty on {target}: {penalty}.',
            'ainglish': f'sanction-penalize({authority.replace(" ", "-")}): {target}, {penalty}.'})
    return rows


GENERATORS = {'no-undo': no_undo, 'duration': durations, 'outcome-careful': outcomes,
              'outcome-compact': lambda: outcomes(True), 'sanction': sanctions}


def shared_contexts():
    return {'kind': 'ainglish.authored-cost-contexts.v1',
        'scope': 'Synthetic cost claims, not factual reports about real organisations. Context is identical and excluded from both cost arms; no amortised whole-conversation saving is claimed.',
        'recovery': 'Eij identifies the action object uniquely in each pair. For no-undo, neither writer nor addressee has a return path. For can-undo, the named path is available to a party, with exactly the written expiry or data loss. Each pair is a separate hypothetical situation; the two forms do not assert contradictory facts in one world.',
        'durations': {f'state-{i+40}': {'subject':f'test device {i+40}', 'predicate':'device is powered',
            'window_ref':f'window-{i+90}', 'window':'elapsed minutes [0,120) from this trial\'s start',
            'true_intervals':[[2,7+i%8],[60,71+i%5]],'coverage':'complete; false at every other instant in the window'} for i in range(32)},
        'distributions': {f'forecast-{i+70}': {'event':f'one toy delay trial {i+70}','unit':'seconds','model_version':'frozen v1',
            'conditioning':'unconditional within this fictional trial model',
            'positive_masses':[[0,'1/2'],[2*(i%4+1),'1/4'],[4*(i%4+1),'1/4']]} for i in range(32)},
        'sanctions': 'Each named authority and target resolves to exactly one fictional body or entity within its report. Authority-name hyphenation is the original source rendering policy. Acts are formally asserted; neither arm independently proves lawful authority or execution.'}
