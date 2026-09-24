"""Illustrative claim-route truth table; does not implement register eligibility."""
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
path=ROOT.parent/'endstate-programme-2026-09-11/comparator_acceptance.py'
spec=importlib.util.spec_from_file_location('existing_review_cases',path)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)

BASE=dict(confirmed_loss=False, valid_uncertainty=True, all_promises_met=True,
          careful_superiority=False, careful_preservation=True,
          bare_superiority=True, corpus_recoverable=True, prospective=True,
          independent_confirmation=True, actual_separate_benefit=False)


def interpret(c, route):
    if route not in ('current_superiority','comparator_v5','preservation_discussion'):
        raise ValueError('unknown route')
    checks=[('confirmed_loss_veto',not c['confirmed_loss']),
            ('uncertainty_unresolved',c['valid_uncertainty']),
            ('promises_incomplete',c['all_promises_met']),
            ('independent_confirmation_missing',c['independent_confirmation'])]
    if route=='current_superiority': checks.append(('no_careful_superiority',c['careful_superiority']))
    else:
        checks.extend([('not_prospective',c['prospective']),('preservation_unresolved',c['careful_preservation'])])
        if route=='comparator_v5': checks.extend([('source_corpus_not_recoverable',c['corpus_recoverable']),('no_bare_superiority',c['bare_superiority'])])
        else: checks.append(('no_separate_demonstrated_benefit',c['actual_separate_benefit']))
    return [name for name,ok in checks if not ok] or ['illustrative_requirements_satisfied_not_live_approval']


def check():
    old=prior.check()
    cases=[
        ('preservation_and_corpus_gain',{}, ['no_careful_superiority'], [], ['no_separate_demonstrated_benefit']),
        ('small_confirmed_loss_inside_margin',{'confirmed_loss':True}, ['confirmed_loss_veto'], ['confirmed_loss_veto'], ['confirmed_loss_veto']),
        ('authored_bare_is_not_corpus',{'corpus_recoverable':False}, [], ['source_corpus_not_recoverable'], []),
        ('neutral_cost_is_not_savings',{'bare_superiority':False}, [], ['no_bare_superiority'], ['no_separate_demonstrated_benefit']),
        ('actual_confirmed_savings',{'bare_superiority':False,'actual_separate_benefit':True}, ['no_careful_superiority'], ['no_bare_superiority'], []),
        ('all_correct_zero_width_uncalibrated',{'valid_uncertainty':False}, ['uncertainty_unresolved'], ['uncertainty_unresolved'], ['uncertainty_unresolved']),
        ('post_exposure_relabel',{'prospective':False}, [], ['not_prospective'], ['not_prospective']),
        ('one_failed_marker',{'all_promises_met':False}, ['promises_incomplete'], ['promises_incomplete'], ['promises_incomplete']),
        ('unconfirmed',{'independent_confirmation':False}, ['independent_confirmation_missing'], ['independent_confirmation_missing'], ['independent_confirmation_missing']),
        ('genuine_careful_superiority',{'careful_superiority':True}, [], [], []),
        ('preservation_unresolved',{'careful_preservation':False}, [], ['preservation_unresolved'], ['preservation_unresolved'])]
    rows=[]
    for label,delta,*expected in cases:
        c=BASE|delta; decisions={route:interpret(c,route) for route in ('current_superiority','comparator_v5','preservation_discussion')}
        for actual,needed in zip(decisions.values(),expected): assert set(needed)<=set(actual),(label,actual,needed)
        rows.append({'case':label,'premises':c,'routes':decisions})
    assert interpret(BASE,'comparator_v5')==['illustrative_requirements_satisfied_not_live_approval']
    assert interpret(BASE|{'actual_separate_benefit':True},'preservation_discussion')==['illustrative_requirements_satisfied_not_live_approval']
    return {'kind':'claim-route-review-matrix.v1','measurement':False,'live_rules_changed':False,
            'prior_fixture_count':len(old),'new_case_count':len(rows),'cases':rows}


if __name__=='__main__':
    result=check();(ROOT/'acceptance-matrix.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
