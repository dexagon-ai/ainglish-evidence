"""Continue only the third reader, which stopped at the PRE-LOAD RAM guard.

The first two screen failures are immutable and are not repeated. The published
plan, controls, prompts, scoring and sampler settings remain byte-identical.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import time
import study
from study import ROOT, api, ram, Journal, disk_guard, save_new, verify_freeze, decode_json, reader_messages

def main(commit):
    original=verify_freeze(ROOT)
    assert original.startswith('164fb2f')
    rel=Path(__file__).relative_to(ROOT.parent).as_posix()
    assert subprocess.check_output(['git','show',commit+':'+rel],cwd=ROOT.parent)==Path(__file__).read_bytes()
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
    assert not (ROOT/'execution/reader-2.jsonl').exists(), 'Third reader already exposed; reconcile without retries'
    prior=[json.loads((ROOT/f'execution/result-{i}.json').read_text()) for i in [0,1]]
    assert all(not r['qualified'] and not r['targets'] for r in prior)
    for i in [0,1]:
        events=Journal._validate((ROOT/f'execution/reader-{i}.jsonl').read_text())
        assert sum(e['kind']=='begin' for e in events)==sum(e['kind']=='end' for e in events)==16
    plan=json.loads((ROOT/'PLAN.json').read_text());controls=json.loads((ROOT/'controls.json').read_text())
    model,digest=plan['models'][2]
    tags={m['name']:m for m in api('tags')['models']}
    assert tags[model]['digest']==digest
    if api('ps')['models']:raise RuntimeError('Shared service occupied')
    disk_guard();available=ram()
    if available<tags[model]['size']*1.1+4*1024**3:raise RuntimeError('Pre-load memory reserve still unavailable; no call started')
    save_new(ROOT/'execution/resume-reader-2.json',{'original_freeze':original,'continuation_commit':commit,'available_ram':available,
        'reason':'Transient memory was still occupied immediately after unloading the preceding model. It has now been returned. Reader2 never began; no scientific gate or prior result is changed.'})
    cases=[c for c in json.loads((ROOT.parent/'communication-diagnostics-2026-09-06/cases.json').read_text()) if c['dimensions'] in plan['target_dimensions']]
    with Journal(ROOT/'execution/reader-2.jsonl',dict(plan,selected_model=model)) as journal:
        def call(key,messages):
            disk_guard()
            if ram()<3*1024**3:raise RuntimeError('Host RAM reserve reached')
            if any(m['name']!=model for m in api('ps')['models']):raise RuntimeError('Unrelated shared caller')
            request={'model':model,'messages':messages,'stream':False,'keep_alive':'5m','options':plan['options']}
            journal.begin(key,request);start=time.monotonic();response=api('chat',request);after=api('ps')['models']
            journal.end(key,{'raw':response['message']['content'],'response':response,'resident_after':after,'latency_s':time.monotonic()-start})
            if not after or any(m['name']==model and m.get('size_vram',-1)!=0 for m in after):raise RuntimeError('CPU-only placement not verified')
            return response['message']['content'],response.get('done') is True and response.get('done_reason')=='stop'
        checks=[]
        for c in controls:
            raw,ended=call('control/'+c['id'],c['messages']);checks.append({'id':c['id'],'correct':ended and decode_json(raw,c['gold'])==c['gold'],'truncated':not ended})
        passed=sum(c['correct'] for c in checks)>=14 and not any(c['truncated'] for c in checks)
        row={'model':model,'digest':digest,'qualification':checks,'qualified':passed,'targets':[]}
        save_new(ROOT/'execution/qualification-2.json',row)
        print(model,'qualification',sum(c['correct'] for c in checks),'/16',flush=True)
        if passed:
            for case in cases:
                for arm in ['ainglish','english']:
                    raw,ended=call(case['id']+'/'+arm,reader_messages(case,arm,case['messages'][arm]));decoded=decode_json(raw,case['brief'])
                    row['targets'].append({'id':case['id'],'dimensions':case['dimensions'],'context':case['id'].split('/')[0],'arm':arm,'parsed':decoded is not None,'correct':ended and decoded==case['brief'],'truncated':not ended})
                    if len(row['targets'])%24==0:print(model,len(row['targets']),'targets retained',flush=True)
        loaded=api('ps')['models']
        if loaded and all(m['name']==model for m in loaded):api('generate',{'model':model,'keep_alive':0})
        save_new(ROOT/'execution/result-2.json',row)
    results=prior+[row];summaries=[]
    for reader in results:
        groups=defaultdict(list)
        for t in reader['targets']:groups[(t['arm'],t['dimensions'])].append(t)
        summaries.extend({'model':reader['model'],'arm':arm,'dimensions':n,'n':len(g),**{k:sum(r[k] for r in g) for k in ['correct','parsed','truncated']}} for (arm,n),g in groups.items())
    save_new(ROOT/'RESULTS.json',{'governance_evidence':False,'models':results,'summaries':summaries,'limits':plan['limits']})
    print(json.dumps(summaries,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);a=p.parse_args();main(a.commit)
