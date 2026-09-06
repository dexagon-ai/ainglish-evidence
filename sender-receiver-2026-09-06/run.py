"""Cached GPU0 only; immutable call journal; no selective retries or hidden oracle feedback."""
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
from design import ROOT,FIELDS,GUIDES,SENDER_SYSTEM,RECEIVER_SYSTEM,save


def decode(raw, ended):
    if not ended:return None
    try:
        def pairs(rows):
            if len({k for k,v in rows}) != len(rows):raise ValueError('duplicate field')
            return dict(rows)
        value=json.loads(raw,object_pairs_hook=pairs)
        if not isinstance(value,dict) or set(value)!=set(FIELDS):return None
        if any(v is not None and type(v) is not bool for v in value.values()):return None
        return value
    except (ValueError,TypeError):return None


def prose_format(raw, ended):
    if not ended or not raw.strip() or any(k in raw for k in FIELDS):return False
    try:
        json.loads(raw)
        return False
    except ValueError:
        return True # A narrow format check, not a semantic judgement of the sender's prose.


def verify():
    frozen=json.loads((ROOT/'FROZEN.json').read_text())
    for name,digest in frozen.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    commit=subprocess.check_output(['git','log','-1','--format=%H','--',ROOT.name+'/FROZEN.json'],cwd=ROOT.parent,text=True).strip()
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
    for name in [*frozen,'FROZEN.json']:
        assert subprocess.check_output(['git','show',f'{commit}:{ROOT.name}/{name}'],cwd=ROOT.parent)==(ROOT/name).read_bytes(),name
    return commit


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES')=='0'
    freeze=verify();plan=json.loads((ROOT/'PLAN.json').read_text());cases=json.loads((ROOT/'cases.json').read_text())
    assert not (ROOT/'results/intent.json').exists(),'No automatic rerun after spend intent'
    folder=ROOT.parent/'learning-transfer-2026-09-06'
    seal=subprocess.check_output(['git','rev-parse',plan['adapter_seal']+'^{commit}'],cwd=ROOT.parent,text=True).strip()
    pinbytes=subprocess.check_output(['git','show',f'{seal}:{folder.name}/adapter-receipts.json'],cwd=ROOT.parent)
    pins=json.loads(pinbytes)
    for key in ['ainglish-17','english-17']:
        for name,meta in pins[key]['files'].items():
            assert hashlib.sha256((Path(pins[key]['directory'])/name).read_bytes()).hexdigest()==meta['sha256']
    save(ROOT/'results/intent.json',{'at':time.time(),'freeze':freeze,'adapter_seal':seal,'downloads':0})
    spec=importlib.util.spec_from_file_location('transfer',folder/'run.py');m=importlib.util.module_from_spec(spec)
    import sys
    sys.path.insert(0,str(folder));spec.loader.exec_module(m)
    model,tokenizer,_,provenance=m.legacy(17).prepare()
    import torch
    from peft import PeftModel
    model=PeftModel.from_pretrained(model,pins['ainglish-17']['directory'],adapter_name='ainglish-17',is_trainable=False)
    model.load_adapter(pins['english-17']['directory'],adapter_name='english-17',is_trainable=False)
    model.eval();model.config.use_cache=True
    for condition in plan['conditions']:
        guard=model.disable_adapter() if condition=='base' else contextlib.nullcontext()
        if condition!='base':model.set_adapter(condition)
        with guard,(ROOT/'results'/f'{condition}.jsonl').open('x') as journal:
            def call(messages,cap,meta):
                save(ROOT/'results'/f'{condition}.inflight.json',dict(meta,at=time.time()))
                prompt=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
                encoded=tokenizer(prompt,return_tensors='pt',add_special_tokens=False).to(model.device)
                width=encoded['input_ids'].shape[1];assert width<=plan['max_prompt_tokens']
                started=time.time()
                with torch.inference_mode():gen=model.generate(**encoded,max_new_tokens=cap,do_sample=False,pad_token_id=tokenizer.eos_token_id,eos_token_id=tokenizer.eos_token_id)
                tokens=gen[0,width:].tolist();ended=tokenizer.eos_token_id in tokens
                if ended:tokens=tokens[:tokens.index(tokenizer.eos_token_id)+1]
                raw=tokenizer.decode(tokens,skip_special_tokens=True).strip()
                row=dict(meta,condition=condition,messages=messages,raw=raw,ended=ended,
                    input_tokens=width,output_tokens=len(tokens),latency_s=time.time()-started)
                journal.write(json.dumps(row,ensure_ascii=False)+'\n');journal.flush();os.fsync(journal.fileno())
                save(ROOT/'results'/f'{condition}.inflight.json',dict(meta,status='recorded'))
                return row
            controls=[]
            for i in range(8):
                gold={k:bool((i>>j)&1) for j,k in enumerate(FIELDS)}
                messages=[{'role':'system','content':'Copy the supplied JSON object exactly. No markdown or additional text.'},{'role':'user','content':json.dumps(gold)}]
                r=call(messages,128,{'phase':'control','id':str(i)});value=decode(r['raw'],r['ended'])
                controls.append({'correct':value==gold,'valid':value is not None})
            if sum(r['correct'] for r in controls)<7 or any(not r['valid'] for r in controls):
                save(ROOT/'results'/f'{condition}.receipt.json',{'status':'aborted-controls','controls':controls,'episodes':0,'governance_evidence':False});continue
            for arm in plan['arms']:
                for case in cases:
                    base=[{'role':'system','content':SENDER_SYSTEM+'\n'+GUIDES[arm]},
                        {'role':'user','content':case['common']+'\nCommunicate this intended plan, in '+('Ainglish' if arm=='ainglish' else 'explicit ordinary English')+':\n'+json.dumps(case['semantic_brief'])}]
                    meta={'phase':'target','episode':case['id'],'arm':arm}
                    sender=call(base,192,dict(meta,stage='sender'))
                    receiver=[{'role':'system','content':RECEIVER_SYSTEM+'\n'+GUIDES[arm]},
                        {'role':'user','content':case['common']+'\nSender instruction:\n'+sender['raw']}]
                    first=call(receiver,128,dict(meta,stage='receiver'))
                    clarification=base+[{'role':'assistant','content':sender['raw']},{'role':'user','content':'The receiver proposed this interpretation:\n'+first['raw']+'\nRestate all five choices explicitly once, correcting any mismatch with your intended plan. This clarification is required even if the first interpretation was correct.'}]
                    repair=call(clarification,192,dict(meta,stage='clarification'))
                    final=receiver+[{'role':'assistant','content':first['raw']},{'role':'user','content':'The sender clarifies:\n'+repair['raw']+'\nReturn the complete revised five-field plan.'}]
                    call(final,128,dict(meta,stage='receiver-final'))
                print(condition,arm,'32 episodes recorded',flush=True)
            save(ROOT/'results'/f'{condition}.receipt.json',dict(provenance,status='complete',controls=controls,episodes=64,governance_evidence=False,
                guide_tokens={k:len(tokenizer.encode(v,add_special_tokens=False)) for k,v in GUIDES.items()}))
    save(ROOT/'results/finished.json',{'at':time.time(),'governance_evidence':False})


if __name__=='__main__':main()
