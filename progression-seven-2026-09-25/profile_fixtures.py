"""Prospective acceptance witnesses; not production validation or live evidence."""
import copy
import json
import math
from pathlib import Path
from preservation_design import exact

ROOT=Path(__file__).resolve().parent


def bounds(k,n,t):return exact.lower(k,n,t),exact.upper(k,n,t)


def evaluate(cells, *, prospective=True, confirmed=True, fresh_replica_pass=True,
             confirmed_loss=False, matched_comparator=True, token_means=(-2,-2,-2),
             unique_worlds=True, all_other_promises=True,
             token_form_means=((-2,-2,-2),(-2,-2,-2))):
    if not prospective:return 'legacy_unchanged'
    if not unique_worlds:return 'invalid_sampling'
    if not cells:return 'unresolved'
    for c in cells:
        if set(c)!={'marked','english','errors'} or not c['errors']:raise ValueError('Missing endpoint family')
        for k,n in [c['marked'],c['english'],*c['errors']]:
            if type(k) is not int or type(n) is not int or not 0<=k<=n or n<1:raise ValueError('Bad counts')
    m=sum(2+len(c['errors']) for c in cells);t=.05/(2*m)
    supports=[];opposes=[]
    for c in cells:
        la,ua=bounds(*c['marked'],t);le,ue=bounds(*c['english'],t)
        e=[bounds(k,n,t) for k,n in c['errors']]
        supports.append(la-ue>=-.05 and min(la,le)>=.9 and all(u<=.05 for l,u in e))
        opposes.append(ua-le<-.05 or min(ua,ue)<.9 or any(l>.05 for l,u in e))
    if confirmed_loss:return 'confirmed_loss_veto'
    if any(opposes):return 'opposes_profile'
    if not confirmed or not fresh_replica_pass:return 'unconfirmed_or_replica_incomplete'
    if not matched_comparator:return 'comparator_mismatch'
    token_rows=[token_means,*token_form_means]
    if not token_form_means or any(len(r)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in r) or max(r)>-1 for r in token_rows):
        return 'no_demonstrated_benefit'
    if not all_other_promises:return 'other_promises_incomplete'
    return 'profile_and_benefit_satisfied_not_ratified' if all(supports) else 'unresolved'


def main():
    good={'marked':(512,512),'english':(512,512),'errors':[(0,512)]}
    bad={'marked':(200,512),'english':(500,512),'errors':[(100,512)]}
    tiny={'marked':(2,2),'english':(2,2),'errors':[(0,2)]}
    cases=[('finite_ceiling_bounds',[good]*4,{},'profile_and_benefit_satisfied_not_ratified'),
           ('two_perfect_answers',[tiny]*4,{},'unresolved'),
           ('one_bad_form',[good,good,bad,tiny],{},'opposes_profile'),
           ('unknown_scope',[good]*4,{'prospective':False},'legacy_unchanged'),
           ('no_confirmation',[good]*4,{'confirmed':False},'unconfirmed_or_replica_incomplete'),
           ('replica_does_not_pass',[good]*4,{'fresh_replica_pass':False},'unconfirmed_or_replica_incomplete'),
           ('small_confirmed_loss',[good]*4,{'confirmed_loss':True},'confirmed_loss_veto'),
           ('allowed_positive_cost',[good]*4,{'token_means':(4,4,4)},'no_demonstrated_benefit'),
           ('one_tokenizer_loses',[good]*4,{'token_means':(-3,-2,1)},'no_demonstrated_benefit'),
           ('roster_subset',[good]*4,{'token_means':(-3,-2)},'no_demonstrated_benefit'),
           ('one_form_costs_more',[good]*4,{'token_form_means':((-2,-2,-2),(1,-2,-2))},'no_demonstrated_benefit'),
           ('nonfinite_token',[good]*4,{'token_means':(-3,float('nan'),-2)},'no_demonstrated_benefit'),
           ('missing_form_costs',[good]*4,{'token_form_means':()},'no_demonstrated_benefit'),
           ('padded_english',[good]*4,{'matched_comparator':False},'comparator_mismatch'),
           ('renamed_template_copies',[good]*4,{'unique_worlds':False},'invalid_sampling'),
           ('unmet_robustness',[good]*4,{'all_other_promises':False},'other_promises_incomplete')]
    rows=[]
    for name,cells,kw,want in cases:
        got=evaluate(cells,**kw);assert got==want,(name,got,want);rows.append({'case':name,'expected':want,'actual':got})
    population=json.loads(next(ROOT.glob('population-*.json')).read_bytes())
    # An opt-in reader routes legacy data untouched. This tests the adapter
    # witness, NOT a server implementation that does not yet exist.
    before=copy.deepcopy(population['proposals'])
    after=[p if evaluate([good],prospective=False)=='legacy_unchanged' else None for p in before]
    assert before==after
    result={'fixtures':rows,'legacy_adapter_projection_equal':len(before),
            'is_production_test':False,'is_unclaimed_verdict_flips_measurement':False}
    (ROOT/'profile-fixtures.json').write_text(json.dumps(result,indent=2)+'\n')
    print(len(rows),'fixtures passed;',len(before),'legacy adapter rows unchanged')


if __name__=='__main__':main()
