"""Prospective held-out designs. Build and symbolically validate before any target call."""
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import random
import statistics

ROOT=Path(__file__).resolve().parent
SEED=2026090582
LETTERS=list('ABCD')

def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def save(path,value):
 path.parent.mkdir(exist_ok=True,parents=True)
 with path.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def number(v):
 v=Fraction(v)
 return str(v.numerator) if v.denominator==1 else str(float(v))
def item(ident,e,a,q,choices,gold,stratum,meta):
 assert len(choices)==len(set(choices)) and gold in choices
 return {'id':ident,'english':e,'ainglish':a,'question':q,'options':choices,'answer':gold,
         'settlement_stratum':stratum,'strata':meta}
def controls(study):
 result=[]
 for i,(a,b) in enumerate([('Elva','Reno'),('Hana','Vero'),('Jora','Lito'),('Kira','Bren'),
                            ('Mavi','Sena'),('Neri','Falo'),('Pavo','Gita'),('Tera','Wren')]):
  r=item(f'{study}-control-{i}',f'Either {a} or {b} has locker {study}-{i}; its holder is unspecified.',
      f'{a}, not {b}, has locker {study}-{i}; its holder is specified.',
      f'Who has locker {study}-{i}?',[a,b,'unspecified','neither'],a,'control',{})
  r['calibration']=True;r.pop('settlement_stratum');result.append(r)
 return result
def encode(rows):
 # Opaque output is deliberately short; full choices remain in the common question.
 # Gold letter positions are balanced per condition, rather than merely rotating lists.
 for stratum in sorted({r.get('settlement_stratum','control') for r in rows}):
  subset=[r for r in rows if r.get('settlement_stratum','control')==stratum]
  for i,r in enumerate(subset):
   options=list(r['options']);gold=r['answer'];n=len(options);pos=i%n
   options.remove(gold);random.Random(SEED+i+len(stratum)).shuffle(options);options.insert(pos,gold)
   labels=LETTERS[:n]
   r['strata']['answer_options']=dict(zip(labels,options))
   r['strata']['semantic_gold']=gold
   r['question']+=' Answer with the option letter only. '+' '.join(f'{l} = {v}.' for l,v in zip(labels,options))
   r['options']=labels;r['answer']=labels[pos]
 return rows

def mean():
 primary=[];practical=[];diagnostic=[];populations={}
 families=[[2,2,2,2,62],[-12,-4,6,10],[-7,-1,0,4,9],[3,3,11,11,27],
           [-8,-2,2,8],[1,5,5,7,12],[0,0,3,17],[-9,-5,-5,3]]
 domains=[('valve correction','Pa'),('invoice adjustment','GBP'),('route delay','minutes'),
          ('sensor offset','degC'),('crate balance','units'),('power adjustment','kWh'),
          ('column deviation','mm'),('account movement','EUR')]
 for i,(domain,family) in enumerate(itertools.product(domains,families)):
  d,unit=domain;refs=[f'PDX-{i:03}-east',f'PDX-{i:03}-west'];chosen=i%2
  values=[[v*(1+i%3)+7*i+side*19 for v in family] for side in range(2)]
  for ref,vals in zip(refs,values):populations[ref]={'values':vals,'unit':unit,'window':'2026-09-05T12:00/13:00Z','all_included':True,'no_missing':True,'transform':'identity','scope':'only this finite recorded collection'}
  common=(f'The immutable {d} files below each contain their entire listed finite collection, in {unit}, '
    'for 12:00–13:00 UTC on 5 September 2026. Include every listed value with equal weight, '
    'exclude none, treat no value as missing, and apply no transformation. No wider-population claim is made.\n'+
    '\n'.join(f'{ref}: '+', '.join(map(str,v))+'.' for ref,v in zip(refs,values))+'\nFiled report: ')
  for form in ['mean-of','median-of']:
   value=statistics.mean([Fraction(x) for x in values[chosen]]) if form=='mean-of' else statistics.median([Fraction(x) for x in values[chosen]])
   stat='unweighted arithmetic mean' if form=='mean-of' else 'median'
   e=f'The {stat} of the exact finite collection {refs[chosen]} is {number(value)} {unit}.'
   a=f'{form}({refs[chosen]}) = {number(value)} {unit}.'
   choices=[f'{op}; {ref}' for op,ref in itertools.product(['sum/count','sorted middle'],refs)]
   gold=f'{"sum/count" if form=="mean-of" else "sorted middle"}; {refs[chosen]}'
   meta={'form':form,'frame_cluster':i,'family':families.index(family),'domain':d,'target_ref':refs[chosen],
         'other_ref':refs[1-chosen],'reported_value':number(value),'probe':'joint-statistic-and-reference'}
   r=item(f'mean-new-{i}-{form}',common+e,common+a,
     'An auditor must reproduce exactly this report. Which computation and file must be used? '
     'sum/count adds all values and divides by their count; sorted middle sorts all values and '
     'takes the middle, averaging the two central values for even size.',choices,gold,form,meta)
   primary.append(r)
   other=json.loads(json.dumps(r));other['english']=common+f'{"Arithmetic mean" if form=="mean-of" else "Median"} of {refs[chosen]} = {number(value)} {unit}.';practical.append(other)
   # Separate consequence diagnostic, never pooled into the primary identification test.
   probe=i%4
   q=['Is the reported centre strictly above more than half of the listed individual values?',
      'Does any listed individual value equal the reported centre?',
      'Does this report alone establish the same centre for a larger unobserved collection?',
      'Can an auditor obtain this exact centre from the complete stated file and procedure?'][probe]
   yes=[sum(Fraction(v)<value for v in values[chosen])>len(values[chosen])/2,
        value in values[chosen],False,True][probe]
   diagnostic.append(item(f'mean-consequence-{i}-{form}',common+e,common+a,q,['yes','no'],
       'yes' if yes else 'no',form,dict(meta,probe=['above-most','observed-value','wider-population','exact-recheck'][probe],diagnostic_only=True)))
 return {'mean.careful':primary,'mean.practical':practical,'mean.consequences':diagnostic},populations

def quantity():
 rows=[]
 domains=[('coolant target','degC'),('freight allowance','GBP'),('dispatch offset','minutes'),
          ('crate reserve','units'),('pressure correction','Pa'),('battery target','kWh'),
          ('drill depth','mm'),('credit adjustment','EUR')]
 for condition in ['known','unknown','ordered']:
  for i in range(16):
   quantity,unit=domains[i%8];quantity=f'Batch PDQ-{condition}-{i} {quantity}'
   old=-23+7*i;operand=(-1 if i%2 else 1)*(3+i);first=11-i
   for form in ['set-to','adjust-by']:
    common=f'One scalar quantity is in scope: {quantity}, measured in {unit}. '
    if condition=='unknown':common+='Its current value is not supplied. '
    else:common+=f'Its starting value is {old} {unit}. '
    if condition=='ordered':common+=f'First increase this quantity by {first} {unit}; complete that update before the next instruction. '
    before=old+first if condition=='ordered' else old
    value=None if condition=='unknown' and form=='adjust-by' else operand if form=='set-to' else before+operand
    e=(f'Set this quantity to {operand} {unit}.' if form=='set-to' else
       f'{"Increase" if operand>=0 else "Decrease"} this quantity by {abs(operand)} {unit}.')
    a=f'{quantity} {form}({operand:+d} {unit}).'
    candidates=list(dict.fromkeys([operand,before+operand,before,operand-before]))
    while len(candidates)<3:candidates.append(900+len(candidates))
    candidates=candidates[:3]
    if value is not None and value not in candidates:candidates[-1]=value
    choices=[f'{n} {unit}' for n in candidates]+['not determined']
    rows.append(item(f'quantity-new-{condition}-{i}-{form}',common+e,common+a,
      'Assuming the stated updates complete exactly in their stated order, what is the final value?',choices,
      'not determined' if value is None else f'{value} {unit}',form+':'+condition,
      {'form':form,'condition':condition,'frame_cluster':condition+'-'+str(i),'old':old,'operand':operand,
       'first':first,'expected':value,'unit':unit,'domain':domains[i%8][0]}))
 return rows

def choice():
 rows=[]
 for probe in ['admissibility','feasibility','consequence']:
  for i in range(16):
   members=[f'PD-{probe}-{i}-{x}' for x in 'KLM'];values=[f'agent-{i}-R',f'agent-{i}-S']
   patterns=[[[0,1],[0,1],[0,1]],[[0],[1],[0,1]],[[0],[0],[0]],[[0],[0,1],[1]],
             [[0,1],[],[0,1]],[[1],[1],[1]],[[0],[0],[0,1]],[[0,1],[0,1],[1]]]
   eligibility={m:[values[v] for v in indices] for m,indices in zip(members,patterns[i%8])}
   candidate=[values[(i+j)%2] if i%3 else values[i%2] for j in range(3)]
   common=(f'The set Reports-{probe}-{i} contains exactly '+', '.join(members)+'. '
      'Assign exactly one reviewer to each report. Reviewer identifiers denote distinct people; '
      'reviewer capacity is unlimited. All eligibility constraints remain mandatory. '+
      ' '.join(f'{m} allows '+(', '.join(eligibility[m]) or 'no reviewer')+'.' for m in members)+'\nRequirement: ')
   for form in ['same-for-all','may-vary-across']:
    e=('All three reports must use the same reviewer.' if form=='same-for-all' else 'Reviewers may be the same or different across the three reports.')
    a=f'Assign exactly one reviewer to each report, {form}(Reports-{probe}-{i}).'
    # Per-member cardinality is already common context; repeat it in BOTH variable arms.
    e='Assign exactly one reviewer to each report. '+e
    valid=[x for x in itertools.product(*(eligibility[m] for m in members))
           if form=='may-vary-across' or len(set(x))==1]
    if probe=='admissibility':
     common_probe=common+'Candidate: '+', '.join(f'{m} → {v}' for m,v in zip(members,candidate))+'.\n'
     q='Does the candidate satisfy every stated requirement?';yes=tuple(candidate) in valid
    elif probe=='feasibility':common_probe=common;q='Does at least one assignment satisfy every stated requirement?';yes=bool(valid)
    else:common_probe=common;q='Is at least one permitted assignment possible that uses more than one reviewer identity?';yes=any(len(set(x))>1 for x in valid)
    rows.append(item(f'choice-new-{probe}-{i}-{form}',common_probe+e,common_probe+a,q,['yes','no'],
      'yes' if yes else 'no',form+':'+probe,{'form':form,'probe':probe,'frame_cluster':probe+'-'+str(i),
       'members':members,'values':values,'eligibility':eligibility,'candidate':candidate,'valid_count':len(valid)}))
 return rows

GUIDES={
 'quantity':{
  'english':'Reference: set a quantity to V makes V its new value. Increase or decrease it by D changes its immediately preceding value by that signed amount. A missing starting value can prevent a numeric answer. Explicitly ordered updates are applied in that order.',
  'ainglish':'Reference: quantity set-to(V) makes V its new value. quantity adjust-by(D) changes its immediately preceding value by signed D. A missing starting value can prevent a numeric answer. Explicitly ordered updates are applied in that order.'},
 'choice':{
  'english':'Reference: the same reviewer for all reports requires one shared reviewer identity. Reviewers may be the same or different allows reuse and variation but requires neither diversity nor completion. Exactly one reviewer per report, eligibility and capacity constraints still apply.',
  'ainglish':'Reference: same-for-all(reports) requires one shared reviewer identity. may-vary-across(reports) allows reuse and variation but requires neither diversity nor completion. Exactly one reviewer per report, eligibility and capacity constraints still apply.'}}

def instruction():
 rows=[]
 directives=[('Use sentence-case headings','document','Use sentence-case headings'),
  ('Write dates with the month spelled out','report','Write dates with the month spelled out'),
  ('Include units beside every numeric value','table','Include units beside every numeric value'),
  ('Sort entries alphabetically','index','Sort entries alphabetically'),
  ('Use British spelling','guide','Use British spelling'),
  ('Place the summary before the body','memo','Place the summary before the body'),
  ('Name the reference beside each comparison','review','Name the reference beside each comparison'),
  ('Separate assumptions from conclusions','analysis','Separate assumptions from conclusions')]
 for i,(d,kind,_) in enumerate(directives):
  for context in ['current','later-same-project','later-other-project','unrelated-kind','revoked','storage-forbidden','audit-required','explicit-project-limit']:
   for form in ['this-once','from-now-on']:
    pre=f'The same human asks for a {kind} in project Maple. '
    if context=='storage-forbidden':pre+='A separate policy forbids storing preferences; this question concerns applicability, not storage. '
    if context=='audit-required':pre+='A separate policy requires retaining all requests in an audit log; retention does not determine applicability. '
    if context=='explicit-project-limit':pre+='The human explicitly limits this directive to project Maple only. '
    e=f'{d} for this item only; it does not govern later comparable work.' if form=='this-once' else f'{d} for this item and all later comparable work until explicitly revoked.'
    a=d+', '+form+'.'
    later={'current':'You are doing the original item now.',
     'later-same-project':f'Later the same human requests another comparable {kind} in Maple, without revoking the directive.',
     'later-other-project':f'Later the same human requests another comparable {kind} in project Cedar, without revoking or limiting the directive.',
     'unrelated-kind':'Later the same human requests a different kind of work, a numerical checksum calculation rather than that document task.',
     'revoked':f'The human explicitly revokes the directive before requesting another comparable {kind}.',
     'storage-forbidden':f'Later the same human requests another comparable {kind}; the directive has not been revoked.',
     'audit-required':f'Later the same human requests another comparable {kind}; the directive has not been revoked.',
     'explicit-project-limit':f'Later the same human requests another comparable {kind} in project Cedar.'}[context]
    yes=context=='current' or form=='from-now-on' and context in ['later-same-project','later-other-project','storage-forbidden','audit-required']
    rows.append(item(f'scope-prospective-{i}-{context}-{form}',pre+e+' '+later,pre+a+' '+later,
      'Does this directive govern the work now being requested?',['yes','no'],'yes' if yes else 'no',form+':'+context,
      {'form':form,'context':context,'frame_cluster':i,'expected_applies':yes,'author_resolution_required_before_inference':True}))
 return rows

def main():
 studies,populations=mean()
 for name,rows in [('quantity',quantity()),('choice',choice())]:
  studies[name+'.cold']=rows
  warm=json.loads(json.dumps(rows));guide=GUIDES[name]
  # Same information in each language's guide, tightly matched words/characters; report
  # actual tokenizer-specific instruction costs separately, not hidden as free context.
  for r in warm:
   for arm in ['english','ainglish']:r[arm]=guide[arm]+'\n\n'+r[arm]
  studies[name+'.reference']=warm
 studies['instruction.prospective']=instruction()
 index={}
 for name,rows in studies.items():
  rows=encode(rows+controls(name))
  save(ROOT/'frozen'/f'{name}.items.json',rows)
  index[name]={'items_sha256':hashlib.sha256(canonical(rows)).hexdigest(),
    'real_items':sum(not x.get('calibration') for x in rows),'controls':8,
    'strata':dict(Counter(x['settlement_stratum'] for x in rows if not x.get('calibration')))}
 save(ROOT/'frozen/design-index.json',index);save(ROOT/'frozen/populations.json',populations)
 save(ROOT/'frozen/guides.json',GUIDES)
 print(json.dumps(index,indent=2))

if __name__=='__main__':main()
