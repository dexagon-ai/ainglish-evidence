"""Paired local adapters and frozen research tasks; no downloads or governance writes."""
import argparse
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'ratified-learning-pilot-2026-09-06'
from audit_research import audit,digest,rows,verify
from build_research import SYSTEM,save


def legacy(artifacts):
    # Reuse the already exercised offline NF4/LoRA trainer, not another instrument.
    sys.path.insert(0,str(OLD))
    spec=importlib.util.spec_from_file_location('prior_offline_trainer',OLD/'run.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=ROOT;module.ARTIFACTS=artifacts;module.rows=rows;module.verify=verify
    return module


def train(condition,artifacts):
    audit();verify(public=True)
    assert condition in ('ainglish','english')
    legacy(artifacts).train(condition)


def seal(artifacts):
    module=legacy(artifacts)
    packet={language:{'files':module.inventory(artifacts/language),'receipt':json.loads((artifacts/language/'training-receipt.json').read_text())} for language in ['ainglish','english']}
    for record in packet.values():assert 'adapter_model.safetensors' in record['files']
    save('adapter-receipts.json',packet)
    print(json.dumps({k:sum(x['bytes'] for x in v['files'].values()) for k,v in packet.items()}))


def evaluate(artifacts,prior_artifacts):
    audit();verify(public=True)
    relative=f'{ROOT.name}/adapter-receipts.json'
    seal_commit=subprocess.check_output(['git','log','-1','--format=%H','--',relative],cwd=ROOT.parent,text=True).strip()
    assert seal_commit
    subprocess.run(['git','merge-base','--is-ancestor',seal_commit,'origin/main'],cwd=ROOT.parent,check=True)
    assert subprocess.check_output(['git','show',f'{seal_commit}:{relative}'],cwd=ROOT.parent)==(ROOT/'adapter-receipts.json').read_bytes()
    pins=json.loads((ROOT/'adapter-receipts.json').read_text())
    oldpins=json.loads((OLD/'adapter-receipts.json').read_text())
    for directory,expected in [(artifacts,pins),(prior_artifacts,oldpins)]:
        for language,record in expected.items():
            for name,meta in record['files'].items():assert digest(directory/language/name)==meta['sha256']
    destination=ROOT/'research-results';destination.mkdir(exist_ok=True)
    with (destination/'intent.json').open('x') as h:json.dump({'at':time.time(),'freeze':verify(public=True),'adapter_seal':seal_commit,'retries':0},h)
    model,tokenizer,plan,provenance=legacy(artifacts).prepare()
    import torch
    from peft import PeftModel
    model=PeftModel.from_pretrained(model,str(artifacts/'ainglish'),adapter_name='ainglish',is_trainable=False)
    model.load_adapter(str(artifacts/'english'),adapter_name='english',is_trainable=False)
    model.load_adapter(str(prior_artifacts/'ainglish'),adapter_name='prior-ainglish',is_trainable=False)
    model.load_adapter(str(prior_artifacts/'english'),adapter_name='prior-english',is_trainable=False)
    model.eval();tokenizer.padding_side='left';model.config.use_cache=True
    targets=rows('research-tasks.jsonl')
    controls=[]
    for i in range(12):
        opts=dict(zip('ABC',[f'person-{i}-north',f'person-{i}-south',f'person-{i}-west']))
        answer='ABC'[i%3]
        body=f'The record explicitly identifies {opts[answer]} as the sole holder of key Q-{i}. Who holds that key?\n'+'\n'.join(k+'. '+v for k,v in opts.items())
        controls.append({'id':f'control/{i}','options':opts,'answer':answer,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':body}]})
    for condition in ['base','ainglish','english','prior-ainglish','prior-english']:
        selected=targets if not condition.startswith('prior-') else [r for r in targets if r['study'] in ['retention','option-permutation']]
        guard=model.disable_adapter() if condition=='base' else contextlib.nullcontext()
        if condition!='base':model.set_adapter(condition)
        with (destination/(condition+'.jsonl')).open('x') as journal,guard:
            def execute(batch,phase,offset):
                intent={'phase':phase,'offset':offset,'ids':[r['id'] for r in batch],'at':time.time()}
                with (destination/(condition+'.inflight.json')).open('w') as h:json.dump(intent,h)
                prompts=[tokenizer.apply_chat_template(r['messages'],tokenize=False,add_generation_prompt=True) for r in batch]
                encoded=tokenizer(prompts,return_tensors='pt',padding=True,add_special_tokens=False).to(model.device)
                assert encoded['input_ids'].shape[1]<=2048,'Declared prompt bound exceeded; no silent truncation'
                start=time.time();width=encoded['input_ids'].shape[1]
                with torch.inference_mode():out=model.generate(**encoded,max_new_tokens=8,do_sample=False,pad_token_id=tokenizer.eos_token_id,eos_token_id=tokenizer.eos_token_id)
                result=[]
                for case,tokens,length in zip(batch,out[:,width:].tolist(),encoded['attention_mask'].sum(dim=1).tolist()):
                    ended=tokenizer.eos_token_id in tokens
                    if ended:tokens=tokens[:tokens.index(tokenizer.eos_token_id)+1]
                    raw=tokenizer.decode(tokens,skip_special_tokens=True).strip()
                    rec={k:case.get(k) for k in ['id','study','case_id','family','frame','arm','boundary_case','answer','semantic_gold']}
                    rec.update(condition=condition,phase=phase,raw=raw,valid=raw in case['options'] and ended,correct=raw==case['answer'] and ended,
                        input_tokens=length,output_tokens=len(tokens),truncated=not ended,batch_latency_s=round(time.time()-start,3))
                    journal.write(json.dumps(rec,ensure_ascii=False)+'\n');result.append(rec)
                journal.flush();os.fsync(journal.fileno())
                with (destination/(condition+'.inflight.json')).open('w') as h:json.dump(dict(intent,status='recorded'),h)
                return result
            seen=[]
            for offset in range(0,12,8):seen+=execute(controls[offset:offset+8],'control',offset)
            if sum(r['correct'] for r in seen)<11 or any(not r['valid'] or r['truncated'] for r in seen):
                save('research-results/'+condition+'.receipt.json',dict(provenance,status='aborted-control',targets=0,governance_evidence=False))
                raise SystemExit('Control failure: no targets, no retry; later conditions not run')
            for offset in range(0,len(selected),8):
                execute(selected[offset:offset+8],'target',offset)
                if offset%128==0:print(condition,min(offset+8,len(selected)),'/',len(selected),flush=True)
        save('research-results/'+condition+'.receipt.json',dict(provenance,status='complete',targets=len(selected),controls=12,governance_evidence=False))
    save('research-results/finished.json',{'at':time.time(),'status':'complete','model_downloads':0})


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['train','seal','evaluate'])
    parser.add_argument('--condition',choices=['ainglish','english'])
    parser.add_argument('--artifacts',type=Path,required=True)
    parser.add_argument('--prior-artifacts',type=Path)
    args=parser.parse_args()
    assert args.artifacts.is_absolute() and args.artifacts.name=='usefulness-learning-20260906'
    if args.action=='train':train(args.condition,args.artifacts)
    elif args.action=='seal':seal(args.artifacts)
    else:evaluate(args.artifacts,args.prior_artifacts)
