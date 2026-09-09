"""CPU-only, known-truth comparison of different questions; no Ainglish writes."""
import hashlib,json,math,subprocess
from pathlib import Path
from statistics import NormalDist
import numpy as np

ROOT=Path(__file__).resolve().parent
PLAN=ROOT/'bounded-prerequisite-plan.json'

def upper(mean,n,span,cells,alpha):
 return mean+span*math.sqrt(math.log(cells/alpha)/(2*n))

def wilson(k,n):
 p=k/n;z=NormalDist().inv_cdf(.975);d=1+z*z/n
 mid=(p+z*z/(2*n))/d;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return [max(0.,mid-half),min(1.,mid+half)]

def result(mask):
 k=int(mask.sum());n=len(mask);p=k/n
 return {'passes':k,'trials':n,'rate':p,'monte_carlo_se':math.sqrt(p*(1-p)/n),'wilson_95':wilson(k,n)}

def selftest():
 assert upper(2.,32,8.,12,.05)==upper(2.,32,8.,12,.05)
 assert upper(2.,32*64,8.,12,.05)<upper(2.,32,8.,12,.05)
 assert upper(2.,512,8.,12,.05)<upper(2.,8,8.,12,.05)
 assert upper(2.,32,8.,12,.05)>upper(2.,32,8.,1,.05)
 assert wilson(0,5000)[0]==0 and wilson(5000,5000)[1]==1

def run():
 selftest();plan=json.loads(PLAN.read_text());rng=np.random.default_rng(plan['seed'])
 repeats=plan['replicates_per_condition'];k=plan['cells'];alpha=plan['familywise_alpha'];bound=plan['cell_mean_allowance']
 rows=[]
 for family in plan['families']:
  span=8 if family=='two_point_0_8' else 12
  for profile,mu_list in plan['true_cell_means'].items():
   mu=np.array(mu_list)
   for n in plan['independent_clusters']:
    # Same cluster draw across named cells: multiplicity control must not assume
    # tokenizers/forms are independent. Studies and clusters ARE independent here.
    u=rng.random((repeats,2,n,1))
    if family=='two_point_0_8':x=(u<mu/8)*8.
    else:
     mid_p=(mu-.05*12)/3
     assert np.all(mid_p>=0) and np.all(mid_p<=.95)
     x=np.where(u<.05,12.,np.where(u<(.05+mid_p),3.,0.))
    means=x.mean(axis=2);se=x.std(axis=2,ddof=1)/math.sqrt(n)
    heads=means.max(axis=2)
    agrees=np.abs(heads[:,0]-heads[:,1])<=np.maximum(.02,.1*np.abs(heads[:,0]))
    sample_pass=np.all(means<=bound,axis=(1,2))
    # K*2 union-bound allocation covers every named cell in both frozen studies.
    honest_upper=upper(means,n,span,2*k,alpha)
    normal_upper=means+NormalDist().inv_cdf(1-alpha/(2*k))*se
    for duplicate in plan['duplicate_renderings_per_cluster']:
     wrong_upper=upper(means,n*duplicate,span,2*k,alpha)
     methods={'sample_bound_only':sample_pass,'point_agreement_only':agrees,
       'point_and_sample_bound':agrees&sample_pass,
       'naive_duplicate_hoeffding':np.all(wrong_upper<=bound,axis=(1,2)),
       'cluster_normal_approximation':np.all(normal_upper<=bound,axis=(1,2)),
       'two_study_cluster_hoeffding':np.all(honest_upper<=bound,axis=(1,2))}
     coverage={'naive_duplicate_hoeffding':np.all(wrong_upper>=mu,axis=(1,2)),
       'cluster_normal_approximation':np.all(normal_upper>=mu,axis=(1,2)),
       'two_study_cluster_hoeffding':np.all(honest_upper>=mu,axis=(1,2))}
     rows.append({'family':family,'profile':profile,'true_means':mu_list,'support':[0,span],
       'independent_clusters_per_study':n,'duplicate_renderings_per_cluster':duplicate,
       'all_true_means_within_allowance':bool(np.all(mu<=bound)),
       'rule_results':{name:result(mask)|({'simultaneous_coverage':result(coverage[name])} if name in coverage else {}) for name,mask in methods.items()}})
    print('SIMULATED',family,profile,n,flush=True)
 out={'kind':'ainglish.report-only-bounded-prerequisite-simulation.v1',
  'plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),'seed':plan['seed'],
  'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip(),
  'numpy_version':np.__version__,'conditions':rows,'ainglish_writes':0,'model_calls':0,
  'boundary':plan['prospective_boundary']}
 with (ROOT/'bounded-prerequisite-results.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False)

if __name__=='__main__':run()
