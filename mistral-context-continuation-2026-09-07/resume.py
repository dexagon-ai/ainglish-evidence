"""Continue only unspent cells after a resource guard, retaining the original chain."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'mistral-context-transfer-2026-09-07'
spec=importlib.util.spec_from_file_location('unchanged_mistral_study',OLD/'study.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import Journal,save_new,verify_freeze,digest,disk_guard

def build():
 original=verify_freeze(OLD);path=OLD/'execution/calls.jsonl'
 events=Journal._validate(path.read_text());begins={r['data']['call_id']:r['data'] for r in events if r['kind']=='begin'}
 ends={r['data']['call_id']:r['data'] for r in events if r['kind']=='end'}
 assert begins.keys()==ends.keys() and len(ends)==131
 assert not (OLD/'RESULTS.json').exists()
 save_new(ROOT/'PLAN.json',{'kind':'ainglish.resource-stop-continuation.v1','original_freeze':original,
  'journal_prefix_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'journal_prefix_bytes':path.stat().st_size,
  'completed_calls':list(ends),'completed_count':131,'completed_neutral':32,'completed_reference':99,
  'remaining_reference_calls':93,'conditional_sender_handoff_calls':384,
  'stop':'The original process exited before another begin when its RAM-or-shared-caller guard fired. The contemporaneous disjunct was not recorded, so neither RAM pressure nor another caller is asserted as the sole cause.',
  'recovery':'All131 calls have complete hash-matched ends. Cache-replay only those exact requests without an API call; append only never-started cells. Same source bytecode/renderers,gold,reader digest,CPU8-thread options,8192context,512output and original fixed order. Original screen passes remain the screen; no new controls or model substitution.',
  'boundary':'This is completion of an interrupted run, not an independent replication or a new attempt at previously answered cells. Do not change inclusion based on partial outcomes. If a new call becomes uncertain, stop again without inference retry.',
  'qualification_sha256':hashlib.sha256((OLD/'execution/qualification.json').read_bytes()).hexdigest()})
 save_new(ROOT/'FROZEN.json',{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['resume.py','PLAN.json','../mistral-context-transfer-2026-09-07/study.py','../overnight-runtime-2026-09-06/runtime.py']})
 print('Frozen exact unspent-tail continuation;no model calls.')

def run():
 continuation=verify_freeze(ROOT);original=verify_freeze(OLD)
 recovery=json.loads((ROOT/'PLAN.json').read_text());plan=json.loads((OLD/'PLAN.json').read_text())
 path=OLD/'execution/calls.jsonl';raw=path.read_bytes()
 assert original==recovery['original_freeze']
 assert len(raw)==recovery['journal_prefix_bytes'] and hashlib.sha256(raw).hexdigest()==recovery['journal_prefix_sha256']
 assert hashlib.sha256((OLD/'execution/qualification.json').read_bytes()).hexdigest()==recovery['qualification_sha256']
 assert not m.api('ps')['models'],'Shared service occupied;no eviction'
 tags={r['name']:r for r in m.api('tags')['models']}
 assert tags[m.MODEL]['digest']==m.DIGEST
 assert m.available_ram()>=tags[m.MODEL]['size']*1.1+4*1024**3,'Wait for safe RAM without evicting another task'
 save_new(ROOT/'execution/intent.json',{'continuation':continuation,'original':original,'retries':0})
 with Journal(path,{'freeze':original,**plan},resume=True) as journal:
  def call(key,messages):
   request={'model':m.MODEL,'messages':messages,'stream':False,'keep_alive':'5m','options':m.OPTIONS}
   cached=journal.lookup(key,request)
   if cached is not None:
    response=cached['response'];return cached['raw'],response.get('done') is True and response.get('done_reason')=='stop'
   disk_guard()
   if m.available_ram()<3*1024**3 or any(r['name']!=m.MODEL for r in m.api('ps')['models']):
    raise RuntimeError('Resource/shared-caller guard before new spend;no retry')
   journal.begin(key,request);started=m.time.monotonic();response=m.api('chat',request);resident=m.api('ps')['models']
   row=journal.end(key,{'raw':response['message']['content'],'response':response,'resident_after':resident,'latency_s':m.time.monotonic()-started})
   assert resident and all(r.get('size_vram',-1)==0 for r in resident if r['name']==m.MODEL),'CPU placement not confirmed;retain without retry'
   return row['raw'],response.get('done') is True and response.get('done_reason')=='stop'
  # Verify every prior neutral request while reconstructing, never spend it again.
  controls=json.loads((OLD/'controls.json').read_text());checks={}
  for role in ['reader','writer']:
   rows=[]
   for c in controls[role]:
    raw,ended=call('qualification/'+role+'/'+c['id'],c['messages'])
    correct=m.decode(raw,c['brief'])==c['brief'] if role=='reader' else m.fixed_lines(raw)==m.fixed_lines(c['gold'])
    rows.append({'id':c['id'],'correct':ended and correct,'truncated':not ended})
   checks[role]={'passed':sum(r['correct'] for r in rows)>=14 and not any(r['truncated'] for r in rows),'rows':rows}
  assert checks==json.loads((OLD/'execution/qualification.json').read_text())
  targets=json.loads((OLD/'cases.json').read_text());references=[];handoffs=[]
  if checks['reader']['passed']:
   for c in targets:
    for arm in ['ainglish','english']:
     raw,ended=call('reference/'+c['id']+'/'+arm,m.reader_messages(c,arm,c['messages'][arm]))
     parsed=m.decode(raw,c['brief']);references.append({'id':c['id'],'arm':arm,'parsed':parsed is not None,'correct':ended and parsed==c['brief'],'truncated':not ended})
     if len(references)%24==0:print('Verified or completed references',len(references),'/192',flush=True)
  gate=len(references)==192 and all(sum(r['correct'] for r in references if r['arm']==arm)>=.8*96 and not any(r['truncated'] for r in references if r['arm']==arm) for arm in ['ainglish','english'])
  save_new(OLD/'execution/reference-gate.json',{'passed':gate,'references':references})
  if gate and checks['writer']['passed']:
   def choice(brief):return {'team':'include' if brief['include_recipient'] else 'exclude','work':'one' if brief['collective'] else 'each','deadline':'complete' if brief['finish_deadline'] else 'start'}
   for c in targets:
    fixture=json.dumps({'inventory':[{'case':c['id'],'checked_item':'bounded demonstration'}]},sort_keys=True).encode()
    for arm in ['ainglish','english']:
     messages=m.sender_messages(c,arm);messages[0]['content']+=' Use no more than one terminal full stop per line; no Markdown fences.'
     raw,writer_ended=call('sender/'+c['id']+'/'+arm,messages);sender=m.parse_writer(raw,arm)
     reply,ended=call('handoff/'+c['id']+'/'+arm,m.reader_messages(c,arm,raw));received=m.decode(reply,c['brief'])
     row={'id':c['id'],'arm':arm,'sender_parsed':sender is not None,'sender_correct':writer_ended and sender==c['brief'],
      'sender_truncated':not writer_ended,'receiver_parsed':received is not None,'receiver_correct':ended and received==c['brief'],
      'receiver_tracks_sender':None if sender is None else ended and received==sender,'receiver_truncated':not ended,'execution':None}
     if writer_ended and ended and received is not None:
      receipt=m.execute(choice(received),fixture,instrument_qualified=True)
      row['execution']={'receipt':receipt,'follows_intended_plan':m.follows_intended_plan(receipt,choice(c['brief'])),'task_success':m.success(receipt,choice(c['brief']),fixture)}
     handoffs.append(row)
     if len(handoffs)%24==0:print('Handoffs',len(handoffs),'/192',flush=True)
  save_new(OLD/'RESULTS.json',{'freeze':original,'continuation_freeze':continuation,'governance_evidence':False,'qualification':checks,'reference_gate':gate,'references':references,'handoffs':handoffs,'limits':plan['limits']+[recovery['boundary']]})
 loaded=m.api('ps')['models']
 if loaded and all(r['name']==m.MODEL for r in loaded):m.api('generate',{'model':m.MODEL,'keep_alive':0})
 print('Finished without repeating completed inference',len(references),len(handoffs),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);a=p.parse_args()
 build() if a.action=='build' else run()
