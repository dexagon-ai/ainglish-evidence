"""Prospective control-only redesign after seven zero-target calibration aborts.

The original controls always named the planted holder first, even in the
under-specified arm. That is a guessable cue, not evidence about a language item.
Remove that cue, balance holder/order independently, retain the full old record.
"""
import copy, hashlib, json, random, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'control-repair'
SEED=2026090591
ORDER=['mean.careful','mean.practical','mean.consequences','quantity.cold','quantity.reference','choice.cold','choice.reference']
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def save(name,value):
 with (OUT/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def build():
 OUT.mkdir(exist_ok=True);(OUT/'frozen').mkdir(exist_ok=True)
 outcomes=json.loads((ROOT/'reader-campaign-finished.json').read_text())['outcomes']
 assert all(x['state']=='aborted' and x['calls']==32 for x in outcomes) and len(outcomes)==7
 for name in ORDER:
  old=json.loads((ROOT/'frozen'/f'{name}.items.json').read_text())
  rows=[x for x in old if not x.get('calibration')]
  for i in range(16):
   candidates=[f'holder-{name}-{i}-{letter}' for letter in 'KLMN']
   # Explicitly orthogonal to candidate presentation and output-label positions.
   holder=candidates[i%4];labels=list('ABCD')
   shown=candidates[:];random.Random(SEED+i).shuffle(shown)
   options=candidates[:];options.remove(holder);random.Random(SEED+97+i).shuffle(options)
   options.insert((i//4)%4,holder)
   common=f'Locker CR-{name}-{i} has exactly one holder from '+', '.join(shown)+'. '
   rows.append({'id':f'cr-{name}-{i}','calibration':True,
    'english':common+'The record omits which candidate is the holder.',
    'ainglish':common+f'The record identifies {holder} as the holder.',
    'question':f'Which candidate is the holder of locker CR-{name}-{i}? Choose one option letter. '+
       ' '.join(f'{label} = {value}.' for label,value in zip(labels,options)),
    'options':labels,'answer':labels[options.index(holder)],
    'strata':{'semantic_gold':holder,'answer_options':dict(zip(labels,options)),
     'design':'four-way uninformed forced guess versus explicit identification; no Ainglish target'}})
  save('frozen/'+name+'.items.json',rows)
 save('design.json',{'reason':'Earlier planted holder was always first named in both arms, a guessable positional cue. This is a control-design repair, not a target result.',
  'prior_attempts':[json.loads((ROOT/(name+'.opened.json')).read_text())['attempt']['attempt_id'] for name in ORDER],
  'prior_target_cells':0,'unchanged':'All real items, questions, gold, reader identities/settings, strata, analysis and gap floor.',
  'change':'16 four-candidate forced-guess controls; planted candidate independently balanced across output positions. No unknown answer is falsely scored against the planted holder.',
  'stop_rule':'If any repaired study aborts, stop the remaining campaign. No further instrument redesign in this batch.',
  'inference':'The absent-information arm deliberately requires a guess; this is not a normal comprehension task.',
  'seed':SEED})
 validate()
def validate():
 for name in ORDER:
  old=json.loads((ROOT/'frozen'/f'{name}.items.json').read_text());rows=json.loads((OUT/'frozen'/f'{name}.items.json').read_text())
  assert [x for x in old if not x.get('calibration')]==[x for x in rows if not x.get('calibration')]
  controls=[x for x in rows if x.get('calibration')];assert len(controls)==16
  assert all(sum(x['answer']==l for x in controls)==4 for l in 'ABCD')
  for x in controls:
   assert x['strata']['answer_options'][x['answer']]==x['strata']['semantic_gold']
   assert 'identifies '+x['strata']['semantic_gold']+' as the holder' in x['ainglish']
   assert 'omits which candidate' in x['english']
 return True
def prepare(commit):
 validate()
 for name in ORDER:
  spec=json.loads((ROOT/(name+'.runspec.json')).read_text())
  rows=json.loads((OUT/'frozen'/f'{name}.items.json').read_text())
  spec['items_url']=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/control-repair/frozen/{name}.items.json'
  spec['items_sha256']=hashlib.sha256(canonical(rows)).hexdigest()
  spec['attempt']['planned_sample'].update(calibration_items=16,calibration_calls=64,source_commit=commit,
    control_repair='postdeploy-four-way-control-v2',predecessor_attempt_id=json.loads((ROOT/(name+'.opened.json')).read_text())['attempt']['attempt_id'])
  spec['attempt']['admissibility_gates']=[x.replace('eight target-independent planted controls','sixteen target-independent four-way controls') for x in spec['attempt']['admissibility_gates']]
  spec['attempt']['admissibility_gates'].append('Any abort stops the rest of this repaired campaign; no further redesign in this batch.')
  save(name+'.runspec.json',spec)
def run():
 import run_readers_once as runner
 import prepare_readers
 prepare_readers.ROOT=OUT
 runner.ROOT=OUT;runner.validate=validate
 runner.STOP_ON_ABORT=True
 runner.main()
if __name__=='__main__':
 {'build':build,'prepare':lambda:prepare(sys.argv[2]),'run':run}[sys.argv[1]]()
