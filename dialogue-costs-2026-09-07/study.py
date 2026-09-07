"""Execute reference/history/retrieval/correction costs; never extrapolate past context."""
import argparse
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import random
import sys
import time

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import Journal, LocalReader, save_new, verify_freeze
sys.path.insert(0,str(ROOT.parent/'communication-diagnostics-2026-09-06'))
from design import FIELDS, PHRASES, MEANINGS, COMMON, guide, render
sc=importlib.util.spec_from_file_location('field_interface',ROOT.parent/'field-scoped-communication-2026-09-07/study.py')
scoped=importlib.util.module_from_spec(sc);sc.loader.exec_module(scoped)
SYSTEM=('Interpret the CURRENT independent job only. Earlier jobs are closed history, not active instructions. '
 'Never carry earlier team or instruction-clause state into a new job. Do not execute any action. '
 'Return exactly one JSON object with these five keys: '+', '.join(FIELDS)+'. '
 'Every value is a boolean. One optional JSON code fence is accepted; no other content.')
CORRECTION=('The previous answer failed the exact-answer check. Re-read this same CURRENT job and the supplied '
 'definitions; return the five boolean fields again. No answer values are supplied in this feedback.')

def build():
 plan={'kind':'ainglish.executed-dialogue-costs.v1','governance_evidence':False,
  'snapshot':'/home/dexagon/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28',
  'reader':'Offline native Qwen2.5-7B, GPU0 NF4 double quantization BF16, greedy, inherited seed20260906',
  'context_window_tokens':8192,'output_cap':256,'max_prompt_tokens':7936,
  'qualification':'16 fresh neutral five-field records; at least14/16 exact correct and zero truncations. No language calls on failure.',
  'policies':['history-once','lookup-per-turn'],'arms':['ainglish','english'],'turns':32,
  'dictionary':'Both complete phrase guides are published. history-once reads its guide once and retains actual messages/answers. lookup-per-turn physically reads its local JSON guide at each turn and uses only the current job, except a conditional same-turn correction.',
  'corrections':'Exactly one additional attempt after each incorrect, malformed or truncated first pass, provided it fits. A gold-oracle check triggers generic feedback without gold bits. This is teacher-assisted repair, not autonomous error detection. Keep all original costs and outcomes.',
  'limits':['8192 is the chosen working window, checked against model capacity, not a claim about its maximum supported length.',
   'Stop a history conversation before a request exceeding7936 prompt tokens; never truncate or summarize history or pretend unexecuted turns succeeded.',
   'Report matched completed prefixes1/2/4/8/16/32 only, with first-pass and after-correction accuracy separate.',
   'Four synthetic conversations on one English-trained model, not independent readers, governance evidence or a trained Ainglish model.',
   'Exact input/generated token IDs and actual dictionary bytes/read latency are retained. No KV-cache billing discounts or provider invoice costs are assumed.',
   'No adapter training, downloads, external actions, stochastic retries or post-hoc success selection.']}
 order=list(product([False,True],repeat=5));random.Random(20260907013).shuffle(order)
 cases=[]
 for i,bits in enumerate(order):
  brief=dict(zip(FIELDS,bits))
  context=f'CURRENT independent job lens-{8100+i}. You are Mira, coordinating a telescope lens inspection with Noor and Ivo. The named check is examining the lens coating. This job starts a fresh authorized A/B instruction ledger; identical labels in previous jobs refer to different closed ledgers.'
  cases.append({'id':f'lens-{8100+i}','brief':brief,'context':context,'messages':{a:render(brief,a) for a in PHRASES}})
 controls=[]
 names=['flexible','reflective','magnetic','transparent','scented']
 words=[('rigid','flexible'),('matte','reflective'),('nonmagnetic','magnetic'),('opaque','transparent'),('odourless','scented')]
 for i in range(16):
  bits=[bool(i&(1<<j)) for j in range(4)];bits.append(bits[0]^bits[1]^bits[2]^bits[3])
  brief=dict(zip(names,bits));table='\n'.join(f'{n}: false={w[0]}; true={w[1]}.' for n,w in zip(names,words))
  record=f'Inspection tile {5100+i}: '+', '.join(w[int(b)] for w,b in zip(words,bits))+'.'
  controls.append({'id':str(5100+i),'brief':brief,'messages':scoped.interface(names,record,table,'\n'.join(f'{n}: Is the tile {w[1]}?' for n,w in zip(names,words)))})
 save_new(ROOT/'PLAN.json',plan);save_new(ROOT/'cases.json',cases);save_new(ROOT/'controls.json',controls)
 save_new(ROOT/'dictionary.json',{arm:guide(arm) for arm in PHRASES})
 names=['study.py','test_study.py','README.md','PLAN.json','cases.json','controls.json','dictionary.json',
  '../overnight-runtime-2026-09-06/runtime.py','../communication-diagnostics-2026-09-06/design.py',
  '../communication-diagnostics-2026-09-06/source-constructs.json','../field-scoped-communication-2026-09-07/study.py']
 save_new(ROOT/'FROZEN.json',{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})

def current(case,arm):
 return COMMON+'\n'+case['context']+'\nCURRENT message:\n'+case['messages'][arm]+'\nQuestions:\n'+'\n'.join(f'{f}: {q}' for f,q in zip(FIELDS,MEANINGS))
def prompt_size(reader,messages):
 return len(reader.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True))
def score(raw,ended,gold):return bool(ended and scoped.decode(raw,gold)==gold)

def run():
 commit=verify_freeze(ROOT);plan=json.loads((ROOT/'PLAN.json').read_text())
 available=next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
 if available<14*1024**3:raise RuntimeError('Wait for at least14GiB available RAM before loading; no eviction')
 reader=LocalReader(plan['snapshot'])
 assert reader.model.config.max_position_embeddings>=plan['context_window_tokens']
 with Journal(ROOT/'execution/calls.jsonl',{'freeze':commit,**plan}) as journal:
  save_new(ROOT/'execution/provenance.json',reader.provenance)
  checks=[]
  for c in json.loads((ROOT/'controls.json').read_text()):
   r=reader.call(journal,'neutral/'+c['id'],c['messages'],cap=plan['output_cap'],max_prompt_tokens=plan['max_prompt_tokens'])
   checks.append({'id':c['id'],'correct':score(r['raw'],r['ended'],c['brief']),'truncated':not r['ended']})
  qualified=sum(r['correct'] for r in checks)>=14 and not any(r['truncated'] for r in checks)
  save_new(ROOT/'execution/qualification.json',{'qualified':qualified,'checks':checks})
  print('Neutral screen',sum(r['correct'] for r in checks),'/16',qualified,flush=True)
  rows=[];stops=[];reads=[]
  def lookup(arm,policy,turn):
   started=time.perf_counter();raw=(ROOT/'dictionary.json').read_bytes();text=json.loads(raw)[arm]
   reads.append({'arm':arm,'policy':policy,'turn':turn,'bytes_read':len(raw),'selected_text_utf8_bytes':len(text.encode()),'read_seconds':time.perf_counter()-started,'sha256':hashlib.sha256(raw).hexdigest()})
   return text
  if qualified:
   for policy in plan['policies']:
    for arm in plan['arms']:
     history=[{'role':'system','content':SYSTEM+'\n'+lookup(arm,policy,0)}] if policy=='history-once' else None
     for i,c in enumerate(json.loads((ROOT/'cases.json').read_text()),1):
      messages=history+[{'role':'user','content':current(c,arm)}] if history is not None else [
       {'role':'system','content':SYSTEM+'\n'+lookup(arm,policy,i)},{'role':'user','content':current(c,arm)}]
      n=prompt_size(reader,messages)
      if n>plan['max_prompt_tokens']:
       stops.append({'policy':policy,'arm':arm,'turn':i,'phase':'first','prompt_tokens':n,'reason':'context_limit_before_spend'});break
      key=f'{policy}/{arm}/{i}'
      r=reader.call(journal,key+'/first',messages,cap=plan['output_cap'],max_prompt_tokens=plan['max_prompt_tokens'],metadata={'turn':i,'policy':policy,'arm':arm})
      first=score(r['raw'],r['ended'],c['brief']);messages=messages+[{'role':'assistant','content':r['raw']}]
      row={'policy':policy,'arm':arm,'turn':i,'id':c['id'],'first_correct':first,'final_correct':first,'correction_called':False,
       'input_tokens':r['input_tokens'],'output_tokens':r['output_tokens'],'truncations':int(not r['ended']),'latency_s':r['latency_s']}
      if not first:
       correction=messages+[{'role':'user','content':CORRECTION}];n=prompt_size(reader,correction)
       if n<=plan['max_prompt_tokens']:
        r=reader.call(journal,key+'/correction',correction,cap=plan['output_cap'],max_prompt_tokens=plan['max_prompt_tokens'],metadata={'turn':i,'policy':policy,'arm':arm,'gold_oracle_trigger':True})
        row['correction_called']=True;row['final_correct']=score(r['raw'],r['ended'],c['brief'])
        for k in ['input_tokens','output_tokens','latency_s']:row[k]+=r[k]
        row['truncations']+=int(not r['ended']);messages=correction+[{'role':'assistant','content':r['raw']}]
       else:
        row['correction_blocked_by_context']=True
        stops.append({'policy':policy,'arm':arm,'turn':i,'phase':'correction','prompt_tokens':n,'reason':'context_limit_before_spend'})
      rows.append(row)
      if history is not None:history=messages
      print(policy,arm,i,'first',row['first_correct'],'final',row['final_correct'],'tokens',row['input_tokens']+row['output_tokens'],flush=True)
      if row.get('correction_blocked_by_context'):break
  groups={(p,a):[r for r in rows if r['policy']==p and r['arm']==a] for p in plan['policies'] for a in plan['arms']}
  minimum=min(map(len,groups.values()))
  summaries=[]
  for horizon in [1,2,4,8,16,32]:
   if horizon>minimum:continue
   for (policy,arm),group in groups.items():
    part=group[:horizon]
    summaries.append({'policy':policy,'arm':arm,'completed_prefix':horizon,
     **{k:sum(r[k] for r in part) for k in ['first_correct','final_correct','correction_called','input_tokens','output_tokens','truncations','latency_s']}})
  save_new(ROOT/'RESULTS.json',{'freeze':commit,'qualified':qualified,'rows':rows,'stops':stops,'dictionary_reads':reads,'matched_prefix_summaries':summaries,'limits':plan['limits']})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);args=p.parse_args()
 build() if args.action=='build' else run()
