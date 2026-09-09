"""Structural shortcuts are calculations, not reader-performance evidence."""
import re
from collections import defaultdict
from reader_campaign import ROOT,save,load

OUT=ROOT/'outcome-consequence-review'
items=load(OUT/'items.json');groups=defaultdict(list);masked=[]
for r in items:
 prediction='Yes' if r['strata']['question_polarity']=='unsupported' else 'No'
 correct=prediction==r['answer'];groups['all'].append(correct)
 for field in ('form','consequence_family','question_polarity'):groups[field+':'+str(r['strata'][field])].append(correct)
 common,assertion=r['english'].rsplit('Under ',1)
 ref=re.match(r'(D-[0-9a-f]+),',assertion).group(1)
 text=common+f'The writer reports the numeric value {r["strata"]["numeric_instance"]} under {ref}, but the chosen statistic label is not supplied.'
 masked.append({'id':r['id'],'masked_text':text,'question':r['question'],'options':r['options'],
  'original_task_key':r['answer'],'strata':r['strata'],
  'warning':'Information-ablation instrument only. This key belongs to the original labelled assertion, not a claim that missing statistic information is entailed by the masked text. Never file this as a meaning-matched English comparison.'})
save(OUT/'question-only-baseline.json',{'kind':'ainglish.structural-instrument-baseline.v1',
 'algorithm':'Predict No for guarantee questions and Yes for unsupported-inference questions, without inspecting the assertion, form, value or distribution.',
 'groups':{k:{'correct':sum(v),'total':len(v),'fraction':sum(v)/len(v)} for k,v in groups.items()},
 'model_calls':0,'boundary':'Deterministic baseline, not measured model performance. Opposite question polarity balances answer codes but does not create a variable property or independent semantic cases.'})
save(OUT/'label-masked-review.json',masked)
print('Question-only baseline:',sum(groups['all']), '/',len(groups['all']),'; zero reader calls.')
