"""Full communication costs; first and final plans; never reinterpret malformed outputs."""
from collections import defaultdict
import json
from design import ROOT,FIELDS,save
from run import decode,prose_format


def main():
    plan=json.loads((ROOT/'PLAN.json').read_text());cases={r['id']:r for r in json.loads((ROOT/'cases.json').read_text())};summary={}
    for condition in plan['conditions']:
        receipt=json.loads((ROOT/'results'/f'{condition}.receipt.json').read_text())
        rows=[json.loads(s) for s in (ROOT/'results'/f'{condition}.jsonl').read_text().splitlines()]
        summary[condition]={'status':receipt['status'],'controls':receipt['controls'],'arms':{}}
        groups=defaultdict(dict)
        for r in rows:
            if r['phase']=='target':
                assert r['stage'] not in groups[(r['arm'],r['episode'])]
                groups[(r['arm'],r['episode'])][r['stage']]=r
        for arm in plan['arms']:
            episodes=[]
            for (a,eid),stages in groups.items():
                if a!=arm:continue
                assert set(stages)==set(plan['stages'])
                gold=cases[eid]['brief'];first=decode(stages['receiver']['raw'],stages['receiver']['ended']);final=decode(stages['receiver-final']['raw'],stages['receiver-final']['ended'])
                episodes.append({'id':eid,'first_correct':first==gold,'final_correct':final==gold,'first_valid':first is not None,'final_valid':final is not None,
                    'first_fields':{k:first is not None and first[k]==gold[k] for k in FIELDS},
                    'final_fields':{k:final is not None and final[k]==gold[k] for k in FIELDS},
                    'first_format_adherent_correct':first==gold and prose_format(stages['sender']['raw'],stages['sender']['ended']),
                    'final_format_adherent_correct':final==gold and all(prose_format(stages[s]['raw'],stages[s]['ended']) for s in ['sender','clarification']),
                    'input_tokens':sum(r['input_tokens'] for r in stages.values()),'output_tokens':sum(r['output_tokens'] for r in stages.values()),
                    'truncated_calls':sum(not r['ended'] for r in stages.values())})
            if not episodes:continue
            summary[condition]['arms'][arm]={'episodes':episodes,'n':len(episodes),
                'first_correct':sum(r['first_correct'] for r in episodes),'final_correct':sum(r['final_correct'] for r in episodes),
                'first_format_adherent_correct':sum(r['first_format_adherent_correct'] for r in episodes),
                'final_format_adherent_correct':sum(r['final_format_adherent_correct'] for r in episodes),
                'final_malformed':sum(not r['final_valid'] for r in episodes),'truncated_calls':sum(r['truncated_calls'] for r in episodes),
                'repaired':sum(not r['first_correct'] and r['final_correct'] for r in episodes),'regressed':sum(r['first_correct'] and not r['final_correct'] for r in episodes),
                'input_tokens':sum(r['input_tokens'] for r in episodes),'output_tokens':sum(r['output_tokens'] for r in episodes),
                'guide_tokens':receipt['guide_tokens'][arm],
                'first_field_correct':{k:sum(r['first_fields'][k] for r in episodes) for k in FIELDS},
                'final_field_correct':{k:sum(r['final_fields'][k] for r in episodes) for k in FIELDS}}
    result={'kind':'ainglish.sender-receiver-prose-results.v1','governance_evidence':False,'conditions':summary,'limits':plan['limits']}
    save(ROOT/'RESULTS.json',result)
    lines=['# Sender–receiver prose task','','Synthetic local research, not language-governance evidence. Every episode includes one prescribed clarification; cost includes all four calls.','','|Model condition|Language|First correct|Final correct|Total input tokens|Total output tokens|','|---|---|---:|---:|---:|---:|']
    for k,condition in summary.items():
        if not condition['arms']:lines.append(f'|{k}|Aborted at controls|—|—|—|—|')
        for a,r in condition['arms'].items():lines.append(f"|{k}|{a}|{r['first_correct']}/{r['n']}|{r['final_correct']}/{r['n']}|{r['input_tokens']}|{r['output_tokens']}|")
    lines+=['','## Limits','',*['- '+s for s in plan['limits']]]
    (ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__=='__main__':main()
