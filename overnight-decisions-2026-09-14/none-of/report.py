"""Preregistered supplementary reporting. Standard library only; never calls a reader."""
from collections import defaultdict
import json
import math
from pathlib import Path
import random
import sys

ALPHA=.00625

def cdf(k,n,p):
 if p<=0:return 1.0
 if p>=1:return float(k>=n)
 logs=[math.lgamma(n+1)-math.lgamma(j+1)-math.lgamma(n-j+1)+j*math.log(p)+(n-j)*math.log1p(-p) for j in range(k+1)]
 return min(1.,math.fsum(math.exp(v) for v in logs))

def solve(k,n,target):
 lo,hi=0.,1.
 for _ in range(70):
  p=(lo+hi)/2
  if cdf(k,n,p)>target:lo=p
  else:hi=p
 return (lo+hi)/2

def bounds(k,n,alpha=ALPHA):
 if not 0<=k<=n or n<1:raise ValueError('Need a nonempty binomial sample')
 return (0. if k==0 else solve(k-1,n,1-alpha),1. if k==n else solve(k,n,alpha))

def count_rows(rows):
 cells=defaultdict(lambda:[0,0])
 for row in rows:
  if row['arm'] not in ['ainglish','english']:raise ValueError('Unknown arm')
  ok=row['answer']==row['expected']
  assert ok==row['correct']
  cell=cells[(row['reader'],row['strata']['form'],row['arm'])]
  cell[0]+=ok;cell[1]+=1
 return dict(cells)

def clusters(rows,draws=2000):
 groups=defaultdict(list)
 for row in rows:groups[row['strata']['predicate_family']].append(row)
 keys=sorted(groups);group_counts={k:count_rows(v) for k,v in groups.items()}
 strata=sorted({(r['reader'],r['strata']['form']) for r in rows})
 samples={s:[] for s in strata};undefined={s:0 for s in strata};rng=random.Random(2026091409)
 for _ in range(draws):
  counts=defaultdict(lambda:[0,0])
  for k in rng.choices(keys,k=len(keys)):
   for cell,(correct,total) in group_counts[k].items():
    counts[cell][0]+=correct;counts[cell][1]+=total
  for s in strata:
   a=counts[(*s,'ainglish')];e=counts[(*s,'english')]
   if not a[1] or not e[1]:undefined[s]+=1
   else:samples[s].append(a[0]/a[1]-e[0]/e[1])
 out=[]
 for s in strata:
  v=sorted(samples[s]);missing=undefined[s]
  out.append({'reader':s[0],'form':s[1],'undefined_draws':missing,
   'interval':None if missing or not v else [v[int(.025*(len(v)-1))],v[int(.975*(len(v)-1))]]})
 return {'family_count':len(keys),'draws':draws,'seed':2026091409,'per_reader_form':out}

def analyse(rows):
 counts=count_rows(rows);out=[]
 for reader,form in sorted({key[:2] for key in counts}):
  a=counts[(reader,form,'ainglish')];e=counts[(reader,form,'english')]
  ab=bounds(*a);eb=bounds(*e);diff=a[0]/a[1]-e[0]/e[1]
  lower=ab[0]-eb[1]
  out.append({'reader':reader,'form':form,'ainglish_correct_total':a,'english_correct_total':e,
   'ainglish_bounds':ab,'english_bounds':eb,'delta_pp':100*diff,
   'conditional_lower_difference_pp':100*lower,'conditional_5pp_preservation':lower>=-.05})
 slices=defaultdict(lambda:[0,0])
 for row in rows:
  for axis in ['domain','set_size','coverage','probe']:
   key=(row['reader'],row['strata']['form'],axis,str(row['strata'][axis]),row['arm'])
   slices[key][0]+=row['correct'];slices[key][1]+=1
 return {'kind':'supplementary-not-official-replacement','target_cells':len(rows),'alpha_per_bound':ALPHA,
  'per_reader_form':out,'slices':[{'reader':k[0],'form':k[1],'axis':k[2],'value':k[3],'arm':k[4],
   'correct':v[0],'total':v[1]} for k,v in sorted(slices.items())],
  'frame_cluster_sensitivity':clusters(rows),
  'boundary':'Conditional binomial and convenience-frame bootstrap sensitivity, not proof of independent sampling, human performance, reader-population generalisation or ratification. Preserve the unchanged official result.'}

def main():
 path=Path(sys.argv[1]);doc=json.loads(path.read_text());result=analyse(doc['rows'])
 output=Path(sys.argv[2]);output.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'target_cells':result['target_cells'],'per_reader_form':result['per_reader_form']},indent=2))

if __name__=='__main__':main()
