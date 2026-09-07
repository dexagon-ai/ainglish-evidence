"""Prospective five-character interface; real lookup/history and bounded repair cost."""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import Journal, LocalReader, save_new, verify_freeze
sys.path.insert(0, str(ROOT.parent/'communication-diagnostics-2026-09-06'))
from design import FIELDS, MEANINGS, COMMON, PHRASES, guide, render

SYSTEM = ('Read the CURRENT independent record only; earlier jobs are closed history. '
    'Do not execute any action. Answer the five numbered questions in order with exactly '
    'five consecutive capital characters from Y and N. Y means yes; N means no. '
    'No spaces, commas, quotes, JSON, markdown or explanation.')
CORRECTION = ('Your previous answer did not pass the exact-answer check. Re-read this same '
    'CURRENT record and the supplied reference. Answer the same five questions again. '
    'No answer values are supplied in this feedback.')


def code(bits):
    return ''.join('Y' if value else 'N' for value in bits)


def score(raw, ended, gold):
    text = raw.strip()
    return {'valid': bool(ended and len(text) == 5 and set(text) <= {'Y','N'}),
            'correct': bool(ended and text == gold), 'truncated': not ended}


def current(case, arm):
    return COMMON+'\n'+case['context']+'\nCURRENT message:\n'+case['messages'][arm]+'\n'+\
        '\n'.join(f'{i+1}. {question}' for i,question in enumerate(MEANINGS))


def build():
    contexts = [('kite-festival', 'checking the kite rigging'),
                ('seed-library', 'checking the seed-packet inventory'),
                ('print-workshop', 'checking the printed programme')]
    cases = []
    for ci,(name,action) in enumerate(contexts):
        order = list(product([False,True],repeat=5));random.Random(2026090740+ci).shuffle(order)
        for i,bits in enumerate(order):
            brief = dict(zip(FIELDS,bits))
            cases.append({'id':f'{name}-{8700+ci*100+i}', 'context_id':name, 'turn':i+1,
                'brief':brief, 'gold':code(bits),
                'context':f'CURRENT independent job {name}-{8700+ci*100+i}. You are Mira, coordinating with Noor and Ivo. The named check is {action}. This job has a fresh authorized A/B instruction ledger; labels in previous jobs denote different closed ledgers.',
                'messages':{arm:render(brief,arm) for arm in PHRASES}})
    controls = []
    properties = ['circle','arrow','triangle','star','square']
    patterns = list(product([False,True],repeat=5));random.Random(2026090743).shuffle(patterns)
    for i,bits in enumerate(patterns):
        facts = '\n'.join('The '+name+' is '+('present' if bit else 'absent')+'.' for name,bit in zip(properties,bits))
        questions = '\n'.join(f'{j+1}. Is the {name} present?' for j,name in enumerate(properties))
        controls.append({'id':f'neutral-tile-{9300+i}', 'gold':code(bits),
            'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':f'CURRENT record: inspection tile {9300+i}.\n'+facts+'\n'+questions}]})
    plan = {'kind':'ainglish.dialogue-code-interface.v1','governance_evidence':False,
        'snapshot':'/home/dexagon/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28',
        'reader':'Cached native Qwen2.5-7B, GPU0 NF4 double quantization BF16, greedy, seed20260906; no adapter.',
        'qualification':{'neutral_cases':32,'minimum_exact_correct':28,'require_all_valid':True,'maximum_truncations':0},
        'qualification_boundary':'Checks the prospective response interface, not semantic ability on Ainglish or the task population.',
        'change_reason':'Previous JSON screen scored4/16; raw outputs include broken magnetic keys and a flexible field stuck false. New fixed positional Y/N code and explicitly stated present/absent controls are declared prospectively, not post-hoc repair of those outputs. Both wrapper and controls change, so this does not isolate a causal wrapper effect.',
        'policies':['history-once','lookup-per-turn'],'arms':['ainglish','english'],
        'contexts':[c[0] for c in contexts],'turns_per_context':32,'max_initial_calls':384,
        'max_repair_calls':384,'max_total_calls':800,
        'context_window_tokens':8192,'output_cap':64,'max_prompt_tokens':8128,
        'repair':'At most one gold-oracle-triggered generic correction per wrong/malformed/truncated response, only if the complete prompt fits. No gold bits, no selection of favourable retries.',
        'resource_guards':{'minimum_host_free_gib':15,'minimum_ram_before_load_gib':14,'gpu':'physical0 idle; never evict'},
        'limits':['Three authored scenario frames with32 factorial configurations each, not96 independent contexts or agents.',
            'Both full language guides are visible. This is guided current-model research, not governance evidence, cold reading or a trained future model.',
            'A strictly smaller output surface can improve formatting without improving semantic understanding. First-pass validity and exact correctness remain separate.',
            'history-once retains actual requests and answers; lookup-per-turn reads the physical local dictionary on every turn and discards prior closed jobs.',
            'Stop before an oversized prompt; never silently truncate, summarize, or report unexecuted turns as successful.',
            'Record exact input/generated token IDs, actual dictionary bytes/read latency and all repair costs. No KV-cache discount, provider invoice or human usability claim.',
            'Generic corrective feedback uses a gold oracle; this is not autonomous error detection.',
            'The old4/16 qualification and zero language calls remain unchanged. No model downloads or uncertain-call retries.']}
    for name,value in [('cases.json',cases),('controls.json',controls),('dictionary.json',{a:guide(a) for a in PHRASES}),('PLAN.json',plan)]:
        save_new(ROOT/name,value)
    names = ['study.py','test_study.py','README.md','cases.json','controls.json','dictionary.json','PLAN.json',
        '../overnight-runtime-2026-09-06/runtime.py','../communication-diagnostics-2026-09-06/design.py',
        '../communication-diagnostics-2026-09-06/source-constructs.json']
    save_new(ROOT/'FROZEN.json',{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})


def run():
    commit=verify_freeze(ROOT);plan=json.loads((ROOT/'PLAN.json').read_text())
    available=next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
    if available < 14*1024**3:
        raise RuntimeError('Need14GiB available RAM before allocation; preserve other workloads.')
    reader=LocalReader(plan['snapshot'])
    assert reader.model.config.max_position_embeddings >= plan['context_window_tokens']
    with Journal(ROOT/'execution/calls.jsonl', {'freeze':commit,**plan}) as journal:
        save_new(ROOT/'execution/provenance.json',reader.provenance)
        controls=[]
        for case in json.loads((ROOT/'controls.json').read_text()):
            r=reader.call(journal,case['id'],case['messages'],cap=plan['output_cap'],max_prompt_tokens=plan['max_prompt_tokens'])
            controls.append({'id':case['id'],**score(r['raw'],r['ended'],case['gold'])})
        qualified=sum(r['correct'] for r in controls)>=28 and all(r['valid'] for r in controls)
        save_new(ROOT/'execution/qualification.json',{'qualified':qualified,'controls':controls})
        print('Fresh code-interface qualification',sum(r['correct'] for r in controls),'/32',qualified,flush=True)
        rows=[];stops=[];reads=[]

        def lookup(arm,policy,context,turn):
            started=time.perf_counter();raw=(ROOT/'dictionary.json').read_bytes();text=json.loads(raw)[arm]
            reads.append({'arm':arm,'policy':policy,'context':context,'turn':turn,
                'file_bytes':len(raw),'selected_text_utf8_bytes':len(text.encode()),
                'read_seconds':time.perf_counter()-started,'sha256':hashlib.sha256(raw).hexdigest()})
            return text

        def fits(messages):
            return len(reader.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)) <= plan['max_prompt_tokens']

        cases=json.loads((ROOT/'cases.json').read_text())
        if qualified:
            for context in plan['contexts']:
                for policy in plan['policies']:
                    for arm in plan['arms']:
                        history=[{'role':'system','content':SYSTEM+'\n'+lookup(arm,policy,context,0)}] if policy=='history-once' else None
                        for case in [c for c in cases if c['context_id']==context]:
                            turn=case['turn']
                            prompt=history+[{'role':'user','content':current(case,arm)}] if history is not None else [
                                {'role':'system','content':SYSTEM+'\n'+lookup(arm,policy,context,turn)}, {'role':'user','content':current(case,arm)}]
                            if not fits(prompt):
                                stops.append({'context':context,'policy':policy,'arm':arm,'turn':turn,'reason':'context_limit_before_initial_spend'});break
                            key=f'{context}/{policy}/{arm}/{turn}'
                            result=reader.call(journal,key+'/initial',prompt,cap=plan['output_cap'],max_prompt_tokens=plan['max_prompt_tokens'])
                            scored=score(result['raw'],result['ended'],case['gold'])
                            row={'context':context,'policy':policy,'arm':arm,'turn':turn,'id':case['id'],
                                'first_valid':scored['valid'],'first_correct':scored['correct'],'final_correct':scored['correct'],
                                'repair_called':False,'input_tokens':result['input_tokens'],'output_tokens':result['output_tokens'],
                                'latency_s':result['latency_s'],'truncations':int(scored['truncated'])}
                            prompt=prompt+[{'role':'assistant','content':result['raw']}]
                            if not scored['correct']:
                                repaired=prompt+[{'role':'user','content':CORRECTION}]
                                if fits(repaired):
                                    result=reader.call(journal,key+'/repair',repaired,cap=plan['output_cap'],max_prompt_tokens=plan['max_prompt_tokens'])
                                    row['repair_called']=True;row['final_correct']=score(result['raw'],result['ended'],case['gold'])['correct']
                                    for field in ['input_tokens','output_tokens','latency_s']:row[field]+=result[field]
                                    row['truncations']+=int(not result['ended'])
                                    prompt=repaired+[{'role':'assistant','content':result['raw']}]
                                else:
                                    row['repair_context_blocked']=True
                                    stops.append({'context':context,'policy':policy,'arm':arm,'turn':turn,'reason':'context_limit_before_repair_spend'})
                            rows.append(row)
                            if history is not None:history=prompt
                            print(key,'first',row['first_correct'],'final',row['final_correct'],'tokens',row['input_tokens']+row['output_tokens'],flush=True)
                            if row.get('repair_context_blocked'):break
        summaries=[]
        for context in plan['contexts']:
            groups={(p,a):[r for r in rows if r['context']==context and r['policy']==p and r['arm']==a]
                for p in plan['policies'] for a in plan['arms']}
            minimum=min(map(len,groups.values()))
            for horizon in [1,2,4,8,16,32]:
                if horizon>minimum:continue
                for (policy,arm),group in groups.items():
                    sums={k:sum(r[k] for r in group[:horizon]) for k in ['first_valid','first_correct','final_correct','repair_called','input_tokens','output_tokens','latency_s','truncations']}
                    summaries.append({'context':context,'policy':policy,'arm':arm,'matched_prefix':horizon,**sums,
                        'total_tokens_per_final_correct':(sums['input_tokens']+sums['output_tokens'])/sums['final_correct'] if sums['final_correct'] else None})
        save_new(ROOT/'RESULTS.json',{'freeze':commit,'qualified':qualified,'controls':controls,'rows':rows,
            'stops':stops,'dictionary_reads':reads,'matched_prefix_summaries':summaries,'limits':plan['limits']})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);args=p.parse_args()
    build() if args.action=='build' else run()
