"""Offline logical, freshness and actual HTTP-body audit; not empirical evidence."""
from collections import Counter
from copy import deepcopy
from datetime import datetime,timedelta
import hashlib,json
from itertools import product
from pathlib import Path
import sys
from unittest.mock import patch
from ainglish import panel
from build import ROOT,AUDIT,gold,write,digest

def captured(ep,item,arm):
 ep=deepcopy(ep);ep[panel._INSTRUMENT_PREPARATION_KEY]={'entry_point':'OFFLINE-ONLY','binding':'NOT-QUALIFICATION'}
 bodies=[]
 def fetch(request,timeout=None):
  assert request.full_url=='http://127.0.0.1:11434/v1/chat/completions'
  bodies.append(json.loads(request.data))
  return {'choices':[{'message':{'content':'A'},'finish_reason':'stop'}]}
 with patch('socket.socket',side_effect=AssertionError('No sockets in audit')),patch.object(panel,'_fetch',fetch):
  panel.ask(ep,item[arm],item['question'],item['options'])
 assert len(bodies)==1
 return bodies[0]

def main():
 spec=json.loads((ROOT/'runspec.draft.json').read_text());items=json.loads((ROOT/'items.json').read_text())
 source=json.loads((AUDIT/'saturnia-verified-items-mirror.json').read_text())
 real=[r for r in items if not r.get('calibration')];prior=[r for r in source if not r.get('calibration')]
 assert digest(items)==spec['items_sha256']
 source_pairs={(r['english'],r['ainglish']) for r in prior};source_sides={r[arm] for r in prior for arm in ['english','ainglish']}
 assert len(real)==len({r['id'] for r in real})==144
 assert len({(r['english'],r['ainglish']) for r in real})==144
 assert not source_pairs&{(r['english'],r['ainglish']) for r in real}
 assert not source_sides&{r[arm] for r in real for arm in ['english','ainglish']}
 assert Counter(r['settlement_stratum'] for r in real)=={s['id']:24 for s in spec['settlement_strata']}
 actual=[]
 for r in real:
  a=r['audit_only'];f=a['facts'];branch=r['settlement_stratum']
  assert gold(f)==r['answer'] and len(set(r['options']))==4 and r['answer'] in r['options']
  assert r['english']==a['common']+a['meaning_english']
  assert r['ainglish']==a['common']+a['meaning_ainglish']
  if branch=='stale-check':
   assert datetime.fromisoformat(a['checked_at'])+timedelta(hours=a['ttl_hours'])<datetime.fromisoformat(a['now'])
  if branch=='verified-settled-coexistence':
   assert datetime.fromisoformat(a['checked_at'])+timedelta(hours=a['ttl_hours'])>datetime.fromisoformat(a['now'])
   assert 'AND settled(' in r['ainglish'] and r['answer']=='act'
  # Scoring-only metadata, branch names and gold never reach HTTP payloads.
  for ep in spec['panel']:
   for arm in ['english','ainglish']:
    body=captured(ep,r,arm)
    poisoned=deepcopy(r);poisoned['answer']='HIDDEN-GOLD';poisoned['audit_only']={'leak':'HIDDEN-GOLD'};poisoned['settlement_stratum']='HIDDEN-GOLD'
    assert body==captured(ep,poisoned,arm)
    assert 'HIDDEN-GOLD' not in json.dumps(body)
    actual.append(body)
 # Exhaustively enumerate precedence interactions; impossible simultaneous
 # demonstration claims are not generated but precedence remains deterministic.
 for nd,expired,discharged in product([False,True],repeat=3):
  assert gold({'non_discharge':nd,'expired':expired,'discharge':discharged})==('dispute' if nd else 're-verify' if expired else 'act' if discharged else 'wait')
 write('AUDIT.json',{'reader_calls':0,'source_complete_pair_overlap':0,'source_individual_arm_overlap':0,
  'real_items':144,'obligation_frames':24,'http_payloads':len(actual),'http_payload_sha256':digest(actual),
  'items_sha256':digest(items),'per_stratum':dict(Counter(r['settlement_stratum'] for r in real)),
  'answer_positions':dict(Counter(r['options'].index(r['answer']) for r in real)),
  'limits':['Own structural/logical audit, not independent validation or empirical comprehension.',
   'The mandatory policy and declared English mapping templates are shared with the source; newly authored obligation contexts are substantive, not merely relabelled original worlds.',
   '24 base obligation scenarios are crossed with six semantic states; all siblings are correlated.',
   'Zero exact source overlap does not prove semantic novelty of every possible prior discussion. Six published review fixtures were read and excluded.']})
 print('144 logical targets, 576 actual HTTP payloads audited, zero reader calls or source overlap')

if __name__=='__main__':main()
