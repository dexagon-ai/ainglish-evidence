"""Prospective review fixtures for the promised comparator preview, not live policy.

Extends the earlier 18 invented cases. Boolean declarations are fixture inputs,
not evidence that an actual corpus, bootstrap or independently confirmed study exists.
"""
import copy,importlib.util,json
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/'progression-programme-2026-09-10/acceptance_fixtures.py'
spec=importlib.util.spec_from_file_location('prior_comparator_cases',PATH)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)

BASE=prior.BASE | {'margin':2,'interval':[-1,2], 'required_form_lowers':[-1,-1],
    'bare_sampling_external':True,'bare_sampling_preregistered':True,
    'learnability_promised':False,'same_cell_cold_baseline':True,'learning_confirmed':False,
    'bootstrap_seed_frozen':True,'bootstrap_resamples_frozen':True,
    'reader_item_clustering':True,'one_sided_strata':True,
    'token_cost_is_descriptive':True,'future_training_gain_measured':False}

CASES=[
    ('S',{},None),
    ('T',{'confirmed_loss':True,'interval':[-1.5,-.5]},'confirmed_loss_veto'),
    ('U',{'required_form_lowers':[-2,-.1]},'strict_per_form_margin_not_cleared'),
    ('V',{'bare_promised':True,'bare_confirmed':True,'bare_sampling_external':False},'bare_selection_not_external'),
    ('W',{'bare_promised':True,'bare_confirmed':True,'bare_sampling_preregistered':False},'bare_selection_not_frozen'),
    ('X',{'learnability_promised':True,'learning_confirmed':True,'same_cell_cold_baseline':False},'learning_baseline_not_same_cell'),
    ('Y',{'learnability_promised':True},'promised_learning_not_confirmed'),
    ('Z',{'bootstrap_seed_frozen':False},'bootstrap_seed_not_frozen'),
    ('AA',{'bootstrap_resamples_frozen':False},'bootstrap_resamples_not_frozen'),
    ('AB',{'reader_item_clustering':False},'wrong_resampling_unit'),
    ('AC',{'one_sided_strata':False},'required_one_sided_strata_missing'),
    ('AD',{'token_cost_is_descriptive':False},'cost_must_not_stand_in_for_comprehension'),
    ('AE',{'future_training_gain_measured':True},'cold_or_entry_exposure_is_not_training'),
    ('AF',{'interval':[0,0],'accuracy':1,'uncertainty_valid':False},'uncertainty_unresolved'),
]


def interpret(c):
    flags=[x for x in prior.interpret(c) if x!='candidate_preservation_and_promises_complete']
    checks=[
        (any(x<=-c['margin'] for x in c['required_form_lowers']),'strict_per_form_margin_not_cleared'),
        (c['bare_promised'] and not c['bare_sampling_external'],'bare_selection_not_external'),
        (c['bare_promised'] and not c['bare_sampling_preregistered'],'bare_selection_not_frozen'),
        (c['learnability_promised'] and not c['same_cell_cold_baseline'],'learning_baseline_not_same_cell'),
        (c['learnability_promised'] and not c['learning_confirmed'],'promised_learning_not_confirmed'),
        (not c['bootstrap_seed_frozen'],'bootstrap_seed_not_frozen'),
        (not c['bootstrap_resamples_frozen'],'bootstrap_resamples_not_frozen'),
        (not c['reader_item_clustering'],'wrong_resampling_unit'),
        (not c['one_sided_strata'],'required_one_sided_strata_missing'),
        (not c['token_cost_is_descriptive'],'cost_must_not_stand_in_for_comprehension'),
        (c['future_training_gain_measured'],'cold_or_entry_exposure_is_not_training')]
    flags.extend(flag for bad,flag in checks if bad)
    return flags or ['candidate_preservation_and_promises_complete']


def check():
    rows=prior.check()
    for name,change,expected in CASES:
        actual=interpret(copy.deepcopy(BASE|change))
        if expected:
            assert expected in actual,(name,actual)
            assert 'candidate_preservation_and_promises_complete' not in actual
        else:assert actual==['candidate_preservation_and_promises_complete']
        rows.append({'case':name,'required':expected,'actual':actual})
    return rows


if __name__=='__main__':
    print(json.dumps({'kind':'prospective-comparator-review-fixtures.v2','measurement':False,
        'live_rule_changed':False,'two_pp_margin':'Reticuli preview commitment fixture, not a new global default',
        'cases':check()},indent=2))
