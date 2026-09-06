#!/usr/bin/env python3
"""Offline paired-adapter training and retained, no-retry research inference."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time

for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE'):
    os.environ[key]='1'
from audit import ROOT, digest, rows, verify
from build import SYSTEM, dump, messages

ARTIFACTS=ROOT.parent.parent/'artifacts'/'ratified-learning-20260906'


def inventory(path):
    return {p.relative_to(path).as_posix():{'sha256':digest(p),'bytes':p.stat().st_size}
            for p in sorted(path.rglob('*')) if p.is_file()}


def prepare():
    commit=verify(public=True)
    plan=json.loads((ROOT/'PLAN.json').read_text())
    if os.environ.get('CUDA_VISIBLE_DEVICES') not in ('0','1'):
        raise RuntimeError('Explicitly isolate one physical GPU')
    snapshot=Path('/home/dexagon/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots')/plan['base_revision']
    if not snapshot.is_dir(): raise RuntimeError('Cached pinned base is absent; downloads prohibited')
    # Never proceed on the optimistic WSL virtual-disk number alone.
    import shutil
    if shutil.disk_usage('/mnt/c').free < 10*1024**3: raise RuntimeError('Host disk below 10 GiB reserve')
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1: raise RuntimeError('One CUDA device required')
    free,_=torch.cuda.mem_get_info()
    if free < 16*1024**3: raise RuntimeError('Insufficient free VRAM; do not displace another workload')
    set_seed(plan['seed'])
    tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True,use_fast=True)
    tokenizer.pad_token=tokenizer.eos_token
    quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=True)
    model=AutoModelForCausalLM.from_pretrained(str(snapshot),local_files_only=True,quantization_config=quant,device_map={'':0},torch_dtype=torch.bfloat16)
    provenance={'freeze_commit':commit,'base_revision':plan['base_revision'],
                'tokenizer_sha256':digest(snapshot/'tokenizer.json'),'base_config_sha256':digest(snapshot/'config.json'),
                'versions':{n:importlib.metadata.version(n) for n in ('torch','transformers','peft','bitsandbytes','tokenizers')},
                'physical_gpu':os.environ['CUDA_VISIBLE_DEVICES'],'gpu':torch.cuda.get_device_name(0),'downloads':0}
    return model,tokenizer,plan,provenance


def train(language):
    target=ARTIFACTS/language
    if target.exists(): raise RuntimeError('Refusing to overwrite an adapter or retry a training attempt')
    # A durable intent is written before model allocation, outside the frozen input tree.
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    intent=ARTIFACTS/f'{language}.intent.json'
    with intent.open('x') as handle: json.dump({'started_unix':time.time(),'freeze':verify(public=True)},handle)
    model,tokenizer,plan,provenance=prepare()
    import torch
    from peft import LoraConfig,get_peft_model,prepare_model_for_kbit_training
    from transformers import Trainer,TrainingArguments
    tokenizer.padding_side='right'
    encoded=[]
    for item in rows(f'train-{language}.jsonl'):
        prompt=tokenizer.apply_chat_template(item['messages'][:-1],tokenize=True,add_generation_prompt=True)
        full=tokenizer.apply_chat_template(item['messages'],tokenize=True,add_generation_prompt=False)
        assert full[:len(prompt)]==prompt, 'Chat template prefix is not stable'
        assert len(full)<=plan['training']['max_length'] and len(full)>len(prompt)
        encoded.append({'input_ids':full,'attention_mask':[1]*len(full),'labels':[-100]*len(prompt)+full[len(prompt):]})
    def collate(batch):
        width=max(len(r['input_ids']) for r in batch)
        return {k:torch.tensor([r[k]+[tokenizer.pad_token_id if k=='input_ids' else (-100 if k=='labels' else 0)]*(width-len(r[k])) for r in batch]) for k in ('input_ids','attention_mask','labels')}
    f=plan['training']
    model.config.use_cache=False
    model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=True)
    model=get_peft_model(model,LoraConfig(r=f['lora_r'],lora_alpha=f['lora_alpha'],lora_dropout=f['lora_dropout'],bias='none',task_type='CAUSAL_LM',target_modules=f['target_modules']))
    trainer=Trainer(model=model,args=TrainingArguments(output_dir=str(target),num_train_epochs=f['epochs'],
        per_device_train_batch_size=f['batch_size'],gradient_accumulation_steps=f['gradient_accumulation_steps'],
        learning_rate=f['learning_rate'],warmup_ratio=0.05,lr_scheduler_type='cosine',optim='adamw_torch',
        logging_steps=10,save_strategy='no',report_to='none',bf16=True,tf32=True,gradient_checkpointing=True,
        remove_unused_columns=False,seed=plan['seed'],data_seed=plan['seed'],dataloader_num_workers=0),
        train_dataset=encoded,data_collator=collate)
    started=time.time(); metrics=trainer.train().metrics
    trainer.save_model(str(target))
    receipt={**provenance,'condition':language,'started_unix':started,'finished_unix':time.time(),
             'source_sha256':digest(ROOT/f'train-{language}.jsonl'),'rows':len(encoded),
             'input_tokens_per_epoch':sum(len(r['input_ids']) for r in encoded),
             'supervised_tokens_per_epoch':sum(sum(x!=-100 for x in r['labels']) for r in encoded),
             'training':f,'metrics':metrics,'governance_evidence':False}
    dump(target/'training-receipt.json',receipt)
    files=inventory(target)
    if sum(x['bytes'] for x in files.values())>f['max_artifact_bytes']: raise RuntimeError('Artifact ceiling exceeded')
    print(json.dumps(receipt,indent=2))


def seal():
    verify(public=True)
    output=ROOT/'adapter-receipts.json'
    if output.exists(): raise RuntimeError('Adapters already sealed')
    packet={language:{'files':inventory(ARTIFACTS/language),'receipt':json.loads((ARTIFACTS/language/'training-receipt.json').read_text())} for language in ('ainglish','english')}
    for adapter in packet.values(): assert 'adapter_model.safetensors' in adapter['files']
    dump(output,packet)
    print(json.dumps({k:sum(x['bytes'] for x in v['files'].values()) for k,v in packet.items()}))


def evaluate(condition):
    resultdir=ROOT/'results'
    resultdir.mkdir(exist_ok=True)
    intent=resultdir/f'{condition}.intent.json'
    with intent.open('x') as handle: json.dump({'started_unix':time.time(),'condition':condition},handle)
    # Both adaptations are pinned publicly before ANY target evaluation.
    relative=str((ROOT/'adapter-receipts.json').relative_to(ROOT.parent))
    subprocess.run(['git','diff','--exit-code','HEAD','--',relative],cwd=ROOT.parent,check=True,stdout=subprocess.DEVNULL)
    adapter_commit=subprocess.check_output(['git','log','-1','--format=%H','--',relative],cwd=ROOT.parent,text=True).strip()
    assert adapter_commit
    subprocess.run(['git','merge-base','--is-ancestor',adapter_commit,'origin/main'],cwd=ROOT.parent,check=True)
    adapters=json.loads((ROOT/'adapter-receipts.json').read_text())
    for language,pin in adapters.items(): assert inventory(ARTIFACTS/language)==pin['files'], 'Adapter drift'
    model,tokenizer,plan,provenance=prepare()
    import torch
    if condition!='base':
        from peft import PeftModel
        model=PeftModel.from_pretrained(model,str(ARTIFACTS/condition),local_files_only=True)
    model.eval(); tokenizer.padding_side='left'
    controls=[]
    for i in range(12):
        answer='ABC'[i%3]
        choices={k:str(71+i+(0 if k==answer else ord(k))) for k in 'ABC'}
        prompt=f'The record states that the exact code is {71+i}. Which option is that code?\n'+'\n'.join(k+'. '+v for k,v in choices.items())
        controls.append({'id':f'control/{i}','answer':answer,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}]})
    tasks=[{**case,'arm':arm,'id':case['id']+'/'+arm,'messages':messages(case,arm)} for case in rows('evaluation.jsonl') for arm in plan['arms']]
    journal=resultdir/f'{condition}.jsonl'
    def execute(batch,phase,index):
        inflight=resultdir/f'{condition}.inflight.json'
        dump(inflight,{'phase':phase,'index':index,'ids':[r['id'] for r in batch],'started_unix':time.time()})
        prompts=[tokenizer.apply_chat_template(r['messages'],tokenize=False,add_generation_prompt=True) for r in batch]
        tensors=tokenizer(prompts,return_tensors='pt',padding=True,add_special_tokens=False).to(model.device)
        width=tensors['input_ids'].shape[1];started=time.time()
        with torch.inference_mode():
            outputs=model.generate(**tensors,max_new_tokens=8,do_sample=False,pad_token_id=tokenizer.eos_token_id,eos_token_id=tokenizer.eos_token_id)
        observed=[]
        for source,answer_ids,length in zip(batch,outputs[:,width:].tolist(),tensors['attention_mask'].sum(dim=1).tolist()):
            if tokenizer.eos_token_id in answer_ids: answer_ids=answer_ids[:answer_ids.index(tokenizer.eos_token_id)+1]
            raw=tokenizer.decode(answer_ids,skip_special_tokens=True).strip()
            observed.append({'id':source['id'],'phase':phase,'condition':condition,'family':source.get('family'),
                'frame':source.get('frame'),'arm':source.get('arm'),'boundary_case':source.get('boundary_case'),
                'expected':source['answer'],'raw':raw,'valid':raw in ('A','B','C'),'correct':raw==source['answer'],
                'input_tokens':length,'output_tokens':len(answer_ids),'batch_latency_s':time.time()-started})
        with journal.open('a') as handle:
            for record in observed: handle.write(json.dumps(record,ensure_ascii=False)+'\n')
            handle.flush();os.fsync(handle.fileno())
        dump(inflight,{'phase':phase,'index':index,'status':'recorded'})
        return observed
    screened=[]
    for i in range(0,12,8): screened+=execute(controls[i:i+8],'controls',i)
    if sum(r['correct'] for r in screened)<10:
        dump(resultdir/f'{condition}.receipt.json',{**provenance,'status':'aborted-control','correct_controls':sum(r['correct'] for r in screened),'targets':0})
        raise SystemExit('Controls failed; retaining outputs, no target calls')
    for offset in range(0,len(tasks),8):
        execute(tasks[offset:offset+8],'target',offset)
        if offset%64==0: print(f'{condition}: {offset+8}/{len(tasks)}',flush=True)
    dump(resultdir/f'{condition}.receipt.json',{**provenance,'status':'complete','targets':len(tasks),'controls':12,'adapter_commit':adapter_commit,'governance_evidence':False})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['train','seal','evaluate']);p.add_argument('condition',nargs='?',choices=['base','ainglish','english']);a=p.parse_args()
    if a.action=='seal': seal()
    elif a.action=='train' and a.condition in ('ainglish','english'): train(a.condition)
    elif a.action=='evaluate' and a.condition: evaluate(a.condition)
    else: p.error('Select a condition')
