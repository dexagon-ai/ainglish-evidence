import json
from collections import defaultdict
from design import ROOT,decode_json,decode_message,save

def main():
    plan=json.loads((ROOT/'PLAN.json').read_text());cases=json.loads((ROOT/'cases.json').read_text())
    events=[json.loads(line) for line in (ROOT/'results/base.jsonl').read_text().splitlines()]
    calls={e['data']['call_id']:e['data'] for e in events if e['kind']=='end'}
    rows=[]
    for case in cases:
        for arm in plan['arms']:
            key=case['id']+'/'+arm
            for phase in ['reference','sender','handoff']:
                c=calls.get(phase+'/'+key)
                if c is None:continue
                decoded=decode_message(c['raw'],arm,case['brief']) if phase=='sender' else decode_json(c['raw'],case['brief'])
                sender = calls.get('sender/'+key)
                sent = decode_message(sender['raw'],arm,case['brief']) if sender and sender['ended'] else None
                rows.append({'id':case['id'],'context':case['id'].split('/')[0],'dimensions':case['dimensions'],
                    'phase':phase,'arm':arm,'parsed':decoded is not None,'correct':c['ended'] and decoded==case['brief'],
                    'sender_meaning_known':phase=='handoff' and sent is not None,
                    'matches_sent_meaning':phase=='handoff' and sent is not None and c['ended'] and decoded==sent,
                    'truncated':not c['ended'],'input_tokens':c['input_tokens'],'output_tokens':c['output_tokens']})
    groups=defaultdict(list)
    for row in rows:groups[(row['phase'],row['arm'],row['dimensions'])].append(row)
    summaries=[{'phase':phase,'arm':arm,'dimensions':n,'n':len(group),
        **{k:sum(r[k] for r in group) for k in ['correct','parsed','truncated']},
        'sender_meaning_known':sum(r['sender_meaning_known'] for r in group),
        'matches_sent_meaning':sum(r['matches_sent_meaning'] for r in group),
        'mean_total_tokens':sum(r['input_tokens']+r['output_tokens'] for r in group)/len(group)}
        for (phase,arm,n),group in groups.items()]
    qualification=json.loads((ROOT/'results/qualification.json').read_text())
    gate=qualification['passed'] and len(rows)==plan['target_calls']
    for arm in plan['arms']:
        for phase,metric in [('reference','correct'),('sender','parsed')]:
            found=[s for s in summaries if s['phase']==phase and s['arm']==arm and s['dimensions']==5]
            gate=bool(gate and found and found[0][metric]/found[0]['n']>=0.8)
    contexts=[]
    for context in ['handoff','equipment','community']:
        for arm in plan['arms']:
            selected=[r for r in rows if r['context']==context and r['arm']==arm and r['dimensions']==5 and r['phase']=='reference']
            contexts.append({'context':context,'arm':arm,'n':len(selected),'correct':sum(r['correct'] for r in selected)})
    out={'kind':'ainglish.communication-diagnostic.results.v1','rows':rows,'summaries':summaries,
        'full_reference_by_context':contexts,'communication_training_gate_passed':gate,
        'governance_evidence':False,'complete':len(rows)==plan['target_calls'],'calls_retained':len(calls)}
    save('RESULTS.json',out)
    text=['# Communication diagnostic results','','This is a constrained, reference-assisted interface test, not unrestricted communication or governance evidence.','',
        '| Phase | Arm | Fields | Correct | Parsed | Truncated | Mean input + output tokens |',
        '|---|---|---:|---:|---:|---:|---:|']
    for s in summaries:text.append(f"| {s['phase']} | {s['arm']} | {s['dimensions']} | {s['correct']}/{s['n']} | {s['parsed']}/{s['n']} | {s['truncated']} | {s['mean_total_tokens']:.2f} |")
    text+=['',f'Prospective communication-training gate passed: **{gate}**.',
        'Three authored contexts are reported separately in RESULTS.json. No original failed experiment was rerun or replaced.']
    (ROOT/'RESULTS.md').write_text('\n'.join(text)+'\n')
    print(json.dumps({'training_gate':gate,'summary':summaries},indent=2))

if __name__=='__main__':main()
