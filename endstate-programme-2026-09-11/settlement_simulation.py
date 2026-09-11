"""Seeded CPU-only synthetic design study; no register rows or rules are changed.

Paired A-minus-E correctness takes values -1,0,+1. The two independent studies
share or differ in a specified population. Repeated blocks model dependence.
Known simulation variances provide an oracle, NOT a deployable interval method.
"""
import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist
import numpy as np

SEED=2026091109
MARGIN_PP=5.0 # illustrative prospective equivalence margin, not Ainglish policy


def draw(rng, repeats, n, cluster, effects):
    if n % cluster:
        raise ValueError('Sample must contain whole dependence blocks')
    effective=n//cluster
    samples=[];variances=[]
    for effect in effects:
        delta=effect/100
        if abs(delta)>.3:raise ValueError('Effect incompatible with fixed 30% discordance')
        counts=rng.multinomial(effective,[(.3+delta)/2,(.3-delta)/2,.7],size=repeats)
        samples.append(100*(counts[:,0]-counts[:,1])/effective)
        variances.append(10000*(.3-delta*delta)/effective)
    return np.stack(samples,axis=1),np.array(variances)


def rate(values):
    p=float(np.mean(values));n=len(values)
    return {'rate':p,'mc_se':math.sqrt(p*(1-p)/n),'simulated_study_pairs':n}


def compare(a,b,va,vb,n):
    diff=np.abs(a-b)
    # This reproduces only the numeric tolerance illustration; the full production
    # contract has other gates, rounding, evidence states and estimators.
    current=np.maximum(.02,.10*np.abs(a))
    naive=np.maximum(current,100/n)
    sd=np.sqrt(va+vb)
    z95=NormalDist().inv_cdf(.975)
    z_equiv=NormalDist().inv_cdf(.95)
    return {
        'numeric_current_all_strata':rate(np.all(diff <= current+1e-12,axis=1)),
        'numeric_one_item_floor_all_strata':rate(np.all(diff <= naive+1e-12,axis=1)),
        'oracle_difference_ci_contains_zero_all_strata':rate(np.all(diff <= z95*sd+1e-12,axis=1)),
        'oracle_equivalence_within_5pp_all_strata':rate(np.all(diff+z_equiv*sd < MARGIN_PP,axis=1)),
        'numeric_current_aggregate_only':rate(np.abs(a.mean(axis=1)-b.mean(axis=1)) <=
              np.maximum(.02,.10*np.abs(a.mean(axis=1)))+1e-12),
    }


def simulate(repeats=20000):
    rng=np.random.default_rng(SEED);rows=[]
    for strata in [1,2,4]:
        for n in [16,32,64,128,512,2048,8192]:
            for cluster in [1,4]:
                for scenario in ['same_population','ten_pp_shift','offsetting_strata']:
                    if scenario=='offsetting_strata' and strata==1:continue
                    original=[5.]*strata;replica=original.copy()
                    if scenario=='ten_pp_shift':replica=[15.]*strata
                    if scenario=='offsetting_strata':replica[:2]=[15.,-5.]
                    a,va=draw(rng,repeats,n,cluster,original)
                    b,vb=draw(rng,repeats,n,cluster,replica)
                    rows.append({'scenario':scenario,'items_per_stratum_per_study':n,
                        'required_strata':strata,'dependence_block':cluster,
                        'independent_blocks_per_stratum':n//cluster,
                        'original_population_pp':original,'replica_population_pp':replica,
                        **compare(a,b,va,vb,n)})
    return {'kind':'synthetic-settlement-design-study.v1','measurement':False,
        'register_writes':0,'seed':SEED,'repeats_per_design':repeats,
        'estimand':'Equal-weight paired binary correctness delta per stratum, in percentage points',
        'margin_pp':MARGIN_PP,'margin_status':'Invented illustration, not recommended default or live rule',
        'uncertainty':'Known-population normal approximation is an oracle design comparison, not an implemented confidence procedure. It is least reliable at small samples.',
        'scope':'Independent study draws, fixed 30% paired discordance, perfect dependence within size-4 blocks. No claim these assumptions fit any live row.',
        'not_equivalent':['Arithmetic lattice','one answer change','statistical uncertainty','practical equivalence margin'],
        'boundaries':['A CI containing zero is not evidence of equivalence or positive benefit.',
            'All required strata matter; aggregate agreement can hide offsetting differences.',
            'Numeric agreement alone does not confer confirmation, clear a veto or ratify anything.',
            'Prospective estimator and sampling changes need governance review; no historical reinterpretation.'],
        'results':rows}


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=20000);a=p.parse_args()
    if a.repeats<1000:raise ValueError('At least 1000 draws required for the report')
    result=simulate(a.repeats)
    with a.out.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps({'designs':len(result['results']),'simulated_study_pairs':len(result['results'])*a.repeats,
                      'seed':SEED,'measurement':False}))


if __name__=='__main__':main()
