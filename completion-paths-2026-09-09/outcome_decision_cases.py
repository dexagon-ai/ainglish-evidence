"""Small exact-arithmetic design review set. No inference or performance claim."""
import json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parent
distributions=[('outside-support',[(0,F(9,10)),(10,F(1,10))]),
 ('non-majority-mode',[(0,F(2,5)),(1,F(7,20)),(2,F(1,4))]),
 ('tied-modes',[(0,F(1,2)),(10,F(1,2))]),
 ('mean-is-mode',[(0,F(1,4)),(2,F(1,2)),(4,F(1,4))]),
 ('certainty-positive',[(3,F(1))]),
 ('aggregated-paths',[(0,F(1,4)),(0,F(1,4)),(4,F(1,2))])]
rows=[]
for name,paths in distributions:
    mass={}
    for x,prob in paths:mass[x]=mass.get(x,F(0))+prob
    assert sum(mass.values())==1 and all(p>0 for p in mass.values())
    mean=sum(F(x)*prob for x,prob in mass.items()); top=max(mass.values())
    modes=sorted(x for x,prob in mass.items() if prob==top)
    for form,x in [('mean-outcome',mean),('likeliest-outcome',F(modes[0]))]:
        p=mass.get(x,F(0))
        rows.append({'id':name+'-'+form,'form':form,'value':str(x),
          'paths':[{'value':v,'probability':str(prob)} for v,prob in paths],
          'aggregated_mass':{str(v):str(prob) for v,prob in mass.items()},
          'mean':str(mean),'modes':modes,
          'consequence_golds':{'can_equal_value':p>0,'must_equal_value':p==1,
             'more_likely_equal_than_all_alternatives':p>F(1,2),
             'value_is_unique_highest_probability_outcome':x in modes and len(modes)==1}})
for key in rows[0]['consequence_golds']:
    assert {r['consequence_golds'][key] for r in rows}=={True,False}, key
out={'kind':'ainglish.outcome-semantic-review-cases.v1','not_a_scientific_sample':True,
     'inference_calls':0,'meaning_changed':False,'rows':rows,
     'warning':'One consequence per eventual trial; these reviewed worlds are not reusable as a held-out scientific set. No author acceptance or performance is inferred.'}
with (ROOT/'outcome-decision-cases.json').open('x') as f:json.dump(out,f,indent=2)
print('12 exact-arithmetic review cases; both truth values for every consequence; no inference.')
