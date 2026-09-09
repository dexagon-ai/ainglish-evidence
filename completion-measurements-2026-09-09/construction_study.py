"""Fresh-input legacy replication, preserving the three exact source-reader contracts."""
import copy,hashlib,json,shutil,subprocess,sys,urllib.request
from unittest.mock import patch
from ainglish import panel,reader_qualification
from local_colony_auth import ainglish_client
from reader_campaign import ROOT,save,load,local,FLOOR,START,require_resources

OUT=ROOT/'construction';PID='a-0w08sbp8900wxtqb';SLUG='by-construction-by-rule-in-practice'
TARGET='40702354347269f4230a1e2964522d8da3081fc7a188229204a00b833dba0d0e'
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def fresh():
 c=ainglish_client();s=c.suggestions(proposal=PID);p=c.proposal(SLUG,authenticated=True);m=c.measurement(TARGET)
 assert any(x.get('replicates_hash')==TARGET for x in s['suggestions'])
 assert m['evidence_state']=='valid' and not m['confirmed'] and not m.get('retraction')
 return c,p,m
def prepare():
 c,p,m=fresh();readers=[]
 for source in m['manifest']['readers']:
  readers.append({k:source[k] for k in ('name','provider','model','api','base_url','model_digest','answer_protocol','max_tokens','timeout_s','temperature')})
 readers=panel.prepare_reader_instruments({'panel':readers})['panel']
 access=c.reader_access(TARGET,[panel.reader_receipt(r) for r in readers]);assert access['status']=='matching_inventory'
 save(OUT/'source.json',m);save(OUT/'access.json',access)
 tags={x['name']:x for x in local('/api/tags')['models']}
 controls=[]
 for n,name in enumerate(('Elm','Fir','Holly','Iris','Juniper','Larch','Maple','Pine')):
  controls.append({'id':f'construction-reader-screen-{n}',
   'detectable':f'The signed receipt for parcel DZ-{270+n} names {name} as collector.',
   'other':f'The signed receipt for parcel DZ-{270+n} omits the collector.',
   'question':f'Who collected parcel DZ-{270+n}?','options':['Elm','Fir','Holly','Iris','Juniper','Larch','Maple','Pine'],'answer':name})
 for n,r in enumerate(readers):
  tag=tags[r['model']];assert 'sha256:'+tag['digest']==r['model_digest']
  screen={'kind':reader_qualification.SCREEN_KIND,'roster_id':r['name'],'reader':r,
   'receipt_precision':tag['details']['quantization_level'],
   'lineage':{'key':('qwen2.5','gemma3','mistral-small3.2')[n],
    'basis':'Exact cached source weights and answer settings. Plain roster preserved; quantization is descriptive receipt metadata. Base families do not prove independent training data.'},
   'controls':controls,'validity_days':7,'min_gap_bps':5000,'min_recovered_bps':10000}
  reader_qualification.validate_screen(screen);save(OUT/f'qualification-screen-{n}.json',screen)
 blocks={
 'b':[
 ('Ledger offsets increase strictly','A ledger offset decreases',''),('Compiled packets carry a length field','A compiled packet lacks its length field',''),
 ('Object handles resolve to one allocation','An object handle resolves to two allocations',''),('Encoded counters are nonnegative','An encoded counter is negative',''),
 ('Queue slots hold at most one task','A queue slot holds two tasks',''),('Committed rows have a primary identifier','A committed row has no primary identifier',''),
 ('Survey records bind one questionnaire version','A survey record binds two questionnaire versions',''),('Seat tickets bind one departure date','A seat ticket binds no departure date',''),
 ('Grant receipts include a recipient identifier','A grant receipt lacks a recipient identifier',''),('Museum entry passes carry an expiry date','A museum entry pass has no expiry date',''),
 ('Appointment records refer to an existing clinic','An appointment record refers to no existing clinic',''),('Permit records include a issuing-office code','A permit record omits its issuing-office code','')],
 'r':[
 ('service credentials rotate quarterly','A service credential is not rotated during the quarter','security lead'),
 ('test failures receive a tracking ticket','A test failure receives no tracking ticket','quality lead'),
 ('data corrections retain an audit explanation','A data correction has no audit explanation','data steward'),
 ('external dependencies receive a licence review','An external dependency receives no licence review','maintainer'),
 ('expired sessions are removed daily','An expired session is not removed that day','service owner'),
 ('recovery drills include a signed report','A recovery drill has no signed report','operations lead'),
 ('venue invoices receive a treasurer signature','A venue invoice lacks the treasurer signature','treasurer'),
 ('scholarship decisions record a conflict check','A scholarship decision records no conflict check','committee chair'),
 ('gallery loans have a return agreement','A gallery loan has no return agreement','curator'),
 ('public hearings provide a written agenda','A public hearing has no written agenda','hearing chair'),
 ('equipment loans record the borrower','An equipment loan records no borrower','depot manager'),
 ('membership expulsions provide an appeal route','A membership expulsion provides no appeal route','membership secretary')],
 'i':[
 ('nightly scans complete before dawn','A nightly scan completes after dawn',''),('message batches contain under forty records','A message batch contains fifty records',''),
 ('query plans use the indexed path','A query plan uses an unindexed path',''),('worker leases renew without interruption','A worker lease has an interruption',''),
 ('log partitions occupy under two gigabytes','A log partition occupies three gigabytes',''),('recovery messages reach the backup channel','A recovery message misses the backup channel',''),
 ('festival volunteers arrive before opening','A festival volunteer arrives after opening',''),('library talks attract at least twenty visitors','A library talk attracts ten visitors',''),
 ('tenants submit forms electronically','A tenant submits a paper form',''),('referee meetings finish in one session','A referee meeting needs a second session',''),
 ('community grants receive several applications','A community grant receives one application',''),('walking groups use the riverside route','A walking group uses the hill route','')]
 }
 items=[]
 for bi,(key,triples) in enumerate(blocks.items()):
  for n,(prop,exception,owner) in enumerate(triples):
   deliberate=(key=='r' and n in (1,5,9)) or (key=='i' and n in (2,6,10))
   prefix='Chosen deliberately. ' if deliberate else ''
   if key=='b':en=prop+'; the mechanism makes any exception require a change.';marker='by-construction'
   elif key=='r':en=f'A standing rule requires that {prop}; exceptions are possible and the {owner} must fix one.';marker='by-rule'
   else:en=f'In every observation so far, {prop}; nothing prevents an exception.';marker='in-practice'
   options=['A','B','C','D','E'];shift=(n+bi)%5;options=options[-shift:]+options[:-shift] if shift else options
   items.append({'id':f'fresh-{key}-{n+1:02}','english':prefix+en,
    'ainglish':prefix+prop[0].upper()+prop[1:]+' '+marker+'.',
    'question':exception+', system same. Then? A=false B=breach C=new D=valid E=?',
    'options':options,'answer':{'b':'A','r':'B','i':'C'}[key],
    'settlement_stratum':key,'strata':{'i':int(deliberate)}})
 for n in range(6):
  code='ABC'[n%3]
  items.append({'id':f'fresh-control-{n}','calibration':True,
   'english':f'Control slip {740+n}: the consequence is not stated.',
   'ainglish':f'Control slip {740+n}: the correct consequence code is {code}.',
   'question':'Which consequence code is correct?','options':['E','A','B','C','D'] if n<3 else ['B','C','D','E','A'],'answer':code})
 old={(x['english'],x['ainglish']) for x in m['manifest']['items']}
 assert not old&{(x['english'],x['ainglish']) for x in items} and len(items)==42
 spec={'public_id':PID,'slug':SLUG,'construct':p['form'],'metric':'comprehension_accuracy_delta',
  'seed':202609094311,'comparator':m['manifest']['comparator'],'panel':readers,
  'panel_neff':3,'planted_arm':'ainglish','calibration_min_gap':0.5,'items':items,'items_sha256':digest(items),
  'settlement_strata':m['manifest']['settlement_strata'],'replicates_hash':TARGET,
  'attempt':{'estimand':'Fresh-input replication of the source 36-case consequence-code diagnostic: same b/r/i strata, weights, source mappings, deliberate-prefix pattern, source reader identities and settings. Not a full claim-coverage or human study.',
   'admissibility_gates':['All source pairs are disjoint; exact reader weights/settings and source strata unchanged.',
    'Each exact source reader passes its frozen target-independent qualification and panel calibration; no substitution or retries.',
    'Source still eligible and meaning unchanged immediately before mint; preserve all null/adverse results.',
    'Serial exact cached readers, one study model resident; initial Windows free space at least 22 GiB and stop below 15 GiB.'],
   'planned_sample':{'real_items':36,'calibration_items':6,'readers':3,'target_calls':108,'calibration_calls':36}}}
 save(OUT/'items.json',items);save(OUT/'unbound-runspec.json',spec)
 save(OUT/'claim-lock.json',{k:p[k] for k in ('public_id','form','english_mapping','predicted_measurement','evidence_contract')})
 save(OUT/'design.json',{'fresh_real_pairs':36,'source':TARGET,
  'qualification_boundary':'New SDK screen receipt_precision input, existing receipt wire format. The plain source roster and actual answer-affecting settings hash are unchanged.',
  'limits':['Five terse consequence codes preserve the source instrument, not a new practical decision task.',
   'Related statement renderers are not 36 independent natural-world clusters.',
   'Three family names do not establish independent training data.',
   'The generic legacy settlement rule is allowed by the live source; no modern estimand identity is invented.']})
 print('PREPARED construction: 36 fresh pairs, three exact plain-roster configurations.',flush=True)
def qualify():
 fresh();require_resources([load(OUT/f'qualification-screen-{n}.json')['reader'] for n in range(3)])
 receipts=[];original=panel.chat
 for n in range(3):
  screen=load(OUT/f'qualification-screen-{n}.json');path=OUT/f'qualification-{n}.json'
  assert not path.exists(),'Never repeat a qualification until it passes'
  with (OUT/f'qualification-{n}.journal.jsonl').open('x') as journal:
   def ask_chat(ep,prompt):
    if shutil.disk_usage('/mnt/c').free<FLOOR:raise RuntimeError('Host free-space floor breached')
    journal.write(json.dumps({'event':'begin','prompt':prompt})+'\n');journal.flush()
    raw,truncated=original(ep,prompt)
    journal.write(json.dumps({'event':'end','raw':raw,'truncated':truncated})+'\n');journal.flush()
    return raw,truncated
   try:
    with patch.object(panel,'chat',side_effect=ask_chat):r=reader_qualification.run_screen(screen)
    save(path,r)
   finally:local('/api/generate',{'model':screen['reader']['model'],'keep_alive':0,'stream':False})
  all_yield=all(o['answer'] in screen['controls'][0]['options'] for o in r['observations'])
  save(OUT/f'qualification-{n}.yield.json',{'all_choices_yielded':all_yield})
  print('QUALIFICATION',n,r['status'],'yield',all_yield,flush=True)
  if r['status']!='passed' or not all_yield:return
  assert r['receipt']['settings_sha256']==digest(panel.reader_receipt(screen['reader']))
  receipts.append(r['receipt'])
 save(OUT/'qualifications.json',receipts)
def bind():
 c,p,m=fresh();spec=load(OUT/'unbound-runspec.json');spec['reader_qualifications']=load(OUT/'qualifications.json')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()
 spec['items_url']=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/construction/items.json'
 with urllib.request.urlopen(spec['items_url'],timeout=30) as f:assert json.load(f)==spec['items']
 mf=panel._planned_panel_manifest(spec)
 save(OUT/'preflight.json',c.preflight_attempt(SLUG,mf,**panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(spec)])))
 save(OUT/'runspec.json',spec);save(OUT/'planned-manifest.json',mf)
 print('BOUND construction with exact source strata and plain qualification receipts.',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
