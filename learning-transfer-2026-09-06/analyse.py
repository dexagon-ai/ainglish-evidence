"""Prospectively pinned analysis: every seed and family, honest frame-level intervals."""
from collections import defaultdict
import json
import random
from statistics import mean
from audit import ROOT,audit,rows

def accuracy(records):return 100*mean(r['correct'] for r in records) if records else None
def contrast(left,right):
    l={r['id']:r for r in left};r={r['id']:r for r in right};assert l.keys()==r.keys() and l
    frames=defaultdict(list)
    for k,v in l.items():frames[v['frame']].append(100*(int(v['correct'])-int(r[k]['correct'])))
    population=[mean(v) for v in frames.values()];rng=random.Random(2026090633)
    draws=sorted(mean(rng.choices(population,k=len(population))) for _ in range(2000))
    return {'delta_pp':mean(population),'frame_bootstrap_95':[draws[49],draws[1949]],'frames':len(frames),'cases':len(l)}

def main():
    audit();plan=json.loads((ROOT/'PLAN.json').read_text());data={};summaries={}
    tasks={r['id']:r for r in rows('tasks.jsonl')}
    for condition in plan['conditions']:
        receipt=json.loads((ROOT/'results'/f'{condition}.receipt.json').read_text())
        allrows=rows('results/'+condition+'.jsonl');records=[r for r in allrows if r['phase']=='target'];data[condition]=records
        assert len(records)==receipt['targets']
        buckets=defaultdict(list)
        for r in records:buckets[(r['study'],r['family'],r['arm'])].append(r)
        summaries[condition]={'status':receipt['status'],'targets':len(records),'invalid':sum(not r['valid'] for r in records),
            'input_tokens':sum(r['input_tokens'] for r in allrows),'output_tokens':sum(r['output_tokens'] for r in allrows),
            'groups':[{'study':k[0],'family':k[1],'arm':k[2],'n':len(v),'accuracy':accuracy(v)} for k,v in buckets.items()]}
        composition=[]
        for family in ['participants+deadline','multiplicity+alternatives']:
            for arm in ['ainglish','english']:
                group=[r for r in records if r['study']=='composition' and r['family']==family and r['arm']==arm]
                if not group:continue
                axes=[[],[]]
                for r in group:
                    expected=r['semantic_gold'].split('; ')
                    observed=tasks[r['id']]['options'].get(r['raw'],'; ').split('; ') if r['valid'] else ['','']
                    for i in range(2):axes[i].append(int(len(observed)==2 and observed[i]==expected[i]))
                composition.append({'family':family,'arm':arm,'joint_accuracy':accuracy(group),'first_axis_accuracy':100*mean(axes[0]),'second_axis_accuracy':100*mean(axes[1])})
        summaries[condition]['composition']=composition
    contrasts=[]
    families=sorted({r['family'] for r in rows('novel-reasoning.jsonl')})
    def select(condition,arm,family):return [r for r in data[condition] if r['study']=='retention' and r['arm']==arm and (family=='overall' or r['family']==family)]
    for seed in plan['seeds']:
        for family in ['overall',*families]:
            for kind,left,right,arm in [('matched_training',f'ainglish-{seed}',f'english-{seed}','ainglish'),('english_retention',f'ainglish-{seed}','base','english')]:
                a,b=select(left,arm,family),select(right,arm,family)
                contrasts.append({'seed':seed,'family':family,'kind':kind,**(contrast(a,b) if a and b else {'status':'missing-condition'})})
    result={'kind':'ainglish.multi-seed-reasoning-transfer-results.v1','governance_evidence':False,'conditions':summaries,'contrasts':contrasts,
        'limits':['One base model, three training seeds, six ratified families, synthetic authored frames.','Frame bootstrap describes this held-out frame collection, not all language or human understanding.','Every seed and family is retained. English incumbent exposure differs; a future learning hypothesis does not nullify current costs or harm.','A -5pp point screen is not statistical proof of non-inferiority.']}
    (ROOT/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Multi-seed reasoning transfer —6 September2026','','Research only; no proposal ratification or settlement follows.','','|Seed|Contrast|Family|Delta pp|Frame interval|','|---|---|---|---:|---|']
    for r in contrasts:
        if 'delta_pp' in r:lines.append(f"|{r['seed']}|{r['kind']}|{r['family']}|{r['delta_pp']:.2f}|{r['frame_bootstrap_95']}|")
    lines+=['','## Limits','',*['- '+s for s in result['limits']]]
    (ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'targets':sum(r['targets'] for r in summaries.values()),'overall':[r for r in contrasts if r['family']=='overall'],'failed_family_point_guards':[r for r in contrasts if r['family']!='overall' and r.get('delta_pp',0)<-5]},indent=2))

if __name__=='__main__':main()
