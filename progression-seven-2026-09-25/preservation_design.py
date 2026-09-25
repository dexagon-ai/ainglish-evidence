"""CPU-only design analysis, NOT language evidence or an implemented live protocol.

Reuses the independently checked exact-binomial implementation. Disjoint IID
worlds per arm; cases sharing a template/event must not inflate n. A paired
discordance bound is shown separately and is NOT the official allocation.
"""
from bisect import bisect_left
from functools import lru_cache
import importlib.util
import json
import math
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exact_bounds',ROOT.parent/'decision-route-audit-2026-09-16/preservation_power.py')
exact=importlib.util.module_from_spec(spec);spec.loader.exec_module(exact)


def clearance(ka,na,ke,ne,unsafe,nu,alpha=.05,margin=.05,floor=.90,cap=.05):
    # Each decision is an intersection-union test. The NI inequality uses two
    # one-sided bounds at alpha/2 via Bonferroni; other endpoints use alpha.
    # This is NOT a joint 95% confidence band over every reported endpoint.
    return min(exact.lower(ka,na,alpha/2)-exact.upper(ke,ne,alpha/2)+margin,
               exact.lower(ka,na,alpha)-floor,
               exact.lower(ke,ne,alpha)-floor,
               cap-exact.upper(unsafe,nu,alpha))


@lru_cache(maxsize=None)
def sampler(n,p):
    c=[];s=0
    for v in exact.distribution(n,p):s+=v;c.append(s)
    c[-1]=1
    return c


def simulate(n,pa,pe,error,cluster_size,reps,seed):
    rng=random.Random(seed);groups=n//cluster_size;assert groups*cluster_size==n
    counts={'naive_independent_rows':0,'honest_one_per_identical_cluster':0,'point_only':0}
    for _ in range(reps):
        a=bisect_left(sampler(groups,pa),rng.random())
        e=bisect_left(sampler(groups,pe),rng.random())
        bad=bisect_left(sampler(groups,error),rng.random())
        counts['point_only']+=a/groups-e/groups>=-.05 and min(a,e)/groups>=.90 and bad/groups<=.05
        counts['naive_independent_rows']+=clearance(a*cluster_size,n,e*cluster_size,n,bad*cluster_size,n)>0
        counts['honest_one_per_identical_cluster']+=clearance(a,groups,e,groups,bad,groups)>0
    return {'rows_per_arm':n,'independent_clusters_per_arm':groups,'cluster_size':cluster_size,
            'true_marked_accuracy':pa,'true_english_accuracy':pe,'true_error_rate':error,'replicates':reps,
            'acceptance_rates':{k:v/reps for k,v in counts.items()},'max_mc_standard_error':.5/math.sqrt(reps),
            'model':'IID Bernoulli clusters; within-cluster responses copied exactly; arms and auxiliary endpoint independently sampled'}


def main():
    exact.verify()
    planning=[]
    for n in (16,32,64,128,256,512,1024):
        planning.append({'n_per_arm_per_reader_stratum':n,
            'best_case_all_correct_clearance_pp':100*clearance(n,n,n,n,0,n),
            'all_correct_marked_accuracy_lower':exact.lower(n,n,.05),
            'zero_error_upper':exact.upper(0,n,.05),
            'ni_power_if_both_accuracies_95pct':exact.ni_power(n,.95,.95,.025),
            'accuracy_floor_power_if_95pct':exact.lower_pass_power(n,.95,.90,.05),
            'error_cap_power_if_1pct':exact.upper_pass_power(n,.01,.05,.05),
            'minimum_core_reader_calls_one_original_two_readers_two_strata':8*n,
            'original_plus_fresh_replication_core_calls':16*n,
            'auxiliary_controls_and_qualification_excluded_from_cost':True})
    simulations=[]
    for pa,pe,error in ((.95,.95,.01),(.90,.95,.01),(.89,.95,.01),(.95,.95,.06)):
        for n,c in ((128,1),(128,8),(512,1),(512,8)):
            simulations.append(simulate(n,pa,pe,error,c,5000,2026092500+len(simulations)))
    paired=[]
    for n in (32,64,128,256):
        # For same-world paired observations delta=p(A-only correct)-p(E-only correct).
        # Bonferroni marginal exact bounds remain valid despite within-pair dependence.
        paired.append({'independent_pairs':n,'zero_discordance_lower_pp':-100*exact.upper(0,n,.025),
                       'not_the_official_disjoint_arm_panel':True})
    simultaneous=[]
    # Draft profile: four reader/form cells, three quantities each, two tails.
    t=.05/24
    for n in (64,128,256,512,1024,2048,4096):
        simultaneous.append({'n_per_arm_per_reader_stratum':n,'marginal_tail':t,
            'best_case_delta_lower_pp':100*(exact.lower(n,n,t)-1),
            'zero_error_upper':exact.upper(0,n,t),
            'ni_power_at_95pct':exact.ni_power(n,.95,.95,t),
            'floor_power_at_95pct':exact.lower_pass_power(n,.95,.9,t),
            'cap_power_at_1pct':exact.upper_pass_power(n,.01,.05,t),
            'warning':'Power for individual endpoints, not the full conjunction or settlement.'})
    report={'kind':'prospective-preservation-design-analysis.v1','seed_family':2026092500,
            'scientific_reader_calls':0,'planning':planning,'simulations':simulations,'paired_diagnostic':paired,
            'conservative_simultaneous_profile':simultaneous,
            'source':'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html',
            'interpretation':'Exact marginal Clopper-Pearson bounds plus union-bound NI construction. Overall pass requires every predeclared endpoint, reader and stratum to pass; no endpoints selected after results. This IUT does not assert simultaneous CI coverage. IID-world and fixed-reader assumptions are essential; finite synthetic convenience banks do not establish a real-world population.',
            'deployment_status':'report-only; neither this script nor a proposed rule changes live gates'}
    (ROOT/'preservation-design.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'planning':planning,'simulations':simulations},indent=2))


if __name__=='__main__':main()
