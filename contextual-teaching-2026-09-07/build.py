"""Authored train-only supplement; no model calls, downloaded data or heldout reuse."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent
CONTEXTS = [
 ('perfumery','blend record','scent wheel'), ('tapestry','weaving plan','thread chart'),
 ('orchard','graft record','fruit sketch'), ('ceramics','glaze record','kiln diagram'),
 ('marquetry','veneer list','inlay drawing'), ('beekeeping','hive record','pollen chart'),
 ('bookbinding','binding note','sewing diagram'), ('watchmaking','service note','gear drawing'),
 ('falconry','training log','flight chart'), ('glasswork','batch note','colour chart'),
 ('coppicing','cutting plan','stool map'), ('luthiery','repair note','bridge sketch'),
]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, obj):
 with p.open('x', encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')

def render(family, context, variant):
 domain, document, diagram = context
 task = f'the {domain} {document}'
 if family == 'participants':
  opening = [f'A coordinator speaks directly to you about {task}. ',
   f'An organiser tells you who will prepare {task}. ', f'You receive this announcement for {task}. ',
   f'An assistant addresses you before the {domain} workshop. '][variant//2]
  include = variant % 2 == 0
  ending = [f' will inspect {task}.', f' will prepare {diagram}.',
   f' will attend the {domain} workshop.', f' will approve {task}.'][variant//2]
  return (opening+'we-'+('including' if include else 'excluding')+'-you'+ending,
   opening+'We, '+('including' if include else 'excluding')+' you,'+ending,
   'Does the named group include the person being addressed?', 'Yes' if include else 'No',
   'This states membership in the named group, not access rights or permission to delegate.')
 if family == 'unknown':
  choice = variant % 2 == 1
  issues = [f'the approved colour for {task}', f'the assigned reviewer of {task}',
            f'the chosen room for the {domain} workshop', f'the selected format for {task}']
  issue = issues[variant//2]
  prefix = f'The {domain} coordinator reports the status of one issue: '
  a = ('choice-not-made' if choice else 'fact-not-known')+' — '+issue+'.'
  e = ('No operative decision has yet been made about '+issue+'.' if choice else
       'There is a determined answer about '+issue+', but I lack evidence of that answer.')
  return prefix+a,prefix+e,'What would close this particular gap?',('An authorized choice' if choice else 'Evidence of the determined answer'),'A status report neither grants authority to choose nor supplies the missing answer.'
 if family == 'deadline':
  finish = variant % 2 == 1
  time = ['11:30Z','13:15Z','15:45Z','17:20Z'][variant//2]
  action = ['prepare','inspect','copy','deliver'][variant//2]+' '+task
  prefix = f'The instruction refers to 2026-10-14 in UTC: '
  a = action.capitalize()+(' complete-by(' if finish else ' start-by(')+time+').'
  e = ('Successfully finish' if finish else 'Begin actual execution of')+' the action “'+action+'” no later than '+time+'.'
  return prefix+a,prefix+e,'Which event is required by the deadline?',('Successful completion' if finish else 'Actual execution starting'),'Acknowledgement, scheduling, failure and cancellation are not successful completion.'
 if family == 'alternatives':
  inclusive = variant % 2 == 0
  first,second = [(document,diagram), ('a paper copy','a digital copy'),
                 ('a written note','an audio note'), ('a table','a drawing')][variant//2]
  prefix = f'For the {domain} handover, provide '
  a = prefix+first+' or '+second+', '+('or-both' if inclusive else 'not-both')+'.'
  e = prefix+(first+', '+second+', or both; at least one is required.' if inclusive else
               'exactly one of '+first+' and '+second+', not both.')
  return a,e,'Would providing both named alternatives satisfy this choice requirement?',('Yes' if inclusive else 'No'),'Neither form permits providing neither; separate constraints still apply.'
 if family == 'multiplicity':
  collective = variant % 2 == 1
  n = [3,4,5,6][variant//2]
  action = ['inspect','copy','check','sign'][variant//2]+' '+task
  a = f'The {n} named participants '+action+', '+('as-one' if collective else 'each-alone')+'.'
  e = (f'The {n} named participants jointly perform one act to '+action+'.' if collective else
       f'Each of the {n} named participants independently performs one act to '+action+'.')
  return a,e,'How many acts of the named kind does this sentence require?',str(1 if collective else n),'This counts whole action instances, not substeps, simultaneity or result agreement.'
 if family == 'update':
  addition = variant % 2 == 1
  old = ['copy','inspect','sign','deliver'][variant//2]+' '+task
  new = ['number','photograph','date','summarise'][variant//2]+' '+task
  prefix = f'The unique active clause A requires you to {old}; none of it has been completed. The sender is authorized to update it. A separate clause B stays untouched. New clause C: '
  a = prefix+('supplements' if addition else 'supersedes')+'(A): '+new+'.'
  e = prefix+(f'keep A active and add, without precedence over A: {new}.' if addition else
     f'retire the whole uncompleted clause A and replace it with: {new}.')
  return a,e,'Does A remain active after this valid committed update?',('Yes' if addition else 'No'),'B is unchanged; retiring an obligation does not undo an external action already completed.'
 raise ValueError(family)

def main():
 source = json.loads((ROOT/'source-constructs.json').read_text())
 assert all(e['status']=='current' and e['ratified_at'] for e in source['entries'].values()), 'Current ratified release entries only'
 data = []
 for family in sorted(source['entries']):
  for vi in range(8):
   for ci, context in enumerate(CONTEXTS):
    a,e,q,g,note = render(family,context,vi)
    data.append(dict(id=f'{family}/{vi}/{context[0]}',family=family,frame=f'{family}/{vi}',
     context=context[0],ainglish=a,english=e,question=q,answer=g,scope_note=note,
     source_slug=source['entries'][family]['slug'],source_content_digest=source['entries'][family]['content_digest']))
 assert len(data)==576 and len({(r['ainglish'],r['english'],r['question']) for r in data})==576
 # Holdouts are used only as forbidden strings, never to create training rows or keys.
 forbidden = set()
 holdout_digests = {}
 for rel in ['learning-transfer-2026-09-06/novel-reasoning.jsonl',
             'learning-transfer-2026-09-06/tasks.jsonl',
             'mistral-context-transfer-2026-09-07/cases.json']:
  p = ROOT.parent/rel
  if not p.is_file(): continue
  holdout_digests[rel] = sha(p)
  records = json.loads(p.read_text()) if p.suffix=='.json' else [json.loads(x) for x in p.read_text().splitlines()]
  def collect(v):
   if isinstance(v,dict):
    for k,x in v.items():
     if k in ('ainglish','english','content') and isinstance(x,str): forbidden.add(x)
     else: collect(x)
   elif isinstance(v,list):
    for x in v: collect(x)
  collect(records)
 assert not {r[k] for r in data for k in ('ainglish','english')} & forbidden
 taught = {'we-including-you','we-excluding-you','fact-not-known','choice-not-made','start-by','complete-by',
           'or-both','not-both','as-one','each-alone','supersedes','supplements'}
 snapshot = json.loads((ROOT.parent/'progression-lab-2026-09-06/snapshot/proposals.json').read_text())
 marker = re.compile(r'\b[a-z][a-z0-9_]*(?:-[a-z0-9_]+)+\b|\b[a-z][a-z0-9_]*(?=\(|:)')
 registered = {m for p in snapshot for m in marker.findall(p['form'])}
 text = '\n'.join(r[k] for r in data for k in ('ainglish','english','question','answer','scope_note'))
 extras = set(marker.findall(text)) & (registered-taught)
 assert not extras, extras
 files = {}
 files['curriculum.jsonl'] = ''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in data).encode()
 for lang in ['ainglish','english']:
  files['train-'+lang+'.jsonl'] = ''.join(json.dumps({'id':r['id'],'messages':[
   {'role':'system','content':'Read the supplied statement. Answer the question without adding unstated authority, evidence or scope.'},
   {'role':'user','content':r[lang]+'\n\n'+r['question']},
   {'role':'assistant','content':r['answer']+'\n'+r['scope_note']} ]},ensure_ascii=False)+'\n' for r in data).encode()
 files['source-constructs.json'] = (ROOT/'source-constructs.json').read_bytes()
 audit = {'kind':'ainglish.contextual-teaching-audit.v1','pairs':576,'authored_frames':48,
  'contexts':12,'families':dict(Counter(r['family'] for r in data)),'official_release':False,
  'source_sha256':sha(ROOT/'source-constructs.json'),'literal_other_registered_markers':sorted(extras),
  'heldout_exact_arm_overlap':0,'checked_holdouts':holdout_digests,
  'boundary':'Synthetic single-author teaching examples, not human-reviewed proof or 576 independent structures. 48 authored frames include related binary variants; semantic/template overlap with other studies remains possible. Full definitions are metadata, never appended automatically. No evaluation, model outputs or empirical results are exported.'}
 files['AUDIT.json'] = (json.dumps(audit,ensure_ascii=False,indent=2)+'\n').encode()
 files['README.txt'] = (ROOT/'README.md').read_bytes()
 manifest = {'kind':'ainglish.non-normative-teaching-supplement.v1','official_release':False,'license':'CC0-1.0',
  'split':'train','synthetic':True,'paired_cases':576,'files':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in files.items()}}
 files['MANIFEST.json'] = (json.dumps(manifest,indent=2)+'\n').encode()
 for name,raw in files.items():
  if name=='source-constructs.json': continue
  with (ROOT/name).open('xb') as f:f.write(raw)
 with zipfile.ZipFile(ROOT/'teaching-supplement-576.zip','x') as z:
  for name,raw in sorted(files.items()):
   info=zipfile.ZipInfo(name,(2026,9,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,raw)
 save(ROOT/'FROZEN.json',{p.name:sha(p) for p in ROOT.iterdir() if p.is_file()})
 print(json.dumps(audit))
if __name__=='__main__':main()
