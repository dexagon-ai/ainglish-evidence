"""Prospective cross-family diagnostic using cached models, CPU-only shared serving.

Not a governance replication. Reuses the published diagnostic cases deliberately;
these are new readers/configurations, not a newly independent holdout.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import Journal, disk_guard, save_new, verify_freeze
sys.path.insert(0,str(ROOT.parent/'communication-diagnostics-2026-09-06'))
from design import reader_messages, decode_json

MODELS=[('qwen2.5:7b','845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'),
 ('gemma3:12b','f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a'),
 ('mistral-small3.2:24b-instruct-2506-q4_K_M','5a408ab55df5c1b5cf46533c368813b30bf9e4d8fc39263bf2a3338cfa3b895b')]

def api(path,body=None):
    url='http://127.0.0.1:11434/api/'+path
    request=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=600) as response:return json.load(response)

def ram():
    values={line.split(':',1)[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')}
    return values['MemAvailable']

def build():
    controls=[]
    fields=['sealed','metal','fragile','cooled','labelled']
    terms=[['open','sealed'],['wood','metal'],['sturdy','fragile'],['warm','cooled'],['unlabelled','labelled']]
    for i in range(16):
        bits=[bool(i&(1<<j)) for j in range(4)];bits.append(bits[0]^bits[1])
        gold=dict(zip(fields,bits))
        facts='; '.join(f'{key}: {words[int(bit)]}' for key,words,bit in zip(fields,terms,bits))
        controls.append({'id':f'package-{910+i}','gold':gold,'messages':[
            {'role':'system','content':'Read the package record. Return only one JSON object with exactly the five named boolean fields. No explanation or markdown.'},
            {'role':'user','content':f'Package {910+i}: '+facts+'. Fields, in order: '+', '.join(fields)+'. Use true when the positive property named by the field is present, false otherwise.'}]})
    plan={'kind':'ainglish.cached-reader-diagnostic.v1','governance_evidence':False,'models':MODELS,
        'options':{'num_gpu':0,'num_thread':8,'num_ctx':8192,'num_predict':512,'temperature':0,'seed':20260907},
        'controls':16,'minimum_controls_correct':14,'control_truncations_allowed':0,
        'target_dimensions':[2,5],'target_calls_per_qualified_model':216,
        'selection':'All 2- and 5-field reference cases from the published diagnostic, both languages, all three contexts. The one-field irrelevant-key issue is not being retested. No writers, adapters, retries or target-selected substitutions.',
        'qualification':'Each model must pass its target-independent compound five-field screen before seeing any target. Failed models are reported, not replaced. Target accuracy does not redefine qualification.',
        'analysis':'Exact JSON protocol and exact boolean joint accuracy by language, dimension and authored context. Show absolute counts and format errors separately, no pooled cross-family success claim.',
        'tokens':'Native Ollama prompt_eval_count and eval_count are retained with raw responses. Generated token IDs are unavailable; no exact output-ID recount claim.',
        'resources':'CPU-only request, verify size_vram=0 after every call; one model at a time; no service restart, downloads or unrelated-model eviction. Stop on uncertain transport or <3GiB available RAM.',
        'limits':['Qwen GGUF differs from the earlier native NF4 reader; not a same-configuration repeat.',
            'Previously published synthetic cases, not a fresh independent holdout or human evidence.',
            'Three model families do not prove independent training corpora. Both language guides are visible.',
            'This does not settle any proposal or unlock the separate failed adapter-training gate.']}
    for name,value in [('PLAN.json',plan),('controls.json',controls)]:save_new(ROOT/name,value)
    names=['study.py','PLAN.json','controls.json','../communication-diagnostics-2026-09-06/design.py','../communication-diagnostics-2026-09-06/cases.json','../overnight-runtime-2026-09-06/runtime.py']
    save_new(ROOT/'FROZEN.json',{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})

def run():
    commit=verify_freeze(ROOT);plan=json.loads((ROOT/'PLAN.json').read_text());controls=json.loads((ROOT/'controls.json').read_text())
    cases=[c for c in json.loads((ROOT.parent/'communication-diagnostics-2026-09-06/cases.json').read_text()) if c['dimensions'] in plan['target_dimensions']]
    assert len(cases)*2==216
    if api('ps')['models']:raise RuntimeError('Shared service occupied; no eviction')
    tags={m['name']:m for m in api('tags')['models']}
    for model,digest in plan['models']:assert tags[model]['digest']==digest
    save_new(ROOT/'execution/intent.json',{'freeze':commit,'ollama_version':api('version'),'target_calls_started':0})
    results=[]
    for index,(model,digest) in enumerate(plan['models']):
        disk_guard()
        if ram()<tags[model]['size']*1.1+4*1024**3:raise RuntimeError('Insufficient available host memory before loading this cached model')
        if api('ps')['models']:raise RuntimeError('Another model arrived before this reader; do not evict it')
        with Journal(ROOT/f'execution/reader-{index}.jsonl',dict(plan,selected_model=model)) as journal:
            def call(key,messages):
                disk_guard()
                if ram()<3*1024**3:raise RuntimeError('Host memory reserve reached')
                loaded=api('ps')['models']
                if any(m['name']!=model for m in loaded):raise RuntimeError('Unrelated shared caller; stop before another call')
                request={'model':model,'messages':messages,'stream':False,'keep_alive':'5m','options':plan['options']}
                journal.begin(key,request);start=time.monotonic()
                response=api('chat',request)
                after=api('ps')['models']
                # Save the received answer even if the placement check fails, without retry.
                journal.end(key,{'raw':response['message']['content'],'response':response,'resident_after':after,'latency_s':time.monotonic()-start})
                if not after or any(m['name']==model and m.get('size_vram',-1)!=0 for m in after):raise RuntimeError('CPU-only placement could not be verified')
                return response['message']['content'],response.get('done') is True and response.get('done_reason')=='stop'
            checks=[]
            for c in controls:
                raw,ended=call('control/'+c['id'],c['messages']);checks.append({'id':c['id'],'correct':ended and decode_json(raw,c['gold'])==c['gold'],'truncated':not ended})
            passed=sum(c['correct'] for c in checks)>=14 and not any(c['truncated'] for c in checks)
            row={'model':model,'digest':digest,'qualification':checks,'qualified':passed,'targets':[]}
            save_new(ROOT/f'execution/qualification-{index}.json',row)
            print(model,'qualification',sum(c['correct'] for c in checks),'/16',flush=True)
            if passed:
                for case in cases:
                    for arm in ['ainglish','english']:
                        raw,ended=call(case['id']+'/'+arm,reader_messages(case,arm,case['messages'][arm]))
                        decoded=decode_json(raw,case['brief'])
                        row['targets'].append({'id':case['id'],'dimensions':case['dimensions'],'context':case['id'].split('/')[0],'arm':arm,'parsed':decoded is not None,'correct':ended and decoded==case['brief'],'truncated':not ended})
                        if len(row['targets'])%24==0:print(model,len(row['targets']),'targets retained',flush=True)
            # Only unload the model this run loaded, and only while no other model is present.
            loaded=api('ps')['models']
            if loaded and all(m['name']==model for m in loaded):api('generate',{'model':model,'keep_alive':0})
            save_new(ROOT/f'execution/result-{index}.json',row);results.append(row)
    summaries=[]
    for row in results:
        groups=defaultdict(list)
        for t in row['targets']:groups[(t['arm'],t['dimensions'])].append(t)
        summaries.extend({'model':row['model'],'arm':arm,'dimensions':n,'n':len(g),**{k:sum(r[k] for r in g) for k in ['correct','parsed','truncated']}} for (arm,n),g in groups.items())
    save_new(ROOT/'RESULTS.json',{'governance_evidence':False,'models':results,'summaries':summaries,'limits':plan['limits']})
    print(json.dumps(summaries,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);args=p.parse_args()
    build() if args.action=='build' else run()
