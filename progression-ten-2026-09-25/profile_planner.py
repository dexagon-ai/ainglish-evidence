"""CPU-only prospective exact-binomial profile witnesses, not a live gate.

The inventory is fixed BEFORE outcomes. Missing endpoints cannot lower M.
The canonical inventory digest is a commitment, not proof of adequate design.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exact',ROOT.parent/'decision-route-audit-2026-09-16/preservation_power.py')
exact=importlib.util.module_from_spec(spec);spec.loader.exec_module(exact)

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def inventory():
 rows=[]
 for reader in ('reader-A','reader-B'):
  for form in ('form-1','form-2'):
   for endpoint in ('accuracy-marked','accuracy-english','semantic-error-one-marked','semantic-error-one-english','semantic-error-two-marked','semantic-error-two-english'):
    rows.append({'id':f'{reader}/{form}/{endpoint}','reader':reader,'form':form,'endpoint':endpoint})
 return {'kind':'prospective-fixed-endpoint-inventory.v1','alpha':.05,'margin':.05,'accuracy_floor':.90,'error_cap':.05,
  'endpoints':rows,'token_forms':['form-1','form-2'],'tokenizers':['cl100k_base','o200k_base','p50k_base'],
  'sampling':'independent world clusters within each endpoint; repeated questions or template copies are not new independent trials'}

def token_benefit(inv,committed_digest,rows):
 if digest(inv)!=committed_digest:return 'inventory_commitment_changed'
 expected={(f,m) for f in ['overall',*inv['token_forms']] for m in inv['tokenizers']}
 keys=[(r['form'],r['tokenizer']) for r in rows]
 if len(keys)!=len(set(keys)) or set(keys)!=expected:return 'incomplete_or_duplicate_token_inventory'
 if any(type(r['mean']) not in (int,float) or not math.isfinite(r['mean']) for r in rows):return 'invalid_token_value'
 return 'compactness_demonstrated' if all(r['mean']<=-1 for r in rows) else 'no_demonstrated_compactness_benefit'

def evaluate(inv,committed_digest,rows):
 if digest(inv)!=committed_digest:return 'inventory_commitment_changed'
 expected={e['id']:e for e in inv['endpoints']}
 if len(expected)!=len(inv['endpoints']) or not expected:return 'invalid_inventory'
 seen=[r['id'] for r in rows]
 if len(set(seen))!=len(seen) or set(seen)!=set(expected):return 'incomplete_or_duplicate_endpoint_inventory'
 cells={};m=len(expected);tail=inv['alpha']/(2*m)
 for row in rows:
  k,n=row['k'],row['n']
  if type(k) is not int or type(n) is not int or not 0<=k<=n or n<1:return 'invalid_counts'
  e=expected[row['id']];cell=cells.setdefault((e['reader'],e['form']),{})
  cell[e['endpoint']]=(exact.lower(k,n,tail),exact.upper(k,n,tail))
 if any(set(c)!={'accuracy-marked','accuracy-english','semantic-error-one-marked','semantic-error-one-english','semantic-error-two-marked','semantic-error-two-english'} for c in cells.values()):return 'incomplete_semantic_design'
 passes=[];opposes=[]
 for c in cells.values():
  am,ae=c['accuracy-marked'],c['accuracy-english']
  errs=[v for k,v in c.items() if k.startswith('semantic-error-')]
  passes.append(am[0]-ae[1]>=-inv['margin'] and min(am[0],ae[0])>=inv['accuracy_floor'] and max(e[1] for e in errs)<=inv['error_cap'])
  opposes.append(am[1]-ae[0]<-inv['margin'] or min(am[1],ae[1])<inv['accuracy_floor'] or max(e[0] for e in errs)>inv['error_cap'])
 return 'opposes_profile' if any(opposes) else 'profile_satisfied' if all(passes) else 'unresolved'

def transition(original=None,replica=None,*,agrees=False,independent=False,token_benefit=False,confirmed_loss=False,other_promises=False,legacy=False):
 if legacy:return 'legacy_unchanged'
 if confirmed_loss:return 'existing_confirmed_loss_veto'
 if original is None:return 'awaiting_original'
 if original!='profile_satisfied':return 'not_ready_original_profile'
 if replica is None:return 'awaiting_fresh_replica'
 if not independent or not agrees:return 'settlement_unresolved'
 if replica!='profile_satisfied':return 'not_ready_replica_profile'
 if not token_benefit:return 'no_demonstrated_compactness_benefit'
 if not other_promises:return 'other_promises_incomplete'
 return 'ready_for_existing_independent_ballot_not_ratified'

def perfect_rows(inv,n):
 return [{'id':e['id'],'k':n if e['endpoint'].startswith('accuracy') else 0,'n':n} for e in inv['endpoints']]

def main():
 exact.verify();inv=inventory();h=digest(inv);good=perfect_rows(inv,512);checks=[]
 def check(name,got,want):
  assert got==want,(name,got,want);checks.append({'name':name,'actual':got})
 check('complete_frozen_inventory',evaluate(inv,h,good),'profile_satisfied')
 check('omit_bad_endpoint_cannot_reduce_M',evaluate(inv,h,good[:-1]),'incomplete_or_duplicate_endpoint_inventory')
 check('duplicate_endpoint',evaluate(inv,h,good+[good[0]]),'incomplete_or_duplicate_endpoint_inventory')
 wrong=copy.deepcopy(good);wrong[-1]['id']='reader-C/form-2/semantic-error-english'
 check('substitute_reader',evaluate(inv,h,wrong),'incomplete_or_duplicate_endpoint_inventory')
 changed=copy.deepcopy(inv);changed['endpoints']=changed['endpoints'][:-1]
 check('rewrite_inventory_afterward',evaluate(changed,h,good[:-1]),'inventory_commitment_changed')
 tiny=perfect_rows(inv,64);check('perfect_but_too_small',evaluate(inv,h,tiny),'unresolved')
 bad=copy.deepcopy(good);bad[0]['k']=200
 check('one_bad_reader_form',evaluate(inv,h,bad),'opposes_profile')
 check('delete_the_harmful_endpoint',evaluate(inv,h,bad[1:]),'incomplete_or_duplicate_endpoint_inventory')
 check('delete_the_whole_harmful_cell',evaluate(inv,h,bad[6:]),'incomplete_or_duplicate_endpoint_inventory')
 errors=copy.deepcopy(good);errors[4]['k']=100
 check('one_semantic_error_endpoint_fails',evaluate(inv,h,errors),'opposes_profile')
 check('delete_the_harmful_second_error_only',evaluate(inv,h,errors[:4]+errors[5:]),'incomplete_or_duplicate_endpoint_inventory')
 invalid=copy.deepcopy(good);invalid[0]['k']=True
 check('bool_is_not_count',evaluate(inv,h,invalid),'invalid_counts')
 tokens=[{'form':f,'tokenizer':m,'mean':-2} for f in ['overall',*inv['token_forms']] for m in inv['tokenizers']]
 check('complete_token_inventory',token_benefit(inv,h,tokens),'compactness_demonstrated')
 tokenbad=copy.deepcopy(tokens);tokenbad[-1]['mean']=3
 check('one_token_form_costs_more',token_benefit(inv,h,tokenbad),'no_demonstrated_compactness_benefit')
 check('delete_harmful_token_form',token_benefit(inv,h,tokenbad[:-1]),'incomplete_or_duplicate_token_inventory')
 check('drop_a_tokenizer_everywhere',token_benefit(inv,h,[r for r in tokens if r['tokenizer']!='p50k_base']),'incomplete_or_duplicate_token_inventory')
 steps=[({},'awaiting_original'),({'original':'profile_satisfied'},'awaiting_fresh_replica'),
  ({'original':'profile_satisfied','replica':'profile_satisfied'},'settlement_unresolved'),
  ({'original':'profile_satisfied','replica':'unresolved','agrees':True,'independent':True},'not_ready_replica_profile'),
  ({'original':'profile_satisfied','replica':'profile_satisfied','agrees':True,'independent':True},'no_demonstrated_compactness_benefit'),
  ({'original':'profile_satisfied','replica':'profile_satisfied','agrees':True,'independent':True,'token_benefit':True},'other_promises_incomplete'),
  ({'original':'profile_satisfied','replica':'profile_satisfied','agrees':True,'independent':True,'token_benefit':True,'other_promises':True},'ready_for_existing_independent_ballot_not_ratified'),
  ({'original':'profile_satisfied','replica':'profile_satisfied','agrees':True,'independent':True,'token_benefit':True,'other_promises':True,'confirmed_loss':True},'existing_confirmed_loss_veto'),
  ({'legacy':True},'legacy_unchanged')]
 for i,(args,want) in enumerate(steps):check(f'prospective_transition_{i}',transition(**args),want)
 floors=[]
 for m in (8,12,16,20,24,40):
  t=.05/(2*m);acc=math.ceil(math.log(t)/math.log(.9));full=math.ceil(math.log(t)/math.log(.95))
  assert exact.lower(full,full,t)-1>=-.05 and exact.lower(full-1,full-1,t)-1<-.05
  floors.append({'M':m,'tail':t,'accuracy_only_perfect_minimum':acc,'full_profile_perfect_minimum':full,
   'accuracy_only_n_cannot_pass_delta':exact.lower(acc,acc,t)-1<-.05,
   'core_calls_two_readers_two_forms_two_arms_one_original':8*full,
   'core_calls_original_and_fresh_replica':16*full,'controls_qualification_and_retries_excluded':True})
 assert next(f for f in floors if f['M']==8)['full_profile_perfect_minimum']==113
 assert next(f for f in floors if f['M']==20)['full_profile_perfect_minimum']==131
 powers=[]
 # Fixed example inventory M=24. Independence of disjoint arms is a planning
 # assumption; no independence among endpoint tests is used by the union bound.
 m=len(inv['endpoints']);t=.05/(2*m)
 for n in (128,256,512,1024,2048):
  ni=exact.ni_power(n,.95,.95,t)
  acc=exact.lower_pass_power(n,.95,.90,t);err=exact.upper_pass_power(n,.01,.05,t)
  fail=4*(1-ni['power_lower'])+8*(1-acc['power'])+16*(1-err['power'])
  powers.append({'n_per_endpoint':n,'assumed_accuracy_both_arms':.95,'assumed_error_rate':.01,
   'NI_pair_power':ni,'accuracy_endpoint_power':acc,'error_endpoint_power':err,
   'one_study_all_conditions_power_lower':max(0,1-fail),
   'one_study_all_conditions_power_upper':min(ni['power_upper'],acc['power'],err['power']),
   'both_studies_all_conditions_power_lower':max(0,1-2*fail),
   'core_calls_original_and_fresh_replica':16*n,
   'excluded_costs':'auxiliary probes/controls, qualification, retries; not settlement agreement power'})
 coverage=[]
 for n in (8,32,128):
  for p in (.01,.05,.5,.9,.95,.99):
   dist=exact.distribution(n,p)
   outside=sum(prob for k,prob in enumerate(dist) if not exact.lower(k,n,t)<=p<=exact.upper(k,n,t))
   assert outside<=2*t+1e-9
   coverage.append({'n':n,'p':p,'marginal_noncoverage':outside,'fixed_M_joint_union_bound':min(1,m*outside)})
 report={'kind':'prospective-profile-planning.v2','live_gate_changes':0,'scientific_reader_calls':0,
  'inventory':inv,'inventory_sha256':h,'fixtures':checks,'all_correct_floors':floors,'power_scenarios':powers,
  'exact_binomial_coverage_checks':coverage,
  'scope':'Computational witnesses, not implemented server behavior, validated language evidence, IID-world certification or a proposal amendment.',
  'proof_boundary':'Each of M two-sided CP intervals fails with probability at most 2t under its fixed IID binomial model. Union bound gives at most 2Mt=0.05, with no independence requirement across endpoints. Clustering within endpoints can invalidate their binomial models. Missing endpoints cannot be silently dropped.',
  'perfect_floor_warning':'Necessary best-case sample floor, not power, budget recommendation, population validation or a guarantee of pass. M=8 omits semantic-error endpoints for a two-reader/two-form design and is an arithmetic illustration only.'}
 (ROOT/'profile-planner.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'fixtures':len(checks),'exact_coverage_checks':len(coverage),'perfect_floors':floors,'scientific_reader_calls':0}))

if __name__=='__main__':main()
