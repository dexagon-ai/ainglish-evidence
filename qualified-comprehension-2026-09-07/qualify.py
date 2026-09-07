"""Target-independent SDK qualification on an owned GPU0 cached-model service."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
import urllib.request
from ainglish import panel,reader_qualification

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import Journal,save_new,verify_freeze,disk_guard
BASE='http://127.0.0.1:11438'
MODELS=[('Gemma12','dexagon-gemma3-12b-pp-task:ctx4k','de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f','gemma3'),
        ('Mistral24','dexagon-mistral-small3.2-24b-pp-task:ctx4k','6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de','mistral-small3.2')]
def api(path):
 with urllib.request.urlopen(BASE+'/api/'+path,timeout=15) as r:return json.load(r)
def controls(prefix,n=16):
 rows=[]
 colours=['ochre','teal','violet','indigo','copper','ivory','scarlet','umber']
 for i in range(n):
  order=colours[i%8:]+colours[:i%8];gold=colours[(2*i+1)%8]
  letter='ABCDEFGH'[order.index(gold)]
  question='Which colour does the record establish? '+ ' '.join(f'{k}={v}.' for k,v in zip('ABCDEFGH',order))+' I=not determined.'
  rows.append({'id':f'{prefix}-{i+6100}','detectable':f'The current label for tile {i+6100} states {gold}.',
   'other':f'The current label for tile {i+6100} is unavailable; its colour is not recorded.',
   'question':question,'options':list('ABCDEFGHI'),'answer':letter})
 return rows
def build():
 tags={x['name']:x['digest'] for x in api('tags')['models']}
 screens=[]
 for name,model,digest,lineage in MODELS:
  assert tags[model]==digest
  reader={'name':'Dexagon-Sept7-'+name,'provider':'ollama','model':model,'base_url':BASE+'/v1',
   'model_digest':'sha256:'+digest,'precision':'q4_k_m','answer_protocol':panel.ANSWER_PROTOCOL,
   'temperature':0,'max_tokens':128,'timeout_s':180,'seed':20260907031}
  screen={'kind':reader_qualification.SCREEN_KIND,'roster_id':reader['name']+'@q4_k_m','reader':reader,
   'lineage':{'key':lineage,'basis':'Distinct cached base families; derivatives include fixed literal-reader system prompt and4096 context. This does not establish independent training data.'},
   'controls':controls('reader-'+name),'validity_days':7,'min_gap_bps':5000,'min_recovered_bps':9500}
  reader_qualification.validate_screen(screen);screens.append(screen)
 save_new(ROOT/'screens.json',screens)
 save_new(ROOT/'QUALIFICATION-PLAN.json',{'kind':'ainglish.sept7-qualified-original-readers.v1','maximum_calls':64,
  'service':BASE,'physical_gpu':'GPU-a30417b6-2cc4-220a-d34d-f76dd9444456','models':MODELS,
  'screen':'16 independently authored neutral colour records per reader, both known and unknown arms,9 opaque answer labels. SDK>=.5 gap and>=.95 recovered headroom; separately>=.95 semantic accuracy per arm,zero truncations/off-option/absence/transport faults.',
  'order':'Gemma screen then Mistral screen, no target cells. Failed readers are not swapped or rescreened. The predefined two-reader panel requires both passes.',
  'boundaries':['All weights already cached in the user-readable Ollama cache. Owned loopback service isolated to physicalGPU0; existing CPU experiment and GPU1 workload untouched.',
   'Model aliases include existing4096-context Modelfile and fixed literal-reader system text; they are not the unmodified original aliases and cannot impersonate an exact-digest replication.',
   'This screen tests the answer interface and missing-information handling, not any Ainglish proposal or future training benefit.',
   'No governance attempt is minted for neutral qualification; language originals require separately published inputs, preregistration, calibration and fresh readiness checks.']})
 save_new(ROOT/'FROZEN.json',{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['qualify.py','screens.json','QUALIFICATION-PLAN.json','../overnight-runtime-2026-09-06/runtime.py']})
 print('64 neutral calls planned; zero model calls so far.')
def run():
 commit=verify_freeze(ROOT);plan=json.loads((ROOT/'QUALIFICATION-PLAN.json').read_text())
 screens=json.loads((ROOT/'screens.json').read_text());results=[]
 assert not api('ps')['models'],'Owned service should begin empty; no eviction'
 with Journal(ROOT/'qualification/calls.jsonl',{'freeze':commit,**plan}) as journal:
  original=panel.chat;ordinal=0;faults=[]
  def chat(reader,prompt):
   nonlocal ordinal
   disk_guard();ordinal+=1;request={'reader':reader,'prompt':prompt}
   journal.begin(str(ordinal),request)
   raw,truncated=original(reader,prompt)
   resident=api('ps')['models']
   journal.end(str(ordinal),{'raw':raw,'truncated':truncated,'resident':resident})
   if not resident or any(m['name']!=reader['model'] or m.get('size_vram',0)<.9*m['size'] for m in resident):
    raise RuntimeError('Unexpected resident or GPU placement: preserve answer without retry')
   if truncated or raw.strip() not in list('ABCDEFGHI'):faults.append(ordinal)
   return raw,truncated
  with patch.object(panel,'chat',side_effect=chat):
   for screen in screens:
    start_faults=len(faults)
    r=reader_qualification.run_screen(screen)
    semantic={cell:sum(o['answer']==(o['expected'] if cell=='detectable' else 'I') for o in r['observations'] if o['cell']==cell)/16 for cell in ['detectable','other']}
    admitted=r['status']=='passed' and min(semantic.values())>=.95 and len(faults)==start_faults
    r['assessment']={'semantic_accuracy':semantic,'admitted':admitted,'faults':faults[start_faults:]}
    save_new(ROOT/'qualification'/(screen['reader']['name']+'.json'),r);results.append(r)
    print(screen['reader']['name'],r['status'],semantic,'admitted',admitted,flush=True)
  save_new(ROOT/'qualification/RESULTS.json',{'freeze':commit,'panel_admitted':all(r['assessment']['admitted'] for r in results),'results':results,'calls':ordinal,'target_calls':0})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);a=p.parse_args()
 build() if a.action=='build' else run()
