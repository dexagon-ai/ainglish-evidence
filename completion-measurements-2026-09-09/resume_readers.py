"""Freeze canonical-template comprehension and a separate, conditional learning packet."""
import copy,hashlib,json,subprocess,sys,urllib.request
from ainglish import panel,study_scope
from local_colony_auth import ainglish_client
from reader_campaign import ROOT,OLD,save,load

PID='a-jvjxmmf83rmvw9vx';SLUG='action-resume-from-checkpoint-action-redo-from-start-retain'
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def build_core(prefix,learning=False):
 rows=[]
 domains=[('reading','Read guide','sections',['amber','coral','ivory','teal']),
  ('review','Complete checklist','items',['birch','cedar','maple','pine']),
  ('media','Play tutorial','clips',['harbour','island','lagoon','marina']),
  ('simulated-workflow','Execute simulated workflow','steps',['bronze','copper','silver','zinc'])]
 cases=[(2,0,True),(2,0,False),(1,2,True),(1,2,False),(0,0,True),(0,0,False),(3,1,True),(3,1,False)]
 for di,(domain,verb,unit,labels) in enumerate(domains):
  if learning:labels=labels[1:]+labels[:1]
  for pole in ('resume','redo'):
   for i,(progress,target,performed_rule) in enumerate(cases):
    ref=f'{prefix}-{di}-{pole}-{i}';checkpoint='CP-'+hashlib.sha256(ref.encode()).hexdigest()[:6]
    action=f'{verb} {ref}';done=', '.join(labels[:progress]) or 'none'
    actor=['Ari','Bela','Cato','Dina'][i%4]
    common=(f'Task {ref}, version 1, consists of the four {unit} {", ".join(labels)}, in that order. '
     f'{actor} previously completed: {done}. Saved record {checkpoint} belongs to this exact task/version and records those completed {unit}; its next unfinished unit is {labels[progress]}. '
     f'An indicator switches on if and only if {labels[target]} is '+('performed' if performed_rule else 'left unperformed')+' during the forthcoming pass. '
     'The task is authorised and purely simulated; no external effects or retry restriction apply. ')
    en=action+(f', continuing from checkpoint {checkpoint}.' if pole=='resume' else ' again from the beginning.')
    ai=action+(f', resume-from({checkpoint}).' if pole=='resume' else ', redo-from-start.')
    performs=(target>=progress) if pole=='resume' else True
    text=common+ai
    rows.append({'id':ref,'english':text if learning else common+en,'ainglish':text,
     'question':'Should the indicator switch on for the forthcoming pass?',
     'options':['Yes','No'] if i%2==0 else ['No','Yes'],'answer':'Yes' if performs==performed_rule else 'No',
     'settlement_stratum':pole+'-core','strata':{'form':pole,'domain':domain,'progress':progress,
       'earlier_worker':actor,'indicator_rule':'performed' if performed_rule else 'unperformed'}})
 assert len(rows)==64
 for pole in ('resume','redo'):
  for domain,*_ in domains:
   group=[r for r in rows if r['strata']['form']==pole and r['strata']['domain']==domain]
   assert len(group)==8 and sum(r['answer']=='Yes' for r in group)==4
 return rows
def prepare():
 c=ainglish_client();s=c.suggestions(proposal=PID);p=c.proposal(SLUG,authenticated=True)
 assert any(x.get('evidence_work',{}).get('metric')=='comprehension_accuracy_delta' and not x.get('replicates_hash') for x in s['suggestions'])
 base=load(OLD/'retention-replication/unbound-runspec.json');readers=panel.prepare_reader_instruments({'panel':copy.deepcopy(base['panel'])})['panel']
 # Fixed unrelated receipt-holder calibration bank, frozen and used in the
 # earlier verifier study. Its reuse is explicit; it is never target evidence.
 controls=[copy.deepcopy(x) for x in load(OLD/'verifier-entropy/bare/items.json') if x.get('calibration')]
 core=build_core('RC');boundary=[]
 cases=[('resume','No saved record is available for the named checkpoint.',True),
  ('resume','The saved record names a different task; it is not a record of this task.',True),
  ('resume','The saved record is for version 1, but the current task is version 2 and no mapping exists.',True),
  ('redo','This pass would resend a real external message, and the standing instruction explicitly prohibits sending it again.',True),
  ('resume','The checkpoint is valid for this exact version, credits the first unit and names the next unfinished unit. All authority is present.',False),
  ('resume','The checkpoint is valid for this exact version and explicitly records zero completed units. All authority is present.',False),
  ('redo','The defined task has a clear first unit; every required unit can be performed afresh. All authority is present.',False),
  ('redo','An ordinary cache speeds access but does not replace performing any required task unit afresh. All authority is present.',False)]
 for copy_index in range(2):
  for i,(pole,condition,stop) in enumerate(cases):
   ref=f'RB-{copy_index}-{i}';checkpoint='K'+str(copy_index)+str(i);action='Complete inspection '+ref
   common=(f'Inspection {ref} has one defined start and a fixed sequence of units. '+condition+
    (' This task is otherwise safe and authorised.' if not (pole=='redo' and stop) else '')+' ')
   en=action+(f', continuing from checkpoint {checkpoint}.' if pole=='resume' else ' again from the beginning.')
   ai=action+(f', resume-from({checkpoint}).' if pole=='resume' else ', redo-from-start.')
   boundary.append({'id':ref,'english':common+en,'ainglish':common+ai,
    'question':'Must the executor resolve missing information or obtain different authority before proceeding?',
    'options':['Yes','No'],'answer':'Yes' if stop else 'No','settlement_stratum':'boundary',
    'strata':{'form':pole,'domain':'boundary','boundary_case':i}})
 for kind,items,metric in [('resume-comprehension',core+boundary,'comprehension_accuracy_delta'),
                           ('resume-learning-held',build_core('RL',learning=True),'learnability')]:
  out=ROOT/kind;all_items=items+controls
  spec={'public_id':PID,'slug':SLUG,'form':p['form'],'construct':p['form'],'metric':metric,
   'seed':202609094523,'panel':readers,'panel_neff':2,'reader_qualifications':base['reader_qualifications'],
   'planted_arm':'ainglish','calibration_min_gap':0.5,'items':all_items,'items_sha256':digest(all_items),
   'attempt':{'estimand':('Ainglish minus canonical concise-English accuracy on 64 balanced core progress consequences and 16 separately reported boundary items.' if metric!='learnability' else 'Entry-only application accuracy on 64 separate balanced progress-consequence messages; each form/domain separately reported. Boundary learning requires a separate planned block, not an inferred pass.'),
    'admissibility_gates':['Fresh live meaning, prediction and exact metric work unchanged; cost-source confirmation does not establish learning or comprehension.',
     'Only the explicitly capped 4096-context cached source configurations; qualify and calibrate before targets. No downloads, reader substitution or retries.',
     'Preregister before every target call; retain null/adverse outcomes and each named pole.',
     'Windows host starts above 22 GiB free and stops below 15 GiB; one explicitly owned study model resident.'],
    'planned_sample':{'real_items':len(items),'calibration_items':len(controls),'readers':2,
     'target_calls':len(items)*(4 if metric=='learnability' else 2),'calibration_calls':len(controls)*4}}}
  if metric=='comprehension_accuracy_delta':
   spec['comparator']={'kind':'complete-canonical-concise-english-v1','description':'ACTION and checkpoint identifier unchanged under the two literal registered templates; all task/progress/indicator facts shared.'}
   spec['settlement_strata']=[{'id':'resume-core','weight':2},{'id':'redo-core','weight':2},{'id':'boundary','weight':1}]
  else:
   text='Registered form: '+p['form']+'\n\n'+p['english_mapping']
   spec['entry']={'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),
    'source_url':'https://ainglish.org/api/v1/proposals/'+SLUG,'proposal_revision':SLUG}
  spec=study_scope.attach(spec,purpose='claim_test',scope=('Supporting comprehension prerequisite; no inference of learnability. Three named settlement strata prevent boundary controls from hiding a failed core pole.' if metric!='learnability' else 'Conditional unrun core learning packet, held until the prerequisite route permits it; this alone cannot establish the separately promised boundary-block learning target.'))
  save(out/'unbound-runspec.json',spec);save(out/'items.json',all_items)
  save(out/'claim-lock.json',{k:p[k] for k in ('public_id','form','english_mapping','predicted_measurement','evidence_contract')})
  save(out/'design.json',{'real_items':len(items),'scope':metric,'reused_calibration_bank':'Eight target-independent receipt-holder controls from the frozen verifier design; not new scientific evidence.',
   'limits':['Four domain renderers and paired indicator questions do not make every surface row an independent natural-world case.',
    'Boundary repeats alter identifiers only: eight distinct boundary conditions, not sixteen independent conditions.',
    'Fixed present-day readers, not humans, new tokenizer training or future model-weight learning.'],
   'reader_policy':'Use only the already tested ctx4k custom models; the unsafe plain 131072-context Mistral source is not part of this study.'})
 print('Prepared 80 canonical CAD items and separate held 64-item learning packet.',flush=True)
def bind():
 out=ROOT/'resume-comprehension';spec=load(out/'unbound-runspec.json')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()
 spec['items_url']=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/resume-comprehension/items.json'
 with urllib.request.urlopen(spec['items_url'],timeout=30) as f:assert json.load(f)==spec['items']
 mf=panel._planned_panel_manifest(spec);c=ainglish_client()
 save(out/'preflight.json',c.preflight_attempt(SLUG,mf,**panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(spec)])))
 save(out/'runspec.json',spec);save(out/'planned-manifest.json',mf)
 print('BOUND canonical resume CAD, without reader spend.',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
