"""Pure report-only comparison. No production evaluator, write API or adopted rule."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent

def eligible_bound_case(*,same_scope=True,valid=True,independent=True,prospective=True,
                        upper_bound=None,allowance=0):
    return all([same_scope,valid,independent,prospective,upper_bound is not None]) and upper_bound<=allowance

def tests():
    good=dict(same_scope=True,valid=True,independent=True,prospective=True,upper_bound=-.1)
    assert eligible_bound_case(**good)
    for key in ['same_scope','valid','independent','prospective']:
        assert not eligible_bound_case(**dict(good,**{key:False}))
    assert not eligible_bound_case(**dict(good,upper_bound=None))
    assert not eligible_bound_case(**dict(good,upper_bound=.01))
    assert eligible_bound_case(**dict(good,upper_bound=0)) # explicitly inclusive policy illustration
    # Agreement around the same wrong comparator is still invalid.
    assert not eligible_bound_case(valid=False,upper_bound=-10)
    # A favourable mean alone is not a known population uncertainty bound.
    assert not eligible_bound_case(upper_bound=None)

def main():
    tests();audit=json.loads((ROOT/'replacement-audit.json').read_text());cost=[]
    for row in audit['rows']:
        cost.append({'hash':row['manifest_hash'],'reported_sample_mean':row['value'],
          'sample_mean_within_declared_zero_allowance':row['value']<=0,
          'current_reproduced_ok':row['reproduced_ok'],
          'population_upper_confidence_bound':None,
          'alternative_rule_result':'not assessable: member_span is not message-sampling uncertainty',
          'current_governance_change':False})
    reader=[]
    for folder in sorted((ROOT/'readers').iterdir()):
        f=folder/'execution'/'analysis.json'
        if not f.exists():continue
        d=json.loads(f.read_text());h=d['headline']
        reader.append({'study':d['study'],'hash':d['manifest_hash'],
          'interval_95':h['interval_95'],'illustrative_minus_3pp_numerical_check_only':h['interval_95'][0]>-3,
          'ainglish_aggregate_at_least_90_percent':h['arms']['ainglish']>=.9,
          'resolution_bound':h['resolution_bound'],
          'route_pass':False,
          'why_not_a_pass':['Margin and absolute floor here are shadow examples, not newly adopted criteria.',
             'No independent confirmation; no validated template-cluster uncertainty; no demonstrated separate benefit.',
             'Aggregate checks cannot substitute for every required form or resolve an old confirmed null/adverse source.']})
    result={'kind':'ainglish.prospective-policy-shadow.v1','governance_effect':'report_only',
        'code_is_production_evaluator':False,'adversarial_assertions_passed':10,
        'cost':cost,'reader':reader,'claimed_verdict_flips':0}
    target=ROOT/'policy-shadow.json'
    if target.exists():assert json.loads(target.read_text())==result
    else:
        with target.open('x') as f:json.dump(result,f,indent=2)
    print('Shadow cases:',len(cost),'cost,',len(reader),'reader; no claimed verdict flips.')
if __name__=='__main__':main()
