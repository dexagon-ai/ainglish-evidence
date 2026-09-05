"""Exact rational prospective probability gold; NO model calls and NO released attempt."""
from fractions import Fraction
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
 rows=[]
 for i,(a,b) in enumerate([(0,1),(1,0),(1,1),(1,3),(3,1),(1,4),(2,3),(3,2)]):
  p=Fraction(a,a+b)
  for form in ['prob','odds-for','odds-against']:
   for probe in ['probability','complement','odds-orientation','payout','calibration','frequency','causation','rounding']:
    event=f'E-{i}-{probe}';common=f'In model M-{i}, {event} and its non-occurrence are mutually exclusive and exhaustive. The following is a reported probability claim, not a statement of observed outcomes. '
    value=f'{float(p)*100:g}%' if form=='prob' else f'{a}:{b}' if form=='odds-for' else f'{b}:{a}'
    e=f'The probability of {event} is {value}.' if form=='prob' else f'The probability odds {"in favour of" if form=="odds-for" else "against"} {event} are {value}.'
    claim=f'{form}({event})={value}.'
    if probe in ['probability','complement']:
     gold=str(p if probe=='probability' else 1-p)
     options=list(dict.fromkeys([gold,str(1-p if probe=='probability' else p),'not determined','1/10','9/10']))[:4]
     question='What probability share is assigned to '+('the event' if probe=='probability' else 'its complement')+'?'
    elif probe=='odds-orientation':
     gold=f'{b}:{a}';options=list(dict.fromkeys([gold,f'{a}:{b}','not determined','2:5','5:2']))[:4]
     question='Which probability odds against the event express the same reported quantity?'
    else:
     question={'payout':'Does this alone state the bookmaker payout?',
      'calibration':'Does this alone establish that the model is calibrated?',
      'frequency':'Does this alone establish the observed event frequency?',
      'causation':'Does this alone establish a cause of the event?',
      'rounding':'Does this alone establish that the supplied estimate was not rounded?'}[probe]
     options=['yes','no'];gold='no'
    row={'id':f'prob-prospective-{i}-{form}-{probe}','english':common+e,'ainglish':common+claim,
     'question':question,'options':options,'answer':gold,'form':form,'probe':probe,
     'audit':{'favourable':a,'unfavourable':b,'probability':str(p),'complement':str(1-p)},
     'gate':'Design only. No inference before token prerequisite is independently satisfied; requires prospective panel/control qualification and fresh mint.'}
    rows.append(row)
 # Validator derives from the rendered ratio/percentage rather than trusting stored gold.
 for r in rows:
  text=r['ainglish'].split('=')[-1][:-1]
  if r['form']=='prob':derived=Fraction(text[:-1])/100
  else:
   x,y=map(Fraction,text.split(':'));assert x>=0 and y>=0 and x+y>0
   derived=(x if r['form']=='odds-for' else y)/(x+y)
  assert derived==Fraction(r['audit']['probability']) and derived+Fraction(r['audit']['complement'])==1
  if r['probe']=='probability':assert Fraction(r['answer'])==derived
  if r['probe']=='complement':assert Fraction(r['answer'])==1-derived
  if r['probe']=='odds-orientation':
   x,y=map(Fraction,r['answer'].split(':'));assert y/(x+y)==derived
  assert r['answer'] in r['options'] and len(set(r['options']))==len(r['options'])
 invalid=[{'form':'odds-for(E)=0:0','valid':False,'reason':'zero total probability weight'},
  {'form':'odds-against(E)=-1:2','valid':False,'reason':'negative probability weight'},
  {'form':'prob(E)=120%','valid':False,'reason':'outside unit interval'},
  {'form':'odds 3:1','valid':False,'reason':'orientation is unspecified'}]
 with (ROOT/'token-studies/probability.comprehension-design.json').open('x') as f:
  json.dump({'items':rows,'invalid_boundary_cases':invalid,'validated_items':len(rows),'reader_calls':0,
   'limitations':'Authored mathematical audit kit, not admitted comprehension evidence. Non-inference probes intentionally all no; report separately and add balanced entailed controls before launch.'},f,indent=2);f.write('\n')
 print(len(rows),'rationally checked design-only items; zero reader calls')
if __name__=='__main__':main()
