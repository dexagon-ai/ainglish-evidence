"""Prospective text-cost rehearsal, not inference or measured task success."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import save_new, verify_freeze, disk_guard

def build():
    sources=json.loads((ROOT.parent/'communication-diagnostics-2026-09-06/source-constructs.json').read_text())['entries']
    keys=['participants','multiplicity','deadline']
    guide='\n\n'.join(sources[k]['english_mapping'] for k in keys)
    common='Noor is speaking to Mira. Noor and Ivo are always in the team; each message states whether Mira joins it. Everyone has permission. All times refer to the same known day in UTC. Each named review is a distinct authorized task.'
    cases=[]
    for noun in ['equipment inventory','exhibit catalogue','draft contract','release notes']:
        turns=[]
        for i in range(128):
            included=bool(i&1);joint=bool(i&2);complete=bool(i&4)
            a=('we-including-you' if included else 'we-excluding-you')+f' will review {noun} item {i+1}, '+('as-one' if joint else 'each-alone')+', '+('complete-by' if complete else 'start-by')+'(18:00 UTC today).'
            team='Noor, Ivo and Mira' if included else 'Noor and Ivo, excluding Mira'
            e=team+(' will jointly perform one review of ' if joint else ' will each perform a separate review of ')+f'{noun} item {i+1}. '+('The review' if joint else 'Every review')+' must '+('successfully finish' if complete else 'start')+' by 18:00 UTC today.'
            turns.append({'ainglish':a,'english':e,'acknowledgement':'Understood: '+e})
        cases.append({'context':noun,'turns':turns})
    plan={'kind':'ainglish.definition-amortisation.v1','depths':[1,2,4,8,16,32,64,128],
        'models':['cl100k_base','o200k_base','p50k_base'],'policies':['once','each_turn'],
        'common':common,'ainglish_reference':guide,'contexts':4,
        'estimand':'Serialized conversation TEXT token volume, and sum of serialized input histories plus authored replies across calls. No provider chat-template or billing claim.',
        'incumbency':'Primary scenario assumes ordinary English is known and Ainglish must be taught with the three full registered definitions. This asymmetric startup cost is explicit, not a matched training comparison.',
        'acknowledgements':'Authored complete English confirmations are identical across language arms. No model produced or validated these conversations.',
        'once':'Full Ainglish guide once at conversation start; history is still retransmitted at each stateless request.',
        'each_turn':'Full Ainglish guide in each user turn; all prior copies remain in the transmitted history.',
        'unmodelled':['Provider framing, cache discounts, retries, truncation policy, actual comprehension, future tokenizer vocabulary changes.'],
        'limits':['Four authored noun contexts and cycled choice patterns, not independent task samples.',
            'A byte/token break-even cannot establish understanding or successful operations.',
            'Large histories may exceed an actual model context limit. Counts do not claim those histories were executed.',
            'Training weights cannot change segmentation under these fixed tokenizers.'],
        'governance_evidence':False,'inference_calls':0}
    save_new(ROOT/'cases.json',cases);save_new(ROOT/'PLAN.json',plan)
    names=['study.py','cases.json','PLAN.json','../communication-diagnostics-2026-09-06/source-constructs.json','../overnight-runtime-2026-09-06/runtime.py']
    save_new(ROOT/'FROZEN.json',{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})

def run():
    commit=verify_freeze(ROOT);disk_guard()
    import tiktoken
    plan=json.loads((ROOT/'PLAN.json').read_text());cases=json.loads((ROOT/'cases.json').read_text());rows=[]
    for name in plan['models']:
        encoder=tiktoken.get_encoding(name)
        def count(messages):return len(encoder.encode(json.dumps(messages,ensure_ascii=False,separators=(',',':'))))
        for policy in plan['policies']:
            for case in cases:
                for arm in ['ainglish','english']:
                    guide=plan['ainglish_reference'] if arm=='ainglish' else ''
                    messages=[{'role':'system','content':plan['common']+(('\n'+guide) if policy=='once' and guide else '')}]
                    transmitted=0;input_total=0;reply_total=0
                    for i,turn in enumerate(case['turns'],1):
                        content=((guide+'\n') if policy=='each_turn' and guide else '')+turn[arm]
                        messages.append({'role':'user','content':content})
                        inp=count(messages);out=len(encoder.encode(turn['acknowledgement']))
                        input_total+=inp;reply_total+=out
                        messages.append({'role':'assistant','content':turn['acknowledgement']})
                        if i in plan['depths']:
                            rows.append({'tokenizer':name,'policy':policy,'context':case['context'],'arm':arm,'turns':i,
                                'unique_transcript_tokens':count(messages),'retransmitted_input_tokens':input_total,
                                'authored_reply_tokens':reply_total,'total_replayed_tokens':input_total+reply_total,'largest_input_tokens':inp})
        print(name,'counted without inference',flush=True)
    summary=[]
    for name in plan['models']:
        for policy in plan['policies']:
            for n in plan['depths']:
                group=[r for r in rows if r['tokenizer']==name and r['policy']==policy and r['turns']==n]
                a=[r for r in group if r['arm']=='ainglish'];e=[r for r in group if r['arm']=='english']
                summary.append({'tokenizer':name,'policy':policy,'turns':n,
                    **{key+'_a_minus_e':sum(r[key] for r in a)/4-sum(r[key] for r in e)/4 for key in ['unique_transcript_tokens','total_replayed_tokens']},
                    'largest_ainglish_input':max(r['largest_input_tokens'] for r in a)})
    save_new(ROOT/'RESULTS.json',{'freeze':commit,'rows':rows,'summaries':summary,'inference_calls':0,'limits':plan['limits']})
    text=['# Definition startup cost across authored conversations','','No inference was run. Positive numbers mean MORE Ainglish text tokens. Replayed totals count every full request history plus its authored reply, not provider billing.','',
        '| Tokenizer | Guide policy | Turns | Transcript delta | Replayed-total delta | Largest Ainglish input |','|---|---|---:|---:|---:|---:|']
    for r in summary:text.append(f"| {r['tokenizer']} | {r['policy']} | {r['turns']} | {r['unique_transcript_tokens_a_minus_e']:.2f} | {r['total_replayed_tokens_a_minus_e']:.2f} | {r['largest_ainglish_input']} |")
    text+=['','English is assumed known; Ainglish is taught with complete definitions. This is the current-incumbency scenario, not a causal training comparison. Cache discounts and actual model context limits are not simulated. No break-even proves comprehension or future efficiency.']
    with (ROOT/'RESULTS.md').open('x') as out:out.write('\n'.join(text)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);a=p.parse_args()
    build() if a.action=='build' else run()
