"""Held diagnostic plans. No target calls and no claimed measured robustness."""
from itertools import product


def outcome_specification_diagnostics():
    cases=[
      ('partial','D lists mass 1/4 at zero and 1/4 at four; the remaining probability and outcomes are unspecified.',False),
      ('rounded','D displays probabilities rounded to one decimal place; their exact interpretation is unspecified.',False),
      ('ambiguous-reference','D may refer to model v1 or v2, whose masses differ; no version was chosen.',False),
      ('continuous','D is a continuous uniform distribution on [0,4], not a finite discrete mass distribution.',False),
      ('unknown-conditioning','D changes with the conditioning event, but which event applies has not been supplied.',False),
      ('unordered-values','D places mass 1/2 on blue and 1/2 on red, with no numeric quantity or numeric encoding.',False),
      ('exact-two-point','D uniquely identifies finite discrete model v2 for one stated event: mass 1/2 at zero units and 1/2 at four units.',True),
      ('exact-aggregated','D uniquely identifies finite discrete model v2: two disjoint paths each yield two units with mass 1/4; a third yields six units with mass 1/2.',True),
    ]
    rows=[]
    for marker,(kind,spec,valid),variant in product(['mean-outcome','likeliest-outcome'],cases,range(2)):
        common=f'Fictional specification check {variant+1}. {spec} Statement: '
        english='Under D, the probability-weighted mean is two units.' if marker=='mean-outcome' else 'Under D, two units has the highest outcome probability, ties allowed.'
        answer='Enough specification to check the claim, even if it is false.' if valid else 'Clarify or reject the specification before evaluating this registered claim.'
        options=['Enough specification to check the claim, even if it is false.',
                 'Clarify or reject the specification before evaluating this registered claim.']
        if variant:options.reverse()
        rows.append({'id':f'outcome-spec-{len(rows):02}','english':common+english,
          'ainglish':common+f'2 units is {marker}(D).',
          'question':'Does the supplied specification uniquely provide the finite numeric probability model required to check this exact registered claim? This asks evaluability, not whether the asserted value is true.',
          'options':options,'answer':answer,'settlement_stratum':marker,'diagnostic_class':kind,
          'diagnostic_only':True,'calibration':False,'oracle':{'specification_sufficient':valid}})
    assert len(rows)==32
    return rows


def bare_identity_description():
    # Deliberately no shared gold with the two explicit relation readings.
    domains=['book return','file handoff','account audit','container inventory','device repair','archive loan',
             'model deployment','worker update','record comparison','quantity check','document history','configuration exchange']
    return [{'id':f'bare-identity-{i:02}','context':f'Fictional {domain}. X and Y are resolved references; K is a named value projection.',
             'bare_text':'X and Y are the same.',
             'explicit_alternatives':['X same-instance-as(Y).','X value-equal-to(Y, by=K).'],
             'question':'Describe which relations the wording actually establishes and which remain ambiguous.',
             'scoring':'Descriptive interpretation choices only. Do not award correctness for recovering an undisclosed intended relation; do not pool with careful-English non-inferiority.'}
            for i,domain in enumerate(domains)]


def edit_schedule():
    return [{'candidate':name,'edit':edit,'expected_review':review,'executed':False}
      for name in ['identity/equality','duration','outcome statistics']
      for edit,review in [
        ('hyphen-to-space in marker words only','Check preservation of human meaning separately from strict machine-marker recognition.'),
        ('case/punctuation changes','Do not silently change case-sensitive references, epochs or predicate identity; report recognition and interpretation separately.'),
        ('delete a mandatory argument','Require clarification; never infer the absent entity, key, window or distribution.'),
        ('substitute a resolved reference','Meaning changes to the substituted referent; the original answer key is not valid by default.'),
        ('make a reference ambiguous','Require clarification rather than choosing the convenient referent.'),
        ('remove a load-bearing observation/model version','Do not infer current identity values, continuity, or a current probability model from stale information.'),
      ]]
