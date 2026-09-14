"""Pre-exposure supplementary counts and cluster sensitivity; no reader calls."""
from collections import defaultdict
import json,random,sys
from pathlib import Path

def counts(rows):
 out=defaultdict(lambda:[0,0])
 for r in rows:
  assert r['correct']==(r['answer']==r['expected'])
  v=out[(r['reader'],r['settlement_stratum'],r['arm'])];v[0]+=r['correct'];v[1]+=1
 return dict(out)

def analyse(rows):
 by_frame=defaultdict(list)
 for r in rows:by_frame[r['strata']['family']].append(r)
 frames={k:counts(v) for k,v in by_frame.items()};keys=sorted(frames)
 cells=counts(rows);rs=sorted({k[:2] for k in cells});samples={k:[] for k in rs};undefined={k:0 for k in rs}
 rng=random.Random(2026091421)
 for _ in range(2000):
  c=defaultdict(lambda:[0,0])
  for frame in rng.choices(keys,k=len(keys)):
   for cell,(ok,n) in frames[frame].items():c[cell][0]+=ok;c[cell][1]+=n
  for pair in rs:
   a=c[(*pair,'ainglish')];e=c[(*pair,'english')]
   if not a[1] or not e[1]:undefined[pair]+=1
   else:samples[pair].append(100*(a[0]/a[1]-e[0]/e[1]))
 report=[]
 for pair in rs:
  a=cells[(*pair,'ainglish')];e=cells[(*pair,'english')];v=sorted(samples[pair])
  report.append({'reader':pair[0],'stratum':pair[1],'ainglish_correct_total':a,'english_correct_total':e,
   'delta_pp':100*(a[0]/a[1]-e[0]/e[1]),'undefined_draws':undefined[pair],
   'cluster_interval_pp':None if undefined[pair] or not v else [v[int(.025*(len(v)-1))],v[int(.975*(len(v)-1))]]})
 return {'kind':'supplementary-not-official-replacement','target_cells':len(rows),'frames':len(keys),
  'resamples':2000,'seed':2026091421,'per_reader_stratum':report,
  'boundary':'Authored-frame sensitivity, not independent population sampling. All source strata load-bearing. Official register settlement is not replaced.'}

if __name__=='__main__':
 doc=json.loads(Path(sys.argv[1]).read_text())
 Path(sys.argv[2]).write_text(json.dumps(analyse(doc['rows']),indent=2)+'\n')
