"""Bounded completion/report publication for the already-running frozen CPU study.

Never call a model, resume inference, change a gate, kill a process or touch another
agent's service. Publish only generated research artifacts in the user's own repo.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
SOURCE=REPO/'mistral-context-transfer-2026-09-07'
CONTINUATION=REPO/'mistral-context-continuation-2026-09-07'
DEST=Path('/home/dexagon/codex/worktrees/evidence-mistral-finish-20260907')
BRANCH='dexagon/mistral-finish-20260907'
sys.path.insert(0,str(REPO/'overnight-runtime-2026-09-06'))
from runtime import Journal,save_new,verify_freeze,disk_guard

def table(rows, fields):
    groups=defaultdict(list)
    for row in rows:
        groups[row['id'].split('/')[0],row['arm']].append(row)
    return [{'context':context,'arm':arm,'n':len(values),
        **{field:{'true':sum(r.get(field) is True for r in values),
                  'false':sum(r.get(field) is False for r in values),
                  'missing':sum(r.get(field) not in [True,False] for r in values)} for field in fields}}
        for (context,arm),values in sorted(groups.items())]

def process_matches(pid):
    path=Path('/proc')/str(pid)/'cmdline'
    if not path.exists():return False
    args=path.read_bytes().split(b'\0')
    return any(a.endswith(b'mistral-context-continuation-2026-09-07/resume.py') for a in args) and b'run' in args

def analyse():
    original=verify_freeze(SOURCE);continuation=verify_freeze(CONTINUATION)
    events=Journal._validate((SOURCE/'execution/calls.jsonl').read_text())
    begin=[e['data'] for e in events if e['kind']=='begin'];end=[e['data'] for e in events if e['kind']=='end']
    begins={r['call_id']:r for r in begin};ends={r['call_id']:r for r in end}
    assert len(begins)==len(begin) and len(ends)==len(end)
    assert ends.keys()<=begins.keys()
    for key,row in ends.items():assert row['request_hash']==begins[key]['request_hash']
    pending=sorted(begins.keys()-ends.keys())
    path=SOURCE/'RESULTS.json'
    result=json.loads(path.read_text()) if path.exists() else None
    summary={'kind':'ainglish.mistral-completion-audit.v1','original_freeze':original,
        'continuation_freeze':continuation,'completed_at_audit':datetime.now(timezone.utc).isoformat(),
        'begun_calls':len(begin),'completed_calls':len(end),'uncertain_call_ids':pending,
        'inference_calls_by_this_finisher':0,'governance_evidence':False,
        'status':'completed' if result is not None else 'stopped_without_final_result',
        'reference_by_context':[],'handoff_by_context':[],
        'limits':['This is a same-author readback/reproducibility audit, not an independent replication.',
            'Original CPU reader, options, controls, inputs and gates are unchanged; completed calls were not repeated.',
            'Counts describe three authored contexts, not broad operational efficacy or future Ainglish-trained performance.',
            'Ollama token counts are observed counters, not token IDs or provider billing.'],
        'observed_cost':{'prompt_tokens':sum(r['response'].get('prompt_eval_count',0) for r in end),
            'generated_tokens':sum(r['response'].get('eval_count',0) for r in end),
            'latency_seconds_sum':sum(r['latency_s'] for r in end)}}
    if result is not None:
        assert not pending and len(result['references'])==192
        assert result['freeze']==original and result['continuation_freeze']==continuation
        spec=importlib.util.spec_from_file_location('unchanged_study_for_audit',SOURCE/'study.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        targets={r['id']:r for r in json.loads((SOURCE/'cases.json').read_text())}
        expected_references={(key,arm) for key in targets for arm in ['ainglish','english']}
        assert {(r['id'],r['arm']) for r in result['references']}==expected_references
        for key,row in begins.items():
            assert row['request']['model']==m.MODEL and row['request']['options']==m.OPTIONS
        for row in result['references']:
            cell=ends['reference/'+row['id']+'/'+row['arm']]
            stopped=cell['response'].get('done') is True and cell['response'].get('done_reason')=='stop'
            parsed=m.decode(cell['raw'],targets[row['id']]['brief'])
            assert row['correct']==(stopped and parsed==targets[row['id']]['brief'])
            assert row['parsed']==(parsed is not None) and row['truncated']==(not stopped)
        gate=all(sum(r['correct'] for r in result['references'] if r['arm']==arm)>=.8*96
            and not any(r['truncated'] for r in result['references'] if r['arm']==arm) for arm in ['ainglish','english'])
        assert gate==result['reference_gate']
        expected_handoffs=192 if gate and result['qualification']['writer']['passed'] else 0
        assert len(result['handoffs'])==expected_handoffs
        assert len(end)==32+192+2*expected_handoffs
        if expected_handoffs:
            assert {(r['id'],r['arm']) for r in result['handoffs']}==expected_references
        handoffs=[]
        for row in result['handoffs']:
            sender=ends['sender/'+row['id']+'/'+row['arm']]
            receiver=ends['handoff/'+row['id']+'/'+row['arm']]
            intended=targets[row['id']]['brief'];sent=m.parse_writer(sender['raw'],row['arm']);got=m.decode(receiver['raw'],intended)
            sender_stopped=sender['response'].get('done') is True and sender['response'].get('done_reason')=='stop'
            receiver_stopped=receiver['response'].get('done') is True and receiver['response'].get('done_reason')=='stop'
            assert row['sender_correct']==(sender_stopped and sent==intended)
            assert row['receiver_correct']==(receiver_stopped and got==intended)
            assert row['receiver_tracks_sender']==(None if sent is None else receiver_stopped and got==sent)
            execution=row['execution'] or {}
            handoffs.append({**row,'task_success':execution.get('task_success'),
                             'follows_intended_plan':execution.get('follows_intended_plan')})
        summary.update(reference_gate=gate,qualification={k:v['passed'] for k,v in result['qualification'].items()},
            reference_by_context=table(result['references'],['correct','parsed','truncated']),
            handoff_by_context=table(handoffs,['sender_correct','receiver_correct','receiver_tracks_sender','task_success','follows_intended_plan']))
    else:
        summary['limits'].append('No final result exists. Only completion/uncertainty counts are reported; no partial target-accuracy headline is selected. The finisher does not infer the stopping cause or retry an uncertain call.')
    save_new(ROOT/'execution/ANALYSIS.json',summary)
    lines=['# Mistral contextual transfer: completion readback','',
        'Status: '+summary['status']+'.', '',
        f"{len(end)} completed model calls; {len(pending)} uncertain calls retained. The finisher made zero inference calls.", '',
        'The run uses the original pinned CPU-only Mistral reader and fixed settings. The continuation reuses only exact completed responses locally and spends only previously unstarted calls. This is one interrupted-and-continued study, not a new independent replication.', '']
    if result is not None:
        lines += [f"Neutral gates: {summary['qualification']}. Full reference gate: {gate}. Executed handoff pairs: {len(result['handoffs'])}.", '',
            '| Context | Arm | Joint reference correct | Parsed | Truncated |', '|---|---|---:|---:|---:|']
        for r in summary['reference_by_context']:
            lines.append(f"|{r['context']}|{r['arm']}|{r['correct']['true']}/{r['n']}|{r['parsed']['true']}/{r['n']}|{r['truncated']['true']}/{r['n']}|")
        if result['handoffs']:
            lines += ['', '| Context | Arm | Correct sender | Correct receiver | Tracks actual sender | Successful task | Follows intended plan |', '|---|---|---:|---:|---:|---:|---:|']
            for r in summary['handoff_by_context']:
                counts=[f"{r[k]['true']}/{r['n']}" for k in ['sender_correct','receiver_correct','receiver_tracks_sender','task_success','follows_intended_plan']]
                lines.append('|'+r['context']+'|'+r['arm']+'|'+'|'.join(counts)+'|')
            lines += ['', 'The full denominator is retained, including missing execution/meaning rows. Missing versus false is separate in ANALYSIS.json. Actual sender meaning and intended meaning are not interchangeable. Executor success uses the original fixed simulator and bounded disposable files, not a claim about real-time deadline compliance.']
    lines += ['', '## Boundaries','']+['- '+text for text in summary['limits']]
    with (ROOT/'execution/RESULTS.md').open('x') as out:out.write('\n'.join(lines)+'\n')
    return summary

def publish():
    disk_guard()
    remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=REPO,text=True).strip()
    assert remote=='https://github.com/dexagon-ai/ainglish-evidence.git'
    assert not DEST.exists(),'Dedicated publication checkout already exists; do not overwrite'
    subprocess.run(['git','fetch','origin','main'],cwd=REPO,check=True)
    subprocess.run(['git','worktree','add','-b',BRANCH,str(DEST),'origin/main'],cwd=REPO,check=True)
    files=[SOURCE/'execution'/n for n in ['intent.json','calls.jsonl','qualification.json','reference-gate.json']]
    files += [SOURCE/'RESULTS.json',CONTINUATION/'execution/intent.json',ROOT/'execution/ANALYSIS.json',ROOT/'execution/RESULTS.md']
    copied=[]
    for source in files:
        if not source.exists():continue
        relative=source.relative_to(REPO);target=DEST/relative
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);copied.append(str(relative))
    subprocess.run(['git','add','--',*copied],cwd=DEST,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=DEST,check=True)
    subprocess.run(['git','commit','-m','Publish frozen Mistral continuation outcome and complete call audit'],cwd=DEST,check=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=DEST,text=True).strip()
    # Fast-forward only. A concurrent remote update fails safely; no force or rebase.
    subprocess.run(['git','push','origin','HEAD:main'],cwd=DEST,check=True)
    save_new(ROOT/'execution/publication.json',{'commit':commit,'published':True,'worktree':str(DEST)})
    print('Published complete retained outcome',commit,flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);args=parser.parse_args()
    verify_freeze(ROOT);save_new(ROOT/'execution/intent.json',{'pid':args.pid,'maximum_wait_hours':24,'inference_calls':0})
    deadline=time.monotonic()+24*3600
    while process_matches(args.pid):
        if time.monotonic()>deadline:raise RuntimeError('Bounded wait expired; study untouched and no outcome invented')
        time.sleep(30)
    summary=analyse();print(json.dumps(summary),flush=True);publish()

if __name__=='__main__':main()
