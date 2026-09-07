"""Four sealed adapters before target exposure. Offline, guarded, durable no-retry execution."""
import argparse
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from audit import ROOT,audit,digest,rows,verify
from build import SYSTEM,dump,save
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import Journal,LocalReader,disk_guard,preallocate_gpu_guard
ARTIFACTS=Path('/home/dexagon/codex/dexagon/artifacts/contextual-transfer-20260907')

def resources():
    available=next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
    if available < 14*1024**3:raise RuntimeError('Need14GiB available RAM; do not displace another workload.')
    disk_guard();preallocate_gpu_guard()

def legacy(seed):
    spec=importlib.util.spec_from_file_location('frozen_contextual_trainer',ROOT.parent/'ratified-learning-pilot-2026-09-06/run.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=ROOT;module.ARTIFACTS=ARTIFACTS/str(seed);module.rows=rows;module.verify=verify
    original=module.prepare
    def prepare():
        resources();model,tokenizer,plan,provenance=original()
        from transformers import set_seed
        set_seed(seed);plan['seed']=seed;provenance['training_seed']=seed
        return model,tokenizer,plan,provenance
    module.prepare=prepare
    return module

def train(seed,language):
    assert seed in [17,29] and language in ['ainglish','english']
    audit();verify(public=True);resources()
    legacy(seed).train(language)

def seal():
    audit();verify(public=True);module=legacy(17);pins={}
    for seed in [17,29]:
        for language in ['ainglish','english']:
            directory=ARTIFACTS/str(seed)/language
            receipt=json.loads((directory/'training-receipt.json').read_text())
            assert receipt['training_seed']==seed and receipt['rows']==768
            inventory=module.inventory(directory);assert 'adapter_model.safetensors' in inventory
            pins[f'{language}-{seed}']={'directory':str(directory),'receipt':receipt,'files':inventory}
    assert sum(v['bytes'] for r in pins.values() for v in r['files'].values())<=2*1024**3
    save('adapter-receipts.json',pins)

def verify_adapters():
    relative=ROOT.name+'/adapter-receipts.json'
    commit=subprocess.check_output(['git','log','-1','--format=%H','--',relative],cwd=ROOT.parent,text=True).strip()
    assert commit
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
    assert subprocess.check_output(['git','show',f'{commit}:{relative}'],cwd=ROOT.parent)==(ROOT/'adapter-receipts.json').read_bytes()
    pins=json.loads((ROOT/'adapter-receipts.json').read_text());assert len(pins)==4
    for pin in pins.values():assert legacy(17).inventory(Path(pin['directory']))==pin['files']
    return commit,pins

def evaluate():
    audit();freeze=verify(public=True);adapter_commit,pins=verify_adapters();resources()
    save('results/intent.json',{'freeze':freeze,'adapter_commit':adapter_commit,'started':time.time(),'uncertain_retries':0})
    plan=json.loads((ROOT/'PLAN.json').read_text())
    reader=LocalReader('/home/dexagon/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/'+plan['base_revision'])
    import torch
    from peft import PeftModel
    first=next(iter(pins))
    model=PeftModel.from_pretrained(reader.model,pins[first]['directory'],adapter_name=first,is_trainable=False,local_files_only=True)
    for name,pin in list(pins.items())[1:]:model.load_adapter(pin['directory'],adapter_name=name,is_trainable=False,local_files_only=True)
    model.eval();model.config.use_cache=True;tokenizer=reader.tokenizer;tokenizer.padding_side='left'
    controls=[]
    for i in range(12):
        labels={k:f'square-{9600+i}-{n}' for n,k in enumerate('ABCD')};answer='ABCD'[i%4]
        controls.append({'id':f'control-{i}','answer':answer,'options':labels,'messages':[
            {'role':'system','content':SYSTEM},{'role':'user','content':'The recorded label is '+labels[answer]+'. Which label is recorded?\n'+'\n'.join(k+'. '+v for k,v in labels.items())}]})
    for condition in plan['conditions']:
        guard=model.disable_adapter() if condition=='base' else contextlib.nullcontext()
        if condition!='base':model.set_adapter(condition)
        with Journal(ROOT/f'results/{condition}.calls.jsonl',{'freeze':freeze,'adapter_seal':adapter_commit,'condition':condition,'batch_size':8,'output_cap':8,'provenance':reader.provenance}) as journal,guard:
            def batch(cases,phase,offset):
                disk_guard()
                prompts=[tokenizer.apply_chat_template(r['messages'],tokenize=False,add_generation_prompt=True) for r in cases]
                encoded=tokenizer(prompts,return_tensors='pt',padding=True,add_special_tokens=False).to(model.device)
                width=encoded['input_ids'].shape[1];assert width<=2048
                requests=[{'messages':r['messages'],'max_new_tokens':8,'do_sample':False,'phase':phase,'batch_offset':offset} for r in cases]
                for case,request in zip(cases,requests):journal.begin(case['id'],request)
                started=time.time()
                with torch.inference_mode():generated=model.generate(**encoded,max_new_tokens=8,do_sample=False,pad_token_id=tokenizer.eos_token_id,eos_token_id=tokenizer.eos_token_id)
                elapsed=time.time()-started;out=[]
                for case,output,inputs,mask in zip(cases,generated[:,width:].tolist(),encoded['input_ids'].tolist(),encoded['attention_mask'].tolist()):
                    ended=tokenizer.eos_token_id in output
                    if ended:output=output[:output.index(tokenizer.eos_token_id)+1]
                    exact=[v for v,m in zip(inputs,mask) if m]
                    raw=tokenizer.decode(output,skip_special_tokens=True).strip()
                    journal.end(case['id'],{'raw':raw,'ended':ended,'input_ids':exact,'output_ids':output,
                        'input_tokens':len(exact),'output_tokens':len(output),'batch_latency_s':elapsed,'batch_offset':offset,'phase':phase})
                    rec={k:case.get(k) for k in ['id','case_id','family','frame','study','arm','answer','semantic_gold','gold_bits']}
                    rec.update(raw=raw,valid=ended and raw in case['options'],correct=ended and raw==case['answer'],truncated=not ended)
                    out.append(rec)
                return out
            observed=[]
            for offset in [0,8]:observed+=batch(controls[offset:offset+8],'control',offset)
            qualified=sum(r['correct'] for r in observed)>=11 and all(r['valid'] for r in observed)
            result={'condition':condition,'qualified':qualified,'controls':observed,'targets':[]}
            if qualified:
                tasks=rows('tasks.jsonl')
                for offset in range(0,len(tasks),8):
                    result['targets']+=batch(tasks[offset:offset+8],'target',offset)
                    if offset%64==0:print(condition,offset+8,'/',len(tasks),flush=True)
            save(f'results/{condition}.json',result)
    save('results/finished.json',{'at':time.time(),'conditions':plan['conditions'],'downloads':0,'governance_evidence':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['train','seal','evaluate']);p.add_argument('--seed',type=int);p.add_argument('--language',choices=['ainglish','english']);a=p.parse_args()
    if a.action=='train':train(a.seed,a.language)
    elif a.action=='seal':seal()
    else:evaluate()
