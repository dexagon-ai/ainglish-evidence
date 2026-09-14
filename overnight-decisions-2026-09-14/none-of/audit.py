"""Finite-gold and actual SDK HTTP-payload audit, with sockets forbidden."""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from ainglish import panel
from build import ROOT, FORMS, permitted, digest, write

def payload(reader,item,arm):
 captured=[]
 ep=deepcopy(reader)
 ep[panel._INSTRUMENT_PREPARATION_KEY]={'binding':'OFFLINE-AUDIT-NOT-QUALIFICATION','entry_point':'offline-payload-audit'}
 def fake(request,timeout=None):
  assert request.full_url=='http://127.0.0.1:11434/v1/chat/completions'
  captured.append(json.loads(request.data))
  return {'choices':[{'message':{'content':'A'},'finish_reason':'stop'}]}
 with patch('socket.socket',side_effect=AssertionError('No network in audit')),patch.object(panel,'_fetch',fake):
  panel.ask(ep,item[arm],item['question'],item['options'])
 assert len(captured)==1
 return captured[0]

def main():
 report={'kind':'offline-structural-audit-not-language-evidence','reader_calls':0,'banks':{}}
 all_pairs={}
 for name in ['primary','consequences','learning']:
  spec=json.loads((ROOT/(name+'.runspec.json')).read_text())
  items=json.loads((ROOT/(name+'.items.json')).read_text())
  assert digest(items)==spec['items_sha256']
  real=[r for r in items if not r.get('calibration')]
  assert len(real)==len({r['id'] for r in real})
  pairs={(r['english'],r['ainglish'],r['question']) for r in real}
  assert len(pairs)==len(real)
  all_pairs[name]=pairs
  captured=[]
  for r in real:
   assert r['answer'] in r['options'] and len(r['options'])==len(set(r['options']))
   assert r['strata']['form']==r['settlement_stratum']
   if name=='primary':
    f=r['settlement_stratum'];n=r['strata']['set_size']
    gold='Exactly k=0' if f=='none-of' else f'Any integer k from 0 through {n-1}'
    assert r['answer']==gold and r['audit_only']['allowed_counts']==sorted(permitted(f,n))
   for ep in spec['panel']:
    for arm in ['english','ainglish']:
     raw=payload(ep,r,arm)
     poisoned=deepcopy(r)
     poisoned['answer']='SENTINEL-HIDDEN-GOLD'
     poisoned['settlement_stratum']='SENTINEL-HIDDEN-FORM'
     poisoned['audit_only']={'secret':'SENTINEL-METADATA'}
     assert raw==payload(ep,poisoned,arm)
     assert 'SENTINEL' not in json.dumps(raw)
     assert set(raw)=={'model','temperature','seed','max_tokens','messages'}
     assert len(raw['messages'])==1 and raw['messages'][0]['role']=='user'
     captured.append({'reader':ep['name'],'item':r['id'],'arm':arm,'body':raw})
  # Detect whether context/question/menu alone exposes hidden intended interval in twins.
  views=defaultdict(Counter)
  if name=='primary':
   for r in real:
    context=r['english'].rsplit('. ',1)[0]
    views[(context,r['question'],tuple(r['options']))][r['answer']]+=1
   assert len(views)==224 and all(len(c)==2 for c in views.values())
   assert sum(max(c.values()) for c in views.values())==224
  raw=json.dumps(captured,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
  # A digest suffices to bind this mechanically reproducible capture. Avoid a multi-MB duplicate.
  report['banks'][name]={'real_items':len(real),'both_arm_http_payloads_audited':len(captured),
   'http_capture_sha256':hashlib.sha256(raw).hexdigest(),'metadata_poisoning_payload_identity':True,
   'answer_positions':dict(Counter(r['options'].index(r['answer']) for r in real)),
   'items_sha256':spec['items_sha256'],'context_only_maximum_hidden_intent_recovery':224 if name=='primary' else None}
 for a in all_pairs:
  for b in all_pairs:
   if a!=b: assert not all_pairs[a]&all_pairs[b]
 report['limits']=['Same-investigator audit, not independent review.',
  'Finite scenario oracle and payload isolation do not prove empirical comprehension.',
  'Repeated predicates, domain frames and multiple probes are correlated; row count is not population diversity.',
  'The primary twin context bound is limited to this authored paired envelope, not arbitrary language.']
 write('STRUCTURAL-AUDIT.json',report)
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()
