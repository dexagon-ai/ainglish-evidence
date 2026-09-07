"""Official SDK original with public freeze, freshness gates and durable wire receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone
from unittest.mock import patch
import urllib.request
from ainglish import estimand,panel,reader_qualification
from local_colony_auth import ainglish_client
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import Journal,save_new,verify_freeze,disk_guard
BASE='http://127.0.0.1:11438'
def read(name):return json.loads((ROOT/name).read_text())
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def fresh(client):
 plan=read('PLAN.json');client.suggestions(proposal=plan['public_id'])
 p=client.proposal(plan['slug'],authenticated=True)
 assert p['stage'] in ['seconded','measured'] and p['publication_status']=='visible'
 assert p['english_mapping']==read('proposal.json')['english_mapping']
 readiness=p['evidence_readiness'];satisfied=readiness['satisfied']
 assert all((x if isinstance(x,str) else x['metric']) in satisfied for x in readiness['prerequisites'])
 return p
def prepare():
 commit=verify_freeze(ROOT);plan=read('PLAN.json')
 screens=json.loads((ROOT.parent/'qualified-comprehension-2026-09-07/screens.json').read_text())
 qualified=json.loads((ROOT.parent/'qualified-comprehension-2026-09-07/qualification/RESULTS.json').read_text())
 assert qualified['panel_admitted']
 readers=[s['reader'] for s in screens];qualifications=[r['receipt'] for r in qualified['results']]
 client=ainglish_client();p=fresh(client)
 spec={'slug':p['slug'],'construct':p['form'],'metric':'comprehension_accuracy_delta','seed':plan['seed'],
  'panel':readers,'models':[q['roster_id'] for q in qualifications],'panel_neff':2,
  'planted_arm':'ainglish','calibration_min_gap':.5,'calibration_min_recovered':.95,
  'study_purpose':'claim_test','study_scope':'Focused joint price/allocation recovery on128 cells,eight domain frames,both forms,affirmation/negation and disclosed/undisclosed other-axis facts. Not full claim completion: no bare gain,direct permission/health inference or edit robustness is established.',
  'admissibility':{'kind':'ainglish.panel.admissibility.v1','per_reader_calibration':True,
   'max_off_option_cells':0,'max_absent_cells':0,'max_truncated_cells':0,'max_transport_fault_cells':0},
  'comparator':{'kind':'complete-careful-english-v1','description':'Same complete scoped claim and shared facts; shortest adequate meaning-complete English for invoice charge or present allocation. No bare ambiguity arm in this scalar.'},
  'comparison_identity':{'comparator_genre':'complete-careful-english-v1','exposure':'cold-no-added-reference',
   'pair_rendering':'price-allocation-joint-128-v1','reader_class':'Two fixed qualified cached ctx4k Q4 readers;serial reader-outermost cells',
   'form_strata':['no-charge','available-now']},
  'settlement_strata':[{'id':f,'weight':1} for f in ['no-charge','available-now']],
  'items_url':f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/items.json',
  'items_sha256':hashlib.sha256(canonical(read('items.json'))).hexdigest(),
  'estimand_contract':estimand.declaration_v2(population=plan['population'],
   item_set_construction={'design':'price-allocation-joint-128-v1','items':128,'domains':8,'forms':2,
    'answer_format':'one opaque choice from9 joint yes/no/not-determined vectors','unknown':'unreported other axis is not determined',
    'negation':'ordinary scoped negation included and reported apart'},
   reader_class='Exact Gemma12 and Mistral24 literal-reader ctx4k Q4 derivatives;temperature0,output128,seed20260907031',
   window='stateless cold single-shot cells;serial reader blocks after all calibration;no target retries',
   selection_rules={'weighting':'equal form strata;all domains,polarities and information states retained',
    'gates':'both neutral screens passed,per-reader calibration,zero transport/yield faults',
    'publication':'every finite admitted direction filed;failed gate retained without rerun'}),
  'attempt':{'proposal_revision':p['slug'],'estimand':'New original:128 complete joint price/allocation cases in two equal form strata;two fixed qualified cached readers;Ainglish minus careful-English accuracy. Report adverse/null values and absolute accuracies. No bare-arm or full-prediction completion claim.',
   'admissibility_gates':plan['gates'],
   'planned_sample':{'scientific_items':128,'calibration_items':8,'readers':2,'target_calls':256,'calibration_calls':32,
    'source_commit':commit,'mapping_sha256':hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
    'qualification_results_sha256':hashlib.sha256((ROOT.parent/'qualified-comprehension-2026-09-07/qualification/RESULTS.json').read_bytes()).hexdigest()}}}
 spec=reader_qualification.attach(spec,qualifications)
 items,digest=panel.fetch_items(spec['items_url'],spec['items_sha256']);manifest=dict(spec,items=items,items_sha256=digest)
 panel.prepare_reader_instruments(manifest)
 planned=panel._planned_panel_manifest(manifest)
 settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(manifest),panel.admissibility_gate_statement(manifest)])
 preflight=client.preflight_attempt(spec['slug'],planned,**settings)
 save_new(ROOT/'derived/runspec.json',spec);save_new(ROOT/'derived/planned.json',planned)
 save_new(ROOT/'derived/preflight.json',preflight)
 save_new(ROOT/'derived/PINS.json',{n:hashlib.sha256((ROOT/'derived'/n).read_bytes()).hexdigest() for n in ['runspec.json','planned.json','preflight.json']})
 print('Live preflight passed;publish derived pins before mint. No targets called.')
def run():
 freeze=verify_freeze(ROOT);client=ainglish_client();fresh(client)
 pinpath=ROOT/'derived/PINS.json'
 commit=subprocess.check_output(['git','log','-1','--format=%H','--',str(pinpath)],cwd=ROOT.parent,text=True).strip()
 subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
 for n,h in read('derived/PINS.json').items():
  p=ROOT/'derived'/n;assert hashlib.sha256(p.read_bytes()).hexdigest()==h
  assert subprocess.check_output(['git','show',f'{commit}:{ROOT.name}/derived/{n}'],cwd=ROOT.parent)==p.read_bytes()
 assert not (ROOT/'execution/intent.json').exists(),'Reconcile;never remint or rerun targets'
 spec=read('derived/runspec.json')
 for q in spec['reader_qualifications']:assert datetime.fromisoformat(q['valid_until'])>datetime.now(timezone.utc)
 items,digest=panel.fetch_items(spec['items_url'],spec['items_sha256']);manifest=dict(spec,items=items,items_sha256=digest)
 panel.prepare_reader_instruments(manifest)
 assert panel._planned_panel_manifest(manifest)==read('derived/planned.json')
 opened={};original_mint=client.mint_attempt;original_chat=panel.chat;ordinal=0
 save_new(ROOT/'execution/intent.json',{'freeze':freeze,'derived_commit':commit,'retries':0})
 with Journal(ROOT/'execution/wire.jsonl',{'freeze':freeze,'derived_commit':commit}) as journal:
  def mint(*args,**kwargs):
   receipt=original_mint(*args,**kwargs);save_new(ROOT/'execution/opened.json',receipt);opened.update(receipt);return receipt
  def chat(reader,prompt):
   nonlocal ordinal
   assert opened;disk_guard();ordinal+=1
   journal.begin(str(ordinal),{'reader':reader,'prompt':prompt,'attempt_id':opened['attempt']['attempt_id']})
   raw,truncated=original_chat(reader,prompt)
   with urllib.request.urlopen(BASE+'/api/ps',timeout=15) as r:resident=json.load(r)['models']
   journal.end(str(ordinal),{'raw':raw,'truncated':truncated,'resident':resident})
   if not resident or any(m['name']!=reader['model'] or m['size_vram']<.9*m['size'] for m in resident):
    raise RuntimeError('Owned GPU-only model-placement check failed after retained call;no retry')
   if ordinal%32==0:print('Offer comprehension',ordinal,'calls retained',flush=True)
   return raw,truncated
  with patch.object(client,'mint_attempt',side_effect=mint),patch.object(panel,'chat',side_effect=chat):
   result=panel._run_preregistered_panel(manifest,spec,panel.ask,client,receipt_dir=str(ROOT/'execution'),receipt_stem='offer')
  if result is not None:
   save_new(ROOT/'execution/result.json',result);save_new(ROOT/'execution/after.json',client.proposal(spec['slug'],authenticated=True))
  save_new(ROOT/'execution/finished.json',{'calls':ordinal,'status':'filed' if result is not None else 'aborted','value':result['value'] if result else None})
  print('Offer original','filed' if result is not None else 'aborted',ordinal,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args()
 prepare() if a.action=='prepare' else run()
