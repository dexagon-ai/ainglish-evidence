"""Independent arithmetic/assignment/meaning-key checks; no tokenizers or readers."""
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def validate():
 index=json.loads((ROOT/'frozen/design-index.json').read_text());summary={}
 populations=json.loads((ROOT/'frozen/populations.json').read_text());studies={}
 for name,design in index.items():
  items=json.loads((ROOT/'frozen'/f'{name}.items.json').read_text());studies[name]=items
  assert hashlib.sha256(canonical(items)).hexdigest()==design['items_sha256']
  assert len({r['id'] for r in items})==len(items)
  assert len({(r['english'],r['ainglish'],r['question']) for r in items})==len(items)
  real=[r for r in items if not r.get('calibration')]
  assert len(real)==design['real_items'] and len(items)-len(real)==8
  for r in items:
   assert r['answer'] in r['options'] and all(len(o)==1 for o in r['options'])
   s=r['strata'];gold=s['semantic_gold'];assert s['answer_options'][r['answer']]==gold
   if r.get('calibration'):
    assert r['ainglish'].startswith(gold+', not ')
    assert not any(x in r['english']+r['ainglish'] for x in ['mean-of','median-of','set-to(',
      'adjust-by(','same-for-all(','may-vary-across(','from-now-on','this-once'])
    continue
   if name.startswith('mean'):
    data=sorted(Fraction(x) for x in populations[s['target_ref']]['values']);n=len(data)
    centre=sum(data)/n if s['form']=='mean-of' else (data[(n-1)//2]+data[n//2])/2
    assert centre==Fraction(s['reported_value'])
    assert s['target_ref']!=s['other_ref'] and s['other_ref'] in r['english']
    if name=='mean.consequences':
     expected={'above-most':sum(x<centre for x in data)*2>n,'observed-value':centre in data,
               'wider-population':False,'exact-recheck':True}[s['probe']]
     assert gold==('yes' if expected else 'no')
    else:assert gold==('sum/count' if s['form']=='mean-of' else 'sorted middle')+'; '+s['target_ref']
   elif name.startswith('quantity'):
    before=s['old']+(s['first'] if s['condition']=='ordered' else 0)
    result=s['operand'] if s['form']=='set-to' else None if s['condition']=='unknown' else before+s['operand']
    assert result==s['expected']
    assert gold==('not determined' if result is None else f'{result} {s["unit"]}')
   elif name.startswith('choice'):
    # Enumerate the whole two-value cube, not the generator's per-member product.
    allowed=[assignment for assignment in itertools.product(s['values'],repeat=len(s['members']))
     if all(v in s['eligibility'][m] for m,v in zip(s['members'],assignment))
     and (s['form']=='may-vary-across' or all(v==assignment[0] for v in assignment))]
    assert len(allowed)==s['valid_count']
    expected=(tuple(s['candidate']) in allowed if s['probe']=='admissibility' else bool(allowed)
       if s['probe']=='feasibility' else any(len(set(x))>1 for x in allowed))
    assert gold==('yes' if expected else 'no')
   elif name.startswith('instruction'):
    expected=s['context']=='current' or (s['form']=='from-now-on' and
      s['context'] not in ['unrelated-kind','revoked','explicit-project-limit'])
    assert s['expected_applies']==expected and gold==('yes' if expected else 'no')
  for condition in design['strata']:
   subset=[r for r in real if r['settlement_stratum']==condition]
   positions=Counter(r['answer'] for r in subset)
   assert len(positions)==len(subset[0]['options']) and max(positions.values())-min(positions.values())<=1
  summary[name]={'items':len(real),'semantic_answer_counts':dict(Counter(r['strata']['semantic_gold'] for r in real)),
                 'conditions':len(design['strata']),'passed':True}
 for a,b in [('mean.careful','mean.practical'),('quantity.cold','quantity.reference'),('choice.cold','choice.reference')]:
  left=[r for r in studies[a] if not r.get('calibration')];right=[r for r in studies[b] if not r.get('calibration')]
  for x,y in zip(left,right):
   assert all(x[k]==y[k] for k in ['id','question','answer','options','strata'])
   if a.startswith('mean'):assert x['ainglish']==y['ainglish'] and x['english']!=y['english']
   else:
    for arm in ['english','ainglish']:assert y[arm].endswith(x[arm]) and y[arm]!=x[arm]
 guides=json.loads((ROOT/'frozen/guides.json').read_text())
 budgets={name:{arm:len(text.split()) for arm,text in guide.items()} for name,guide in guides.items()}
 assert all(n<=50 for v in budgets.values() for n in v.values()),'Common maximum instruction budget is 50 words per arm'
 prior=set()
 for folder in ['next-wave-2026-09-05','progression-studies-2026-09-05','brief-reference-transfer-2026-09-05']:
  for path in (ROOT.parent/folder).rglob('*.items.json'):
   rows=json.loads(path.read_text())
   for row in rows if isinstance(rows,list) else []:
    if all(k in row for k in ['english','ainglish','question']):prior.add(tuple(row[k] for k in ['english','ainglish','question']))
 for name,rows in studies.items():
  assert not prior.intersection(tuple(r[k] for k in ['english','ainglish','question']) for r in rows if not r.get('calibration'))
 return {'studies':summary,'instruction_word_counts':budgets,'instruction_budget_per_arm':50,
         'prior_complete_items_checked':len(prior),'reader_calls':0,'tokenizer_calls':0,
         'limitations':['Fixed authored frames, not randomly sampled human prose.',
          'Equal output positions do not imply semantic class balance; per-condition absolute accuracy must be shown.',
          'Same maximum instruction word budget, not asserted equal native-token count.',
          'Instruction scope remains design-only until author semantic resolution.']}
if __name__=='__main__':
 result=validate()
 with (ROOT/'design-audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:result[k] for k in ['instruction_word_counts','prior_complete_items_checked','limitations']},indent=2))
