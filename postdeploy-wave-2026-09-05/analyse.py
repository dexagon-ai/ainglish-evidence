"""Frozen report-only analysis: fixed readers, base-frame clusters, every condition."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parent
ORDER=['mean.careful','mean.practical','mean.consequences','quantity.cold','quantity.reference','choice.cold','choice.reference']
def estimate(rows,conditions):
 bins=defaultdict(list)
 for r in rows:bins[r['condition'],r['arm']].append(r['correct'])
 if any(not bins[c,a] for c in conditions for a in ['english','ainglish']):return None
 arms={a:100*sum(sum(bins[c,a])/len(bins[c,a]) for c in conditions)/len(conditions) for a in ['english','ainglish']}
 return dict(arms,delta_pp=arms['ainglish']-arms['english'])
def interval(rows):
 conditions=sorted({r['condition'] for r in rows});clusters=defaultdict(list)
 for r in rows:clusters[str(r['cluster'])].append(r)
 keys=sorted(clusters);rng=random.Random(2026090583)
 draws=[estimate([r for k in rng.choices(keys,k=len(keys)) for r in clusters[k]],conditions) for _ in range(2000)]
 lost=sum(r is None for r in draws)
 def quantile(vals,q):
  v=sorted(vals);x=q*(len(v)-1);i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
 return {'point':estimate(rows,conditions),'base_frame_clusters':len(keys),'draws':2000,'missing_condition_draws':lost,
  'conditional_95_intervals':None if lost else {k:[quantile([d[k] for d in draws],.025),quantile([d[k] for d in draws],.975)] for k in draws[0]}}
def read(name):
 items={r['id']:r for r in json.loads((ROOT/'frozen'/f'{name}.items.json').read_text())}
 path=ROOT/(name+'.calls.jsonl');calls=[json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
 rows=[];seen=set();bad=[];errors=defaultdict(Counter)
 for call in calls:
  r=items[call['item_id']];s=r['strata'];key=call['reader'],r['id'],call['arm']
  assert key not in seen;seen.add(key)
  if call.get('exception_type') or call.get('absent_reason') or call.get('answer') not in r['options']:
   bad.append(call);continue
  if r.get('calibration'):continue
  answer=s['answer_options'][call['answer']];gold=s['semantic_gold']
  rows.append({'item':r['id'],'reader':call['reader'],'arm':call['arm'],'condition':r['settlement_stratum'],
   'cluster':s['frame_cluster'],'form':s['form'],'probe':s.get('probe',s.get('condition')),'correct':int(answer==gold)})
  if name in ['mean.careful','mean.practical']:
   guessed=answer.split('; ');target=gold.split('; ')
   errors[call['arm']]['statistic_confusion']+=guessed[0]!=target[0]
   errors[call['arm']]['population_binding_error']+=guessed[1]!=target[1]
 expected=2*sum(not r.get('calibration') for r in items.values())
 out={'calls_retained':len(calls),'scientific_cells':len(rows),'invalid_cells':len(bad),'first_fault':bad[0] if bad else None,
      'complete':(ROOT/(name+'.result.json')).exists() and len(rows)==expected and not bad,
      'semantic_gold_frequencies':dict(Counter(r['strata']['semantic_gold'] for r in items.values() if not r.get('calibration')))}
 if not out['complete']:out['boundary']='No complete estimate; retain first abort/partial result. No imputation or retry.';return out,[]
 out['overall']=interval(rows)
 out['conditions']={v:interval([r for r in rows if r['condition']==v]) for v in sorted({r['condition'] for r in rows})}
 for field in ['reader','form','probe']:
  out[field]={v:estimate([r for r in rows if r[field]==v],sorted({r['condition'] for r in rows if r[field]==v})) for v in sorted({r[field] for r in rows if r[field] is not None})}
 out['error_counts_can_overlap']=dict(errors)
 out['every_condition_clears_report_only_minus5_margin']=all(
   x['conditional_95_intervals'] and x['conditional_95_intervals']['delta_pp'][0]>=-5 for x in out['conditions'].values())
 filed=json.loads((ROOT/(name+'.result.json')).read_text());out['filed']= {k:filed.get(k) for k in ['value','value_lo','value_hi','arms','attempt_id']}
 assert abs(filed['value']-out['overall']['point']['delta_pp'])<.03
 return out,rows
def main():
 reports={};rows={}
 for n in ORDER:reports[n],rows[n]=read(n)
 paired={}
 for left,right in [('mean.careful','mean.practical'),('quantity.cold','quantity.reference'),('choice.cold','choice.reference')]:
  if not rows[left] or not rows[right]:paired[left+' → '+right]={'available':False};continue
  assert {(r['item'],r['reader'],r['arm']) for r in rows[left]}=={(r['item'],r['reader'],r['arm']) for r in rows[right]}
  a=reports[left]['overall']['point'];b=reports[right]['overall']['point']
  paired[left+' → '+right]={'available':True,'second_minus_first':{k:b[k]-a[k] for k in a},
    'boundary':'Matched fixed-case contrast, not independent replication, not training the weights.'}
 output={'report_only':True,'studies':reports,'matched_comparisons':paired,
   'interval_scope':'Authored base-frame resampling, fixed reader roster; no human/all-model population inference.'}
 with (ROOT/'analysis.json').open('x') as f:json.dump(output,f,indent=2);f.write('\n')
 print(json.dumps({n:{'complete':r['complete'],'point':r.get('overall',{}).get('point')} for n,r in reports.items()},indent=2))
if __name__=='__main__':main()
