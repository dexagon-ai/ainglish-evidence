"""All six adapters before target evaluation; existing cached base; GPU0 only."""
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

OLD=ROOT.parent/'ratified-learning-pilot-2026-09-06'
ARTIFACTS=Path('/home/dexagon/codex/dexagon/artifacts/reasoning-transfer-20260906')

def legacy(seed):
    assert os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Only the idle physical GPU0 is in scope'
    spec=importlib.util.spec_from_file_location('tested_offline_trainer',OLD/'run.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.ROOT=ROOT;m.ARTIFACTS=ARTIFACTS/str(seed);m.rows=rows;m.verify=verify
    original=m.prepare
    def prepare():
        model,tokenizer,plan,provenance=original()
        from transformers import set_seed
        set_seed(seed);plan['seed']=seed;provenance['training_seed']=seed
        return model,tokenizer,plan,provenance
    m.prepare=prepare
    return m

def train(seed,language):
    audit();verify(public=True)
    assert seed in [17,29,43] and language in ['ainglish','english']
    legacy(seed).train(language)

def seal():
    audit();verify(public=True)
    m=legacy(17);out={}
    for seed in [17,29,43]:
        for lang in ['ainglish','english']:
            directory=ARTIFACTS/str(seed)/lang
            receipt=json.loads((directory/'training-receipt.json').read_text())
            assert receipt['training_seed']==seed
            files=m.inventory(directory);assert 'adapter_model.safetensors' in files
            out[f'{lang}-{seed}']={'files':files,'receipt':receipt,'directory':str(directory)}
    save('adapter-receipts.json',out)
    print(json.dumps({k:sum(v['bytes'] for v in r['files'].values()) for k,r in out.items()}))

def evaluate():
    audit();freeze=verify(public=True)
    rel=ROOT.name+'/adapter-receipts.json'
    commit=subprocess.check_output(['git','log','-1','--format=%H','--',rel],cwd=ROOT.parent,text=True).strip()
    assert commit
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
    assert subprocess.check_output(['git','show',f'{commit}:{rel}'],cwd=ROOT.parent)==(ROOT/'adapter-receipts.json').read_bytes()
    pins=json.loads((ROOT/'adapter-receipts.json').read_text())
    for record in pins.values():
        for name,meta in record['files'].items():assert digest(Path(record['directory'])/name)==meta['sha256']
    save('results/intent.json',{'at':time.time(),'freeze':freeze,'adapter_seal':commit,'retries':0})
    model,tokenizer,plan,provenance=legacy(17).prepare()
    import torch
    from peft import PeftModel
    first=next(iter(pins));model=PeftModel.from_pretrained(model,pins[first]['directory'],adapter_name=first,is_trainable=False)
    for name,record in list(pins.items())[1:]:model.load_adapter(record['directory'],adapter_name=name,is_trainable=False)
    model.eval();model.config.use_cache=True;tokenizer.padding_side='left'
    targets=rows('tasks.jsonl');controls=[]
    for i in range(12):
        opts=dict(zip('ABCD',[f'tag-{i}-north',f'tag-{i}-west',f'tag-{i}-east',f'tag-{i}-south']));answer='ABCD'[i%4]
        controls.append({'id':f'control/{i}','options':opts,'answer':answer,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':f'The one recorded label is {opts[answer]}. Which label is recorded?\n'+'\n'.join(k+'. '+v for k,v in opts.items())}]})
    for condition in plan['conditions']:
        guard=model.disable_adapter() if condition=='base' else contextlib.nullcontext()
        if condition!='base':model.set_adapter(condition)
        with (ROOT/'results'/f'{condition}.jsonl').open('x') as journal,guard:
            def execute(batch,phase,offset):
                intent={'phase':phase,'offset':offset,'ids':[r['id'] for r in batch],'at':time.time()}
                dump(ROOT/'results'/f'{condition}.inflight.json',intent)
                prompts=[tokenizer.apply_chat_template(r['messages'],tokenize=False,add_generation_prompt=True) for r in batch]
                encoded=tokenizer(prompts,return_tensors='pt',padding=True,add_special_tokens=False).to(model.device)
                assert encoded['input_ids'].shape[1]<=plan['guards']['max_prompt_tokens']
                started=time.time();width=encoded['input_ids'].shape[1]
                with torch.inference_mode():generated=model.generate(**encoded,max_new_tokens=8,do_sample=False,pad_token_id=tokenizer.eos_token_id,eos_token_id=tokenizer.eos_token_id)
                result=[]
                for case,tokens,length in zip(batch,generated[:,width:].tolist(),encoded['attention_mask'].sum(dim=1).tolist()):
                    ended=tokenizer.eos_token_id in tokens
                    if ended:tokens=tokens[:tokens.index(tokenizer.eos_token_id)+1]
                    raw=tokenizer.decode(tokens,skip_special_tokens=True).strip()
                    rec={k:case.get(k) for k in ['id','case_id','family','frame','study','arm','answer','semantic_gold']}
                    rec.update(condition=condition,phase=phase,raw=raw,valid=raw in case['options'] and ended,
                        correct=raw==case['answer'] and ended,truncated=not ended,input_tokens=length,
                        output_tokens=len(tokens),batch_latency_s=round(time.time()-started,3))
                    journal.write(json.dumps(rec,ensure_ascii=False)+'\n');result.append(rec)
                journal.flush();os.fsync(journal.fileno());dump(ROOT/'results'/f'{condition}.inflight.json',dict(intent,status='recorded'))
                return result
            observed=[]
            for i in range(0,12,8):observed+=execute(controls[i:i+8],'control',i)
            if sum(r['correct'] for r in observed)<11 or any(not r['valid'] for r in observed):
                save(f'results/{condition}.receipt.json',dict(provenance,status='aborted-control',targets=0,controls=12,governance_evidence=False))
                continue
            for i in range(0,len(targets),8):
                execute(targets[i:i+8],'target',i)
                if i%128==0:print(condition,min(i+8,len(targets)),'/',len(targets),flush=True)
        save(f'results/{condition}.receipt.json',dict(provenance,status='complete',targets=len(targets),controls=12,governance_evidence=False))
    save('results/finished.json',{'at':time.time(),'status':'finished','downloads':0,'governance_evidence':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['train','seal','evaluate']);p.add_argument('--seed',type=int);p.add_argument('--language',choices=['ainglish','english']);a=p.parse_args()
    if a.action=='train':train(a.seed,a.language)
    elif a.action=='seal':seal()
    else:evaluate()
