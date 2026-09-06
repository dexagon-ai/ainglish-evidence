"""Rescore frozen outputs and report every predeclared endpoint; no inference."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parent
CONDITIONS = ['base', 'ainglish', 'english', 'prior-ainglish', 'prior-english']
SEED = 2026090613


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def score(records):
    n = len(records)
    labels = Counter(r['answer'] for r in records)
    meanings = Counter(r['semantic_gold'] for r in records)
    return dict(n=n, correct=sum(r['correct'] for r in records), accuracy_pct=100*sum(r['correct'] for r in records)/n,
                invalid=sum(not r['valid'] for r in records), frames=len({r['frame'] for r in records}),
                answer_counts=dict(labels), semantic_gold_counts=dict(meanings),
                constant_label_pct=100*max(labels.values())/n, constant_semantic_text_pct=100*max(meanings.values())/n,
                input_tokens=sum(r['input_tokens'] for r in records), output_tokens=sum(r['output_tokens'] for r in records))


def pair(left, right):
    l = {r['case_id']: r for r in left}; r = {r['case_id']: r for r in right}
    assert len(l) == len(left) and len(r) == len(right) and l.keys() == r.keys()
    clusters = defaultdict(list); gained=[]; lost=[]; semantic_changed=[]
    for key in l:
        assert l[key]['frame'] == r[key]['frame']
        delta = int(l[key]['correct']) - int(r[key]['correct'])
        clusters[l[key]['frame']].append(delta)
        if delta > 0: gained.append(key)
        if delta < 0: lost.append(key)
        if l[key].get('decoded') != r[key].get('decoded'): semantic_changed.append(key)
    rng = random.Random(SEED); keys = sorted(clusters); samples=[]
    for _ in range(2000):
        values = [v for key in rng.choices(keys, k=len(keys)) for v in clusters[key]]
        samples.append(100*sum(values)/len(values))
    samples.sort()
    return dict(n=len(l), frames=len(keys), delta_pp=100*(len(gained)-len(lost))/len(l),
                frame_cluster_95_pct=[samples[49], samples[1949]], gained=gained, lost=lost,
                unchanged_correctness=len(l)-len(gained)-len(lost), changed_decoded_meaning=semantic_changed)


def select(records, study, arm, family=None):
    return [r for r in records if r['study']==study and r['arm']==arm and (family is None or r['family']==family)]


def main():
    frozen=json.loads((ROOT/'FROZEN.json').read_text())
    for name, expected in frozen.items(): assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, name
    tasks=read_rows(ROOT/'research-tasks.jsonl'); task_map={r['id']:r for r in tasks}
    assert len(task_map)==len(tasks)==1572
    journals={}; report={'kind':'ainglish.usefulness-results.v1','seed':SEED,'bootstrap_draws':2000,'conditions':{},'comparisons':{},'governance_evidence':False}
    for condition in CONDITIONS:
        records=read_rows(ROOT/'research-results'/f'{condition}.jsonl')
        controls=[r for r in records if r['phase']=='control']; targets=[r for r in records if r['phase']=='target']
        assert len(controls)==12 and {r['id'] for r in controls}=={f'control/{i}' for i in range(12)}
        for row in controls:
            expected='ABC'[int(row['id'].split('/')[1])%3]
            assert row['raw']==expected and row['valid'] and row['correct'] and not row['truncated']
        expected_tasks=[r for r in tasks if not condition.startswith('prior-') or r['study'] in ['retention','option-permutation']]
        assert len(targets)==len(expected_tasks) and {r['id'] for r in targets}=={r['id'] for r in expected_tasks}
        for row in targets:
            task=task_map[row['id']]
            for field in ['answer','case_id','frame','arm','family','semantic_gold']: assert row[field]==task[field], (row['id'],field)
            correct=row['raw']==task['answer'] and not row['truncated']
            valid=row['raw'] in task['options'] and not row['truncated']
            assert row['condition']==condition and row['correct']==correct and row['valid']==valid
            row['decoded']=task['options'].get(row['raw']) if valid else None
        receipt=json.loads((ROOT/'research-results'/f'{condition}.receipt.json').read_text())
        assert receipt['status']=='complete' and receipt['targets']==len(targets) and receipt['downloads']==0
        journals[condition]=targets
        studies={}
        for study in sorted({r['study'] for r in targets}):
            current=[r for r in targets if r['study']==study]
            studies[study]={'arms':{},'families':{}}
            for arm in sorted({r['arm'] for r in current}): studies[study]['arms'][arm]=score(select(current,study,arm))
            for family in sorted({r['family'] for r in current}):
                studies[study]['families'][family]={arm:score(select(current,study,arm,family)) for arm in sorted({r['arm'] for r in current if r['family']==family})}
        report['conditions'][condition]={'controls_correct':12,'target_cells':len(targets),'raw_sha256':hashlib.sha256((ROOT/'research-results'/f'{condition}.jsonl').read_bytes()).hexdigest(),'studies':studies}
    families=sorted({r['family'] for r in tasks if r['study']=='retention'})
    primary={family or 'overall':pair(select(journals['ainglish'],'retention','ainglish',family),select(journals['english'],'retention','ainglish',family)) for family in [None]+families}
    english_retention={family or 'overall':pair(select(journals['ainglish'],'retention','english',family),select(journals['base'],'retention','english',family)) for family in [None]+families}
    report['primary']={'a_trained_minus_e_trained_cold_a':primary,'a_trained_minus_base_english':english_retention,
                       'all_point_guards_pass':all(r['delta_pp']>=-5 for r in primary.values()) and english_retention['overall']['delta_pp']>=-5,
                       'boundary':'Point guards are descriptive, not confidence-based noninferiority. English family outcomes remain visible.'}
    for condition, records in journals.items():
        contrasts={}
        studies=['retention'] if condition.startswith('prior-') else ['retention','writer','workflow','composition']
        for study in studies:
            fs=sorted({r['family'] for r in records if r['study']==study})
            contrasts[study]={f or 'overall':pair(select(records,study,'ainglish',f),select(records,study,'english',f)) for f in [None]+fs}
        if not condition.startswith('prior-'):
            for exposure in ['cold','reference']:
                for surface in ['ainglish','spaces','labels']:
                    contrasts[f'wording/{surface}-{exposure}-minus-english']={f or 'overall':pair(select(records,'wording',surface+'-'+exposure,f),select(records,'wording','english-'+exposure,f)) for f in [None]+families}
            contrasts['reference_cost']={}
            for surface in ['english','ainglish','spaces','labels']:
                cold={r['case_id']:r for r in select(records,'wording',surface+'-cold')}; ref={r['case_id']:r for r in select(records,'wording',surface+'-reference')}
                costs=[ref[k]['input_tokens']-cold[k]['input_tokens'] for k in cold]
                contrasts['reference_cost'][surface]={'n':len(costs),'extra_input_tokens':sum(costs),'min':min(costs),'max':max(costs),'mean':statistics.mean(costs),'accuracy':pair(list(ref.values()),list(cold.values()))}
            original=select(records,'wording','ainglish-cold','participants'); perm=select(records,'option-permutation','ainglish-cold')
            contrasts['option_permutation']=pair(perm,original)
        else:
            # Original wording was intentionally not rerun for the prior adapters.
            contrasts['option_permutation_boundary']='12 responses retained; no paired original-wording condition in this campaign.'
        report['comparisons'][condition]=contrasts
    report['calls']=sum(len(r)+12 for r in journals.values())
    report['target_cells']=sum(len(r) for r in journals.values())
    report['input_tokens']=sum(r['input_tokens'] for records in journals.values() for r in records)
    report['output_tokens']=sum(r['output_tokens'] for records in journals.values() for r in records)
    old=ROOT.parent/'ratified-learning-pilot-2026-09-06/results'
    a=[r for r in read_rows(old/'ainglish.jsonl') if r['arm']=='ainglish-cold']; e=[r for r in read_rows(old/'english.jsonl') if r['arm']=='ainglish-cold']
    for records in [a,e]:
        for r in records:
            assert r['correct']==(r['raw']==r['expected'] and r['valid'])
            r['case_id']=r['id'];r['decoded']=r['raw']
    report['old_pilot_discordance']={f or 'overall':pair([r for r in a if f is None or r['family']==f],[r for r in e if f is None or r['family']==f]) for f in [None]+families}
    destination=ROOT/'RESEARCH-RESULTS.json'
    with destination.open('x') as h: json.dump(report,h,indent=2,ensure_ascii=False);h.write('\n')
    print(json.dumps({'calls':report['calls'],'primary':{k:{f:round(v['delta_pp'],3) for f,v in r.items()} for k,r in report['primary'].items() if isinstance(r,dict)},'point_guards':report['primary']['all_point_guards_pass'],'old_discordance':{k:len(report['old_pilot_discordance']['overall'][k]) for k in ['gained','lost']}}))


if __name__=='__main__':main()
