"""Prospective finite-semantics bank. No reader calls and no governance writes."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
from ainglish.panel import arm_for

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
LIVE=REPO.parent/'live'
PID='a-egz4k62p8x713bt5'
SEED=2026091451  # exact already-qualified sampler configuration
FORMS=['none-of','not-all-of']
DOMAINS={
 'replicas': ['has the latest schema','answers the checksum challenge','holds an intact journal','accepts a read request'],
 'tests': ['finishes within its deadline','meets its stated criterion','produces the expected trace','checks the intended branch'],
 'permissions': ['permits a metadata update','permits opening the archive','permits sending a notification','permits reading the audit log'],
 'files': ['contains a signed header','has a matching digest','opens without a parse error','includes the requested field'],
 'recipients': ['received the attachment','returned an acknowledgement','can open the document','received the revised address'],
 'workers': ['completed the assigned unit','holds a current lease','can reach the coordinator','uploaded the final output'],
 'regions': ['reports an intact index','can serve a fresh read','has received the update','meets the latency target'],
 'people': ['has booked a seat','returned the consent form','has a current entry pass','attended the briefing'],
}

def write(name,data):
 (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

def digest(data):
 return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def label(key):
 return hashlib.sha256(('overnight-none-20260914/'+key).encode()).hexdigest()[:12]

def menu(options,key):
 return sorted(options,key=lambda x:hashlib.sha256((key+'|'+x).encode()).hexdigest())

def permitted(form,n):
 assert n>=2
 return {0} if form=='none-of' else set(range(n))

def controls(learn=False):
 out=[]
 for i in range(16):
  x,y=f'Desk-Orchid-{i+17}',f'Desk-Jasper-{i+51}'
  opts=[x,y,'Both desks','The assignment has not been resolved']
  out.append({'id':f'control-{i:02}', 'calibration':True,
   'english':f'The routing record leaves the delivery owner unresolved between {x} and {y}.',
   'ainglish':f'The routing record assigns delivery ownership to {x}, explicitly excluding {y}.',
   'question':'Which desk may now be written into the completed delivery-owner field?',
   'options':menu(opts,f'control-{i}'),'answer':x,
   **({'calibration_construct':'delivery-owner-record','calibration_scope':'target-independent'} if learn else {})})
 return out

def scenario(domain,predicate,n,variant,coverage='whole'):
 sid='S-'+label(f'{variant}/{domain}/{predicate}/{n}/{coverage}')
 p='P-'+label('predicate/'+domain+'/'+predicate)[:5]
 names=[f'{domain}-{label(sid+str(j))[:4]}' for j in range(n)]
 context=(f'Frozen record {sid}. The membership list is {", ".join(names)}; exactly {n} distinct {domain}, '
          f'unchanged throughout this report. {p} names the property "{predicate}". ')
 if coverage=='part':
  context += 'These listed members are a sample from a larger collection; no statement covers the unlisted members. '
 else:
  context += 'These listed members are the entire named collection. '
 return sid,p,context

def primary(variant='primary'):
 out=[]
 for d,preds in DOMAINS.items():
  for pi,predicate in enumerate(preds):
   for n in range(2,9):
    coverage='part' if (pi+n)%2 else 'whole'
    sid,p,ctx=scenario(d,predicate,n,variant,coverage)
    opts=['Exactly k=0',f'Any integer k from 0 through {n-1}',
          f'Any integer k from 1 through {n-1}',f'Exactly k={n}',
          'The quantified claim is invalid or its set cannot be resolved']
    question=f'Taking the report as a claim, which values of k, the number of listed members meeting {p}, does it permit?'
    for form in FORMS:
     en=(f'No member of {sid} satisfies {p}.' if form=='none-of'
         else f'At least one member of {sid} does not satisfy {p}.')
     gold=opts[0] if form=='none-of' else opts[1]
     out.append({'id':'target-'+label(sid+'/'+form),'english':ctx+en,
      'ainglish':ctx+f'{form}({sid}): {p}.','question':question,
      'options':menu(opts,sid),'answer':gold,'settlement_stratum':form,
      'strata':{'form':form,'domain':d,'set_size':n,'coverage':coverage,'frame':sid,'predicate_family':f'{d}-{pi}','probe':'interval'},
      'audit_only':{'allowed_counts':sorted(permitted(form,n)),
        'bare_english':ctx+f'All members of {sid} do not satisfy {p}.',
        'bare_truth_boundary':'The hidden intention is not identifiable from this ambiguous surface. No bare accuracy result is filed as the careful-English carrier.'}})
 return out

def consequence_bank():
 out=[]
 for row in primary('consequence'):
  n=row['strata']['set_size']; form=row['settlement_stratum']; ks=permitted(form,n)
  tests=[('mixed', 'Could a situation with one successful member and at least one unsuccessful member fit this report?',1 in ks),
         ('existence','Could a successful member exist without contradicting this report?',any(k>0 for k in ks)),
         ('failure','Does this claim require at least one unsuccessful member among the listed members?',all(k<n for k in ks)),
         ('all','Could every listed member be successful without contradicting this report?',n in ks),
         ('capacity','If continued service requires at least one successful listed member, does this report guarantee continued service?',all(k>0 for k in ks))]
  # Here success means meeting the named property, not an extra claim about its desirability.
  for probe,q,gold in tests:
   item={k:v for k,v in row.items() if k!='audit_only'}
   item['id']='probe-'+label(row['id']+'/'+probe)
   item['question']='For this question, successful means meeting the named property. '+q
   item['options']=menu(['Yes','No'],item['id']);item['answer']='Yes' if gold else 'No'
   item['strata']={**row['strata'],'probe':probe}
   out.append(item)
 return out

def learning_bank():
 # Entirely different identified sets from the primary and consequence banks.
 rows=[r for r in primary('learning') if r['strata']['set_size'] in [3,6]]
 for r in rows:
  r.pop('audit_only',None);r['english']=r['ainglish']
 return rows

def roster():
 panels=[];receipts=[]
 q=REPO/'choose-any-completion-2026-09-14/qualification'
 for short in ['gemma','mistral']:
  screen=json.loads((q/f'{short}-screen.json').read_text())
  result=json.loads((q/f'{short}-result.json').read_text())
  assert result['status']=='passed'
  panels.append(screen['reader']);receipts.append(result['receipt'])
 return panels,receipts

def specs():
 proposal=json.loads((LIVE/(PID+'.json')).read_text())
 panels,receipts=roster()
 summary=[]
 # Consequences contain five probes on the same 448 worlds. Their correlation is explicit;
 # the 2240 responses are NOT 2240 independently authored scenarios.
 for name,rows,metric in [('primary',primary(),'comprehension_accuracy_delta'),
      ('consequences',consequence_bank(),'comprehension_accuracy_delta'),
      ('learning',learning_bank(),'learnability')]:
  items=rows+controls(metric=='learnability')
  entry='Registered form: '+proposal['form']+'\n\n'+proposal['english_mapping']
  spec={'slug':proposal['slug'],'construct':'none-of / not-all-of','form':proposal['form'],
    'metric':metric,'seed':SEED,'panel_neff':1,'panel':panels,'reader_qualifications':receipts,
    'items_sha256':digest(items),'items_url':str(ROOT/(name+'.items.json')),
    'calibration_min_gap':.5,'calibration_min_recovered':.875,'planted_arm':'ainglish',
    'admissibility':{'kind':'ainglish.panel.admissibility.v1','per_reader_calibration':True,
       'max_off_option_cells':0,'max_absent_cells':0,'max_truncated_cells':0,'max_transport_fault_cells':0},
    'study_purpose':'claim_test' if name!='learning' else 'diagnostic',
    'study_scope':f'{name}: exact two cached qualified native readers, conservatively panel_neff=1. Complete careful-English mappings for CAD. Finite authored scenarios, correlated templates, per-form reporting; not independent confirmation, human comprehension or future training. Bare-English ambiguity, invalid-set and corruption obligations are not claimed complete by this component.',
    'attempt':{'estimand':f'{name} on the frozen authored population and two named instruments. CAD is marked minus complete-English accuracy with equal required form weights, one hash-assigned arm per reader/item. Learning is entry-loaded accuracy plus paired cold/loaded descriptive gain. All form/domain/size/coverage/probe slices and actual counts retained; supplementary per-reader conditional binomial bounds and frame-cluster sensitivity do not assert population independence.',
      'admissibility_gates':['Current version and meaning unchanged, no new author hold, exact roster/digest/settings qualifications valid before exposure.',
       'All frozen text, options, golds and actual reader payloads audited before mint; answer-bearing metadata never enters reader request.',
       'One serial pass; no retries, alternate seed/model selection or outcome-dependent sample expansion. Retain adverse/null results.',
       'At least 20 GiB local disk free and GPUs available; no new weights, no displacement of another workload.'],
      'planned_sample':{'real_items':len(rows),'calibration_items':16,'readers':2,
       'target_calls':len(rows)*2*(2 if metric=='learnability' else 1),'calibration_calls':64,
       'distinct_world_frames':len({r['strata']['frame'] for r in rows}),
       'form_items':dict(Counter(r['settlement_stratum'] for r in rows))}}}
  if metric=='comprehension_accuracy_delta':
   spec['settlement_strata']=[{'id':f,'weight':1} for f in FORMS]
  if metric=='learnability':
   spec['entry']={'text':entry,'sha256':hashlib.sha256(entry.encode()).hexdigest(),
    'source_url':f'https://ainglish.org/api/v1/proposals/{PID}','proposal_revision':proposal['slug']}
  write(name+'.items.json',items);write(name+'.runspec.json',spec)
  summary.append({'name':name,**spec['attempt']['planned_sample'],
    'items_sha256':spec['items_sha256'],
    'assignment_counts':dict(Counter(f"{ep['name']}/{r['settlement_stratum']}/{arm_for(SEED,ep['name'],r['id'])}" for ep in panels for r in rows))})
 write('DESIGN-COUNTS.json',summary)
 # Exhaust all Boolean membership-property assignments, not just selected friendly cases.
 checked=0
 for n in range(2,9):
  for bits in itertools.product([0,1],repeat=n):
   k=sum(bits)
   assert (k in permitted('none-of',n)) == (not any(bits))
   assert (k in permitted('not-all-of',n)) == (not all(bits))
   checked+=2
 write('SEMANTIC-ORACLE.json',{'truth_assignments_checked':checked,
  'not_all_includes_zero':True,'none_excludes_every_positive_count':True,
  'reader_calls':0,'scope':'Finite logical golds, not independent instrument review or language-performance evidence.'})
 print(json.dumps(summary,indent=2))

if __name__=='__main__':specs()
