"""Phase 2: apply the previously declared form assignment to committed neutral bytes."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import subprocess

from ainglish import panel, reader_qualification
from instrument import ROOT, FORMS, PANEL_SEED, ASSIGNMENT_SEED, assign, canonical, digest, project, opportunities, write

NEUTRAL_COMMIT='52a47c2f2afbb930d4cba23a0d9dd88d52744199'
NEUTRAL_RAW_SHA='171b99ef688bee8f8d642f81aab4f14095d52e6826e9dd7bf943819a6fd1abda'
NEUTRAL_REL='choose-any-completion-2026-09-14/fresh-bank-v2/neutral-worlds.json'

def controls():
    result=[]
    for i in range(32):
        person,other=f'Clerk-Aster-{i+61}',f'Clerk-Zinnia-{i+61}'
        store,alternative=f'Archive-Birch-{i+81}',f'Archive-Elm-{i+81}'
        options=[f'{person} / {store}',f'{person} / {alternative}',f'{other} / {store}',
                 f'{other} / {alternative}','Clerk not established; archive established.',
                 'Clerk established; archive not established.','Neither clerk nor archive established.',
                 'The record contradicts itself.']
        answer=options[0]
        offset=i%8
        options=options[offset:]+options[:offset]
        result.append({'id':f'ca2-calibration-{i+1:02d}','calibration':True,
             'english':f'File-record-{i+501}: either {person} or {other} is the responsible clerk; '
                       f'this has not been settled. Either {store} or {alternative} is the destination archive; this also has not been settled.',
             'ainglish':f'File-record-{i+501}: {person}, not {other}, is the responsible clerk. '
                        f'{store}, not {alternative}, is the destination archive.',
             'question':'Which complete clerk/archive assignment is established by this record?',
             'options':options,'answer':answer})
    return result

def build():
    raw=(ROOT/'neutral-worlds.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==NEUTRAL_RAW_SHA
    committed=subprocess.check_output(['git','show',NEUTRAL_COMMIT+':'+NEUTRAL_REL],cwd=ROOT)
    assert committed==raw
    neutral=json.loads(raw)
    worlds=neutral['worlds']
    assert digest(worlds)==neutral['worlds_sha256']
    assert neutral['assignment_seed_planned']==ASSIGNMENT_SEED
    mapping=assign(worlds)
    items=[project(w,mapping[w['id']]) for w in worlds]
    counterfactuals=[project(w,f,audit=True) for w in worlds for f in FORMS]
    calibration=controls()
    write('items.json',items+calibration)
    write('audit-only-counterfactuals.json',{
        'status':'AUDIT_ONLY_DO_NOT_RUN_AS_ADDITIONAL_TARGET_WORLDS',
        'items_sha256':digest(counterfactuals),'items':counterfactuals})
    write('assignment.json',{'neutral_commit':NEUTRAL_COMMIT,'neutral_file_sha256':NEUTRAL_RAW_SHA,
        'neutral_worlds_sha256':digest(worlds),'assignment_seed':ASSIGNMENT_SEED,
        'policy':'single preregistered random assignment; no reroll or seed selection',
        'mapping':mapping,'target_items_sha256':digest(items),
        'panel_items_including_calibration_sha256':digest(items+calibration),
        'counts':dict(Counter(i['settlement_stratum'] for i in items))})
    readers=[]; qualifications=[]
    for tag in ['gemma','mistral']:
        readers.append(json.loads((ROOT.parent/'qualification'/f'{tag}-screen.json').read_text())['reader'])
        qualifications.append(json.loads((ROOT.parent/'qualification'/f'{tag}-result.json').read_text())['receipt'])
    # Draft transport configuration, deliberately NOT a submit-ready runspec or attempt.
    spec={'status':'REVIEW_REQUIRED_NOT_LAUNCH_APPROVAL','construct':'a-ppyzdf5qk6z67aty',
          'metric':'comprehension_accuracy_delta','seed':PANEL_SEED,'panel':readers,
          'models':[r['name']+'@'+r['precision'] for r in readers], 'panel_neff':1,
          'settlement_strata':[{'id':f,'weight':1} for f in FORMS],
          'items_sha256':digest(items+calibration),'calibration_min_gap':.5}
    spec=reader_qualification.attach(spec,qualifications)
    write('reader-config-review.json',spec)
    cells=[]
    for reader in readers:
        for item in items:
            cells.append({'world_id':item['world_id'],'reader':reader['name'],
                'arm':panel.arm_for(PANEL_SEED,reader['name'],item['id']),
                'form':item['settlement_stratum'],'domain':item['domain'],
                'frame_family':item['frame_family'],'offered_contrasts':opportunities(item)})
    write('planned-cells.json',{'status':'ASSIGNMENT_ONLY_NO_INFERENCE','cells':cells})
    print(json.dumps({'target_worlds':len(items),'calibration_items':len(calibration),
       'planned_target_cells':len(cells),'planned_calibration_cells':len(calibration)*len(readers)*2,
       'actual_target_calls':0,'items_sha256':digest(items+calibration)}))

if __name__=='__main__': build()
