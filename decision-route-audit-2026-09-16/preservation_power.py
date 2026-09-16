"""CPU-only prospective design sensitivity, not observed language evidence.

Exact binomial probabilities and conservative Clopper-Pearson marginal bounds.
Assumes independent sampled world units and independent disjoint arms WITHIN a
reader/form comparison. No independence assumption between endpoint tests is
needed for the reported family power lower bound. Template clustering, provider
faults and the actual frozen hash allocation can invalidate this simple model.
"""
from functools import lru_cache
import json
import math
from pathlib import Path


def cdf(k, n, p):
    if k<0:return 0.0
    if k>=n or p==0:return 1.0
    if p==1:return 0.0
    if k>=n*p:
        return max(0.0,1-cdf(n-k-1,n,1-p))
    # Left tail: start at its largest term and recurse down. This avoids the
    # underflow of starting at P(X=0) in large samples.
    term=math.exp(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)
                  +k*math.log(p)+(n-k)*math.log1p(-p))
    terms=[term]
    for j in range(k,0,-1):
        term*=j/(n-j+1)*(1-p)/p
        terms.append(term)
        if term<terms[0]*1e-16:break
    return min(1.0,math.fsum(terms))


@lru_cache(maxsize=None)
def lower(k,n,tail):
    if not (0<=k<=n and n>0 and 0<tail<.5):raise ValueError('invalid marginal')
    if k==0:return 0.0
    if k==n:return tail**(1/n)
    # Invert the failure count's CDF, avoiding subtraction close to one.
    failures=n-k
    lo,hi=0.0,1.0
    for _ in range(48):
        p=(lo+hi)/2
        if cdf(failures,n,p)>tail:lo=p
        else:hi=p
    return 1-(lo+hi)/2


def upper(k,n,tail):return 1-lower(n-k,n,tail)


def distribution(n,p):
    if p==0:return [1.0]+[0.0]*n
    if p==1:return [0.0]*n+[1.0]
    a=[math.exp(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)
                +k*math.log(p)+(n-k)*math.log1p(-p)) for k in range(n+1)]
    assert abs(math.fsum(a)-1)<1e-9
    return a


def first_success(n,predicate):
    lo,hi=0,n+1
    while lo<hi:
        middle=(lo+hi)//2
        if middle<=n and predicate(middle):hi=middle
        else:lo=middle+1
    return lo


def lower_pass_power(n,p,floor,tail):
    critical=first_success(n,lambda k:lower(k,n,tail)>=floor)
    return {'critical_successes':critical,'power':cdf(n-critical,n,1-p)}


def upper_pass_power(n,p,cap,tail):
    q=lower_pass_power(n,1-p,1-cap,tail)
    return {'maximum_events':n-q['critical_successes'],'power':q['power']}


def ni_power(n,pa,pe,tail,margin=.05):
    a=distribution(n,pa);e=distribution(n,pe)
    survival=[0.0]*(n+2)
    for k in range(n,-1,-1):survival[k]=survival[k+1]+a[k]
    terms=[];omitted=[]
    for ke,prob in enumerate(e):
        if prob<1e-14:
            omitted.append(prob);continue
        ue=upper(ke,n,tail)
        ka=first_success(n,lambda k:lower(k,n,tail)-ue>=-margin)
        terms.append(prob*survival[ka])
    power=math.fsum(terms);error=math.fsum(omitted)
    assert -1e-9<=power<=1+1e-9
    return {'power_lower':max(0,min(1,power)),
            'power_upper':max(0,min(1,power+error)),
            'omitted_probability_mass':error}


def verify():
    assert abs(lower(4,20,.05)-.071354)<1e-6
    assert abs(upper(4,20,.05)-.401029)<1e-6
    for n in (1,8,59,144):
        assert math.isclose(upper(0,n,.05),1-.05**(1/n))
    # Compare recurrence with a separately expressed direct binomial summation.
    for n in (3,9,20):
        for p in (.01,.17,.5,.83,.99):
            for k in range(n):
                direct=sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k+1))
                assert abs(cdf(k,n,p)-direct)<1e-11
    for n in (1,7,19):
        for k in range(n+1):
            for tail in (.025,.05/60):
                assert 0<=lower(k,n,tail)<=k/n<=upper(k,n,tail)<=1
    # Brute-force small-N comparison checks the threshold enumeration.
    n=7;pa=.87;pe=.90;tail=.025;margin=.7
    a=distribution(n,pa);e=distribution(n,pe)
    direct=sum(a[ka]*e[ke] for ka in range(n+1) for ke in range(n+1)
               if lower(ka,n,tail)-upper(ke,n,tail)>=-margin)
    assert abs(ni_power(n,pa,pe,tail,margin)['power_lower']-direct)<1e-12
    # For a boundary null, false NI acceptance is bounded by the two marginal
    # tail errors; this is a check, not a substitute for the union-bound proof.
    for n in (20,40):
        assert ni_power(n,.9,.95,.025)['power_upper']<=.05+1e-10


def main():
    verify()
    rows=[]
    methods={'simultaneous_60':(.05/60,.05/60),'conjunction_iut':(.025,.05)}
    for method,(delta_tail,endpoint_tail) in methods.items():
        for pa,pe in ((.95,.95),(.94,.96),(.90,.95)):
            for n in (256,512,1024,2048,4096):
                ni=ni_power(n,pa,pe,delta_tail)
                fa=lower_pass_power(n,pa,.9,endpoint_tail)
                fe=lower_pass_power(n,pe,.9,endpoint_tail)
                unsafe=upper_pass_power(n,.01,.05,endpoint_tail)
                nonclaim=upper_pass_power(n,.01,.05,endpoint_tail)
                control=lower_pass_power(n,.95,.90,endpoint_tail)
                # 4 NI, 8 accuracy-floor, 4 unsafe, 20 nonclaim and 20 positive
                # control tests. Union bound on at least one failed test.
                fail_sum=(4*(1-ni['power_lower'])+4*(1-fa['power'])+4*(1-fe['power'])
                          +4*(1-unsafe['power'])+20*(1-nonclaim['power'])
                          +20*(1-control['power']))
                joint_lower=max(0,1-fail_sum)
                joint_upper=min(ni['power_upper'],fa['power'],fe['power'],unsafe['power'],nonclaim['power'],control['power'])
                row={'method':method,'n_per_arm_per_reader_form':n,'assumed_marked_accuracy':pa,
                     'assumed_english_accuracy':pe,'assumed_unsafe_or_nonclaim_rate':.01,
                     'assumed_positive_control_accuracy':.95,'ni':ni,'marked_floor':fa,
                     'english_floor':fe,'unsafe_cap':unsafe,'nonclaim_cap':nonclaim,
                     'positive_control_floor':control,'all_required_power_lower':joint_lower,
                     'all_required_power_upper':joint_upper,
                     'main_target_calls_original_plus_replication':16*n,
                     'ten_nonclaim_and_ten_control_strata_calls_original_plus_replication':160*n,
                     'total_conditional_target_calls_original_plus_replication':176*n}
                rows.append(row)
                print(json.dumps({'method':method,'n':n,'pa':pa,'pe':pe,'ni_power':round(ni['power_lower'],5),
                                  'joint_lower':round(joint_lower,5),'joint_upper':round(joint_upper,5)}),flush=True)
    auxiliary=[]
    for method,(_,tail) in methods.items():
        for n in (128,256,384,512,768,1024):
            auxiliary.append({'method':method,'n_per_auxiliary_arm_reader_form':n,
                              'cap':upper_pass_power(n,.01,.05,tail),
                              'positive_control':lower_pass_power(n,.95,.90,tail)})
    # Illustrate cheaper predeclared auxiliary allocations instead of blindly
    # giving every auxiliary endpoint the main-comparison denominator.
    budgets=[]
    for method,main_n,aux_n in (('conjunction_iut',1024,768),('simultaneous_60',2048,1024)):
        core=next(r for r in rows if r['method']==method and r['n_per_arm_per_reader_form']==main_n
                  and r['assumed_marked_accuracy']==.95 and r['assumed_english_accuracy']==.95)
        aux=next(r for r in auxiliary if r['method']==method and r['n_per_auxiliary_arm_reader_form']==aux_n)
        fail_sum=(4*(1-core['ni']['power_lower'])+4*(1-core['marked_floor']['power'])
                  +4*(1-core['english_floor']['power'])+4*(1-core['unsafe_cap']['power'])
                  +20*(1-aux['cap']['power'])+20*(1-aux['positive_control']['power']))
        per_run_calls=8*main_n+80*aux_n
        budgets.append({'method':method,'main_n':main_n,'auxiliary_n':aux_n,
                        'single_study_all_required_power_lower':max(0,1-fail_sum),
                        'both_studies_all_required_power_lower':max(0,1-2*fail_sum),
                        'per_run_target_calls':per_run_calls,
                        'original_plus_replication_target_calls':2*per_run_calls,
                        'calibration_qualification_and_bare_descriptive_calls_not_included':True,
                        'not_a_formal_settlement_agreement_power_calculation':True})
        # A separately reviewable instrument could expose all five nonclaim
        # dimensions in each main record, and all positive-control dimensions
        # in each control record. Correlated endpoints are allowed, but every
        # dimension must actually be elicited/scored; this is not five cloned
        # copies of one score or an already validated instrument.
        shared_fail=(4*(1-core['ni']['power_lower'])+4*(1-core['marked_floor']['power'])
                     +4*(1-core['english_floor']['power'])+4*(1-core['unsafe_cap']['power'])
                     +20*(1-core['nonclaim_cap']['power'])+20*(1-aux['positive_control']['power']))
        budgets[-1]['unvalidated_shared_record_alternative']={
            'single_study_all_required_power_lower':max(0,1-shared_fail),
            'both_studies_all_required_power_lower':max(0,1-2*shared_fail),
            'per_run_target_calls':8*(main_n+aux_n),
            'original_plus_replication_target_calls':16*(main_n+aux_n),
            'requires_independent_instrument_and_scoring_review':True,
            'not_permission_to_count_one_answer_as_unobserved_multiple_successes':True}
    report={'kind':'prospective-independent-binomial-design-sensitivity-v1','model_calls':0,
            'tests':'passed','margin_pp':5,'floor':.90,'cap':.05,'reader_form_cells':4,
            'hypothetical_n_not_selected':True,'study_is_not_authorized_or_preregistered':True,
            'per_reader_pass_witness_is_stronger_than_author_pooled_per_form_claim':True,
            'conjunction_iut_is_not_a_simultaneous_confidence_interval_claim':True,
            'assumptions':'Independent sampled Bernoulli world units within each arm; disjoint independent arms. Between-reader and between-endpoint dependence permitted for union-bound power bounds. Equal fixed denominators are hypothetical, not the official hash allocation. Nonclaim and control strata use separate two-arm comparisons at the same n in this deliberately full-cost upper-budget scenario. Actual reduced auxiliary denominators require separate planning.',
            'rows':rows,'auxiliary_sensitivity':auxiliary,'hypothetical_split_budget_examples':budgets}
    Path(__file__).with_name('preservation-power.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
