"""Unrun author-review packet: one warranted-consequence question, rational counterexamples."""
from fractions import Fraction as F
import hashlib,json
from reader_campaign import ROOT,save

OUT=ROOT/'outcome-consequence-review'
FAMILIES={
 'weighted-mean':('the probability-weighted average outcome equals {x}',lambda d,x:sum(v*p for v,p in d)==x),
 'possible-value':('the reported value {x} can occur as a single outcome',lambda d,x:any(v==x for v,p in d)),
 'maximal-mass':('no distinct outcome value has greater probability than {x}',lambda d,x:dict(d).get(x,F(0))>=max(p for v,p in d)),
 'next-certain':('the next draw is guaranteed to equal {x}',lambda d,x:dict(d).get(x,F(0))==1),
 'unique-most-probable':('{x} is the only value with the highest outcome probability',lambda d,x:dict(d).get(x,F(0))==max(p for v,p in d) and sum(p==max(q for v,q in d) for v,p in d)==1),
 'more-than-half':('the probability of {x} is greater than one half',lambda d,x:dict(d).get(x,F(0))>F(1,2)),
 'median':('at least half the probability lies on values no greater than {x}, and at least half on values no smaller',lambda d,x:sum(p for v,p in d if v<=x)>=F(1,2) and sum(p for v,p in d if v>=x)>=F(1,2)),
 'affine-average':('if each outcome v is converted to 2v+3, its probability-weighted average becomes {affine}',lambda d,x:sum((2*v+3)*p for v,p in d)==2*x+3),
}
def encode(d):return [{'value':v,'probability':str(p)} for v,p in d]
def run():
 rows=[];ledger=[]
 for form in ('mean-outcome','likeliest-outcome'):
  for x in (6,12):
   ds=[[(x,F(1))],[(x-2,F(1,2)),(x+2,F(1,2))],[(x-2,F(1,3)),(x+1,F(2,3))],
       [(x,F(3,5)),(x+5,F(2,5))],[(x,F(1,2)),(x+1,F(1,2))],
       [(x,F(2,5)),(x+1,F(3,10)),(x+2,F(3,10))]]
   valid=[d for d in ds if (FAMILIES['weighted-mean'][1](d,x) if form=='mean-outcome' else FAMILIES['possible-value'][1](d,x) and FAMILIES['maximal-mass'][1](d,x))]
   entailed={'weighted-mean','affine-average'} if form=='mean-outcome' else {'possible-value','maximal-mass'}
   for fi,(family,(template,prop)) in enumerate(FAMILIES.items()):
    yes=family in entailed;counter=next((d for d in valid if not prop(d,x)),None)
    witness=next(d for d in valid if prop(d,x))
    assert (counter is None)==yes
    for reverse in (False,True):
     iid=f'consequence-{form}-{x}-{fi}-{int(reverse)}';ref='D-'+hashlib.sha256(iid.encode()).hexdigest()[:8]
     common=(f'{ref} uniquely identifies one fixed finite discrete distribution of toy numeric outputs in units of counts under model v1. '
      'Its complete table is retained by the writer but is not supplied to the recipient. Treat the following assertion as truthful relative to that table, not as a claim that the model predicts the real world correctly. '
      'Shared definitions: a mean is the probability-weighted arithmetic average; a most probable outcome is a supported value whose mass is no smaller than any other value, with ties allowed. ')
     claim=template.format(x=x,affine=2*x+3)
     question=('Would assuming the following go beyond what this assertion alone guarantees? ' if reverse else 'Does this assertion alone guarantee the following? ')+claim+'.'
     english=(f'Under {ref}, the probability-weighted mean is {x}.' if form=='mean-outcome' else f'Under {ref}, {x} has the highest outcome probability, ties allowed.')
     rows.append({'id':iid,'english':common+english,'ainglish':common+f'{x} is {form}({ref}).',
       'question':question,'options':['Yes','No'],'answer':'Yes' if yes!=reverse else 'No',
       'strata':{'form':form,'consequence_family':family,'question_polarity':'unsupported' if reverse else 'guaranteed','numeric_instance':x},
       'independent_semantic_cluster':family})
     ledger.append({'item_id':iid,'assertion_entailed':yes,'witness_distribution':encode(witness),
       'counterexample_distribution':None if counter is None else encode(counter),
       'proof':('Finite weighted-sum identity and linearity.' if form=='mean-outcome' else 'Definition of a supported maximal-probability value, with ties permitted.') if yes else 'A valid distribution satisfying the asserted statistic makes the proposed consequence false; the witness makes it true. Therefore the assertion alone does not decide it.'})
 assert len(rows)==64 and sum(r['answer']=='Yes' for r in rows)==32
 for form in ('mean-outcome','likeliest-outcome'):
  assert sum(r['answer']=='Yes' for r in rows if r['strata']['form']==form)==16
 save(OUT/'items.json',rows);save(OUT/'rational-entailment-audit.json',ledger)
 save(OUT/'status.json',{'status':'unrun author-review instrument, not an approved claim-carrier plan',
  'items':64,'semantic_clusters':8,'digest_rule':'SHA-256 of sorted-key compact UTF-8 JSON',
  'items_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),
  'model_calls':0,'attempts_minted':0,'ainglish_measurements':0})
 print('Prepared 64 balanced one-consequence rows; all non-entailments have exact rational witnesses and counterexamples.')
if __name__=='__main__':run()
