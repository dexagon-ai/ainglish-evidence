"""Freeze a price/allocation joint-reading original, including honest missing facts."""
from itertools import product
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import save_new
STATES=['yes','no','not determined']
JOINT=list(product(STATES,repeat=2))
DOMAINS=[('compute','GPU slot'),('rooms','meeting room'),('transport','bicycle'),('storage','storage bucket'),
 ('services','editing session'),('tickets','entry ticket'),('subscriptions','monthly account'),('shared-equipment','projector')]
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def options(index):
 pairs=JOINT[index%9:]+JOINT[:index%9]
 return {letter:list(pair) for letter,pair in zip('ABCDEFGHI',pairs)}
def bare_truth(affirmed,known):
 # Bare free admits either price or allocation reading. Intersect with the actual
 # visible facts; do not punish honest uncertainty using a hidden-world key.
 worlds=[]
 for charged,obtainable in product([False,True],repeat=2):
  if any((charged,obtainable)[k]!=v for k,v in known.items()):continue
  possible=(not charged or obtainable) if affirmed else (charged or not obtainable)
  if possible:worlds.append((charged,obtainable))
 assert worlds
 return [STATES[0] if all(w[i] for w in worlds) else STATES[1] if all(not w[i] for w in worlds) else STATES[2] for i in range(2)]
def build_cases():
 out=[]
 for domain,resource in DOMAINS:
  for form in ['no-charge','available-now']:
   for affirmed,other,revealed in product([False,True],repeat=3):
    serial=int(affirmed)*4+int(other)*2+int(revealed)
    item=f'{domain}-item-{7300+serial}';billing=f'{domain}-invoice-{7300+serial}';pool=f'{domain}-pool-{7300+serial}'
    common=f'Entry {item} is an offer for one {resource}. The named invoice is {billing}; the named allocation pool is {pool}. All mentioned requesters qualify. This record concerns 2026-09-07 at12:00 UTC. Monetary charges are nonnegative. '
    distractors=[
     'An unrelated licence must still be obtained for commercial use. ',
     'A refundable deposit belongs to a separate invoice and is not part of the named invoice. ',
     'A reservation in another pool gives no allocation rights in the named pool. ',
     'An inspection of operational health has not been completed. ',
     'A fee next month is outside the named invoice. ',
     'No promise of availability tomorrow has been made. ',
     'Non-monetary effort is not a charge on the named invoice. ',
     'The named invoice and pool exclude every other transaction and pool. ']
    common+=distractors[serial]
    if form=='no-charge':
     charged=not affirmed;obtainable=other;asserted=0;known={1:other} if revealed else {}
     if revealed:common+=f'A separate current allocation record says the requester '+('can' if other else 'cannot')+f' obtain this item from {pool} immediately. '
     a=f'{item} is '+('' if affirmed else 'not ')+f'no-charge({billing}).'
     e=f'{item} has '+('a monetary charge of zero' if affirmed else 'a monetary charge greater than zero')+f' on {billing}.'
    else:
     charged=other;obtainable=affirmed;asserted=1;known={0:other} if revealed else {}
     if revealed:common+=f'A separate current billing record says taking this item creates '+('a positive monetary charge' if other else 'a monetary charge of zero')+f' on {billing}. '
     a=f'{item} is '+('' if affirmed else 'not ')+f'available-now({pool}).'
     e=f'{item} '+('can' if affirmed else 'cannot')+f' currently be claimed by a qualifying requester in {pool}.'
    actual=[charged,obtainable]
    gold=[('yes' if actual[i] else 'no') if i==asserted or revealed else 'not determined' for i in range(2)]
    labels=options(len(out));answer=next(k for k,v in labels.items() if v==gold)
    bare=common+f'{item}: '+('free.' if affirmed else 'not free.')
    question=(f'First: will taking this item add a positive amount to {billing}? Second: can the qualifying requester obtain it immediately from {pool}? '
       'Answer from the record; do not invent missing facts. '+' '.join(f'{k}=first {v[0]}, second {v[1]}.' for k,v in labels.items()))
    out.append({'id':f'{domain}/{form}/{serial}','domain':domain,'form':form,'affirmed':affirmed,
     'other_revealed':revealed,'asserted_axis':asserted,'world':[charged,obtainable],'gold':gold,
     'bare_semantic_gold':bare_truth(affirmed,known),'bare_hidden_world':[STATES[0] if b else STATES[1] for b in actual],
     'choice_meanings':labels,'english':common+e,'ainglish':common+a,'bare':bare,'question':question,'answer':answer})
 return out
def main():
 cases=build_cases();assert len(cases)==128
 assert len({(r['english'],r['ainglish']) for r in cases})==128
 items=[{'id':c['id'],'english':c['english'],'ainglish':c['ainglish'],'question':c['question'],
  'options':list('ABCDEFGHI'),'answer':c['answer'],'settlement_stratum':c['form'],
  'strata':{'domain':c['domain'],'affirmed':int(c['affirmed']),'other_revealed':int(c['other_revealed'])}} for c in cases]
 for i in range(8):
  letter='ABCDEFGH'[i]
  items.append({'id':f'price-neutral-{9100+i}','calibration':True,
   'english':f'The outcome code for seal {9100+i} has not been recorded.',
   'ainglish':f'The recorded outcome code for seal {9100+i} is {letter}.',
   'question':'Which outcome code is stated? A=A. B=B. C=C. D=D. E=E. F=F. G=G. H=H. I=not determined.',
   'options':list('ABCDEFGHI'),'answer':letter})
 save_new(ROOT/'cases.json',cases);save_new(ROOT/'items.json',items)
 save_new(ROOT/'PLAN.json',{'kind':'ainglish.price-allocation-joint-original.v1','public_id':'a-yc4193gwc2e87zkn',
  'slug':'offer-is-no-charge-billing-scope-resource-is-available-now','seed':20260907032,
  'items':128,'calibration_items':8,'domains':8,'forms':2,'predicted_margin_pp':-5,
  'population':'Eight authored domain frames crossed with form, affirmation/explicit negation, latent other-axis truth and whether the other axis is actually reported.128 semantic cells, not128 independently authored templates.',
  'primary':'Joint accuracy on invoice-positive-charge and current allocatability, marked versus complete careful English. Nine exhaustive answer vectors include unknown; unreported facts are UNKNOWN, never recovered from hidden world metadata. Report each form,domain,polarity and revelation cell separately.',
  'diagnostics':'Frozen bare wording, its independently enumerated semantic key and hidden world are retained for a separate descriptive follow-up. No bare calls are included in this original or used in its scalar; no asserted25pp improvement over bare is claimed.',
  'reader_setup':'Both independently screened exact local ctx4k Q4 Gemma12 and Mistral24 readers from qualified-comprehension-2026-09-07; SDK serial reader-outermost order, stateless opaque-choice protocol,128 output cap,greedy,seed20260907031.',
  'gates':['Both predeclared exact-reader screens pass, then per-reader fresh calibration passes; no target calls before authenticated SDK preregistration.',
   'Proposal remains visible nonterminal with unchanged mapping and token prerequisite satisfied; original-author or external gates are not bypassed.',
   'Zero absent,off-option,truncated or transport-fault cells; preserve every admitted direction and any failed-gate abort without target retries.'],
  'non_claims':['A focused joint-reading original, not completion of the entire proposal prediction. Bare gain, direct permission/health inference and edit robustness still need their own evidence.',
   'Ordinary scoped negation is explicitly included, not presented as a third newly registered form; report its cells separately.',
   'No human panel, weight training, future tokenizer savings or independent confirmation is claimed. English training/tokenization incumbency contextualizes adverse results without erasing them.']})
 names=['build.py','test_design.py','run.py','README.md','PLAN.json','cases.json','items.json','proposal.json',
  '../qualified-comprehension-2026-09-07/screens.json','../qualified-comprehension-2026-09-07/QUALIFICATION-PLAN.json',
  '../overnight-runtime-2026-09-06/runtime.py']
 save_new(ROOT/'FROZEN.json',{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
 print('128 joint semantic cases plus8 controls; no tokenization or reader calls.')
if __name__=='__main__':main()
