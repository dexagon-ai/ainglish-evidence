"""Frozen entry-only learning, with role and paid-rental consequences kept visible."""
import copy,hashlib,json,subprocess,urllib.request,sys
from pathlib import Path
from ainglish import panel,study_scope
from local_colony_auth import ainglish_client
from reader_campaign import ROOT,OLD,save

PID='a-3zjcv2sz5g53nxxd'
SLUG='rent-borrow-rent-lend-active-bare-verbs-s-will-rent-borrow'
OUT=ROOT/'rent-learnability'
if len(sys.argv)>1 and sys.argv[1]=='bind':
 spec=json.loads((OUT/'unbound-runspec.json').read_text())
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()
 spec['items_url']=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/rent-learnability/items.json'
 with urllib.request.urlopen(spec['items_url'],timeout=30) as f:assert json.load(f)==spec['items']
 spec['entry']['source_url']=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/rent-learnability/entry.json'
 mf=panel._planned_panel_manifest(spec);c=ainglish_client()
 save(OUT/'preflight.json',c.preflight_attempt(SLUG,mf,**panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(spec)])))
 save(OUT/'runspec.json',spec);save(OUT/'planned-manifest.json',mf)
 print('BOUND rent learnability: immutable inputs referenced, preflight passed',flush=True)
 sys.exit(0)
c=ainglish_client();s=c.suggestions(proposal=PID);p=c.proposal(SLUG,authenticated=True)
assert any(x.get('evidence_work',{}).get('metric')=='learnability' for x in s['suggestions'])
assert p['public_id']==PID and p['stage'] in ('seconded','measured')
base=json.loads((OLD/'retention-replication/unbound-runspec.json').read_text())
readers=panel.prepare_reader_instruments({'panel':copy.deepcopy(base['panel'])})['panel']
names=['Adina','Bram','Celia','Dorian','Elva','Farid','Greta','Hugo']
partners=['Indra','Jalen','Kasia','Loren','Mina','Niko','Orla','Pavel']
domains=[('equipment',['thermal camera','mixing console','laser level','film scanner','signal generator','range finder','portable monitor','sound recorder']),
 ('vehicles',['cargo bicycle','electric scooter','estate car','flatbed truck','motorboat','motorcycle','touring caravan','shuttle bus']),
 ('rooms',['rehearsal room','training room','dance studio','banquet room','meeting room','gallery room','workshop room','practice room']),
 ('supplies',['folding tables','canopy panels','lighting stands','barrier rails','display boards','ceremony chairs','market stalls','serving trays'])]
items=[]
for di,(domain,assets) in enumerate(domains):
 for pole in ('borrow','lend'):
  for i in range(8):
   actor=names[(i+di)%8];partner=partners[(i+2*di)%8];asset=assets[i];named=i%2==0
   relation=(' from ' if pole=='borrow' else ' to ')+partner if named else ''
   directive=f'{actor} will rent-{pole} the {asset}{relation}.'
   record=hashlib.sha256(f'{di}:{pole}:{i}'.encode()).hexdigest()[:8]
   # Each block has 6 direction consequences (3 yes/3 no) and two fee
   # consequences (one yes/one no). Neither marker is a constant answer key.
   if i<6:
    rule=('borrow','borrow','lend','lend','lend','borrow')[i]
    target='obtains temporary use of the asset' if rule=='borrow' else 'makes the asset available for temporary use'
    context=(f'Fictional booking RL-{record}. One arrangement concerns the {asset}. '
     f'The desk switches on an amber indicator for the party that {target}, and leaves the other party\'s indicator off. ')
    question=f'Should the desk switch on {actor}\'s amber indicator for this booking?'
    answer='Yes' if pole==rule else 'No';family='role-consequence'
   else:
    fee=(i==6)==(pole=='borrow')
    context=(f'Fictional booking RL-{record}. One arrangement concerns the {asset}. '
     'The desk switches on a jade indicator for arrangements '+
     ('in which temporary use is acquired for a fee' if fee else 'in which temporary use is provided free of charge')+
     ', and leaves it off for the other kind. ')
    question='Should this booking have the jade indicator switched on?'
    answer='Yes' if fee else 'No';family='fee-consequence'
   text=context+directive
   items.append({'id':f'rl-{di}-{pole}-{i}','english':text,'ainglish':text,
    'question':question,'options':['Yes','No'] if i%2==0 else ['No','Yes'],'answer':answer,
    'strata':{'form':'rent-'+pole,'domain':domain,'counterparty':'named' if named else 'unnamed','question_family':family}})
assert len(items)==64 and len({(i['english'],i['question']) for i in items})==64
for pole in ('borrow','lend'):
 block=[i for i in items if i['strata']['form']=='rent-'+pole]
 assert sum(i['answer']=='Yes' for i in block)==16
 for domain,_ in domains:
  for counterparty in ('named','unnamed'):
   cell=[i for i in block if i['strata']['domain']==domain and i['strata']['counterparty']==counterparty]
   assert len(cell)==4 and sum(i['answer']=='Yes' for i in cell)==2
controls=[]
destinations=['Rill','Sable','Tern','Umber','Vireo','Wick','Yarrow','Zinc']
for i,dest in enumerate(destinations):
 controls.append({'id':f'rl-cal-{i}','calibration':True,'calibration_scope':'target-independent',
  'calibration_construct':'novel-parcel-routing-dictionary',
  'english':f'Parcel QT-{i} carries routing symbol jex{i}; its destination could be any of Rill, Sable, Tern, Umber, Vireo, Wick, Yarrow or Zinc. A dictionary is unavailable.',
  'ainglish':f'Routing dictionary: jex{i} means destination {dest}. Parcel QT-{i} carries symbol jex{i}.',
  'question':f'Which destination receives parcel QT-{i}?','options':destinations,'answer':dest})
entry_text='Registered form: '+p['form']+'\n\n'+p['english_mapping']
save(OUT/'entry.json',{'text':entry_text,'source_field':'form and english_mapping from the freshly read proposal','public_id':PID,'slug':SLUG})
entry_sha=hashlib.sha256(entry_text.encode()).hexdigest()
entry={'text':entry_text,'sha256':entry_sha,'source_url':'https://ainglish.org/api/v1/proposals/'+SLUG,'proposal_revision':SLUG}
all_items=items+controls
spec={'public_id':PID,'slug':SLUG,'form':p['form'],'construct':p['form'],'metric':'learnability','seed':202609091901,
 'panel':readers,'panel_neff':2,'reader_qualifications':base['reader_qualifications'],
 'planted_arm':'ainglish','calibration_min_gap':0.5,'entry':entry,
 'items':all_items,'items_sha256':hashlib.sha256(json.dumps(all_items,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),
 'attempt':{'estimand':'Register-entry-arm application accuracy on 64 fresh rent-role/fee consequence messages, four domains and both poles; report every pole, reader and question family separately. Cold accuracy is descriptive, not a no-entry success gate.',
  'admissibility_gates':['Current proposal meaning and learnability requirement unchanged before mint.',
   'All target-independent qualifications valid; each reader completes unrelated dictionary calibration before target questions.',
   'No target outcome conditions admission: preserve low learnability and all first answers.',
   'Serial exact cached readers, one study model resident, host free space at least 15 GiB; abort on transport failure, truncation or resource breach.'],
  'planned_sample':{'real_items':64,'calibration_items':8,'readers':2,'target_calls':256,'calibration_calls':32}}}
spec=study_scope.attach(spec,purpose='claim_test',scope='Entry-only learnability prerequisite, 64 fresh complete real items. The full registered mapping is supplied, not an independently tested short website card. Does not establish CAD, literal token price, humans or adoption.')
save(OUT/'claim-lock.json',{k:p[k] for k in ('public_id','form','english_mapping','predicted_measurement','evidence_contract')})
save(OUT/'items.json',all_items);save(OUT/'unbound-runspec.json',spec)
save(OUT/'design.json',{'core_items':64,'role_consequence_items':48,'fee_consequence_items':16,
 'entry_words':len(entry_text.split()),'entry_scope':'Full live form+mapping; no per-item coaching or extra examples.',
 'predictions':{'each_form_entry_accuracy_at_least':'0.90','required_disaggregation':['form','reader','domain','counterparty','question_family']},
 'limits':['Two base families are not a claim of independent training data.','Related scenario renderers limit population generalisation and item-bootstrap precision.','Cold and entry calls share a model configuration but are stateless; cold precedes entry for each item.','This study does not establish a comprehension advantage over concise English or price the future 96-cell CAD set.'],
 'spend':'No target calls before this freeze; the already completed exact-reader qualification is target-independent.'})
print('PREPARED rent learnability',len(items),'items; entry words',len(entry_text.split()),flush=True)
