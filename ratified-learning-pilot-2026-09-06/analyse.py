#!/usr/bin/env python3
"""Describe every frozen cell; paired exploratory intervals cluster by topic/family."""
import json
import random
from collections import defaultdict
from audit import ROOT, rows
from build import dump


def summarize(records):
    return {'n':len(records),'correct':sum(r['correct'] for r in records),
            'valid':sum(r['valid'] for r in records),
            'accuracy':sum(r['correct'] for r in records)/len(records) if records else None,
            'input_tokens':sum(r['input_tokens'] for r in records),
            'output_tokens':sum(r['output_tokens'] for r in records)}


def main():
    report={'kind':'ainglish.ratified-learning-pilot-result.v1','governance_evidence':False,'conditions':{}}
    indexed={}
    for condition in ('base','ainglish','english'):
        path=ROOT/'results'/f'{condition}.jsonl'
        if not path.exists():
            report['conditions'][condition]={'status':'no-result'};continue
        records=[json.loads(x) for x in path.read_text().splitlines()]
        targets=[r for r in records if r['phase']=='target']
        assert len({r['id'] for r in records})==len(records),'Duplicate observation'
        receipt=ROOT/'results'/f'{condition}.receipt.json'
        status=json.loads(receipt.read_text())['status'] if receipt.exists() else 'incomplete-or-aborted'
        report['conditions'][condition]={'status':status,'controls':summarize([r for r in records if r['phase']=='controls']),
            'arms':{arm:summarize([r for r in targets if r['arm']==arm]) for arm in ('ainglish-cold','ainglish-reference','english-cold','english-reference')},
            'families':{family:{arm:summarize([r for r in targets if r['family']==family and r['arm']==arm])
                               for arm in ('ainglish-cold','ainglish-reference','english-cold','english-reference')} for family in sorted({r['family'] for r in targets})},
            'boundary':{arm:summarize([r for r in targets if r['arm']==arm and r['boundary_case']]) for arm in ('ainglish-cold','english-cold')}}
        if status=='complete':
            expected={r['id']+'/'+a for r in rows('evaluation.jsonl') for a in ('ainglish-cold','ainglish-reference','english-cold','english-reference')}
            assert {r['id'] for r in targets}==expected,'Incomplete target denominator'
            indexed[condition]={r['id']:r for r in targets}
    if all(k in indexed for k in ('ainglish','english')):
        values=[];clusters=defaultdict(list)
        for case in rows('evaluation.jsonl'):
            base=case['id']
            delta_a=int(indexed['ainglish'][base+'/ainglish-cold']['correct'])-int(indexed['english'][base+'/ainglish-cold']['correct'])
            delta_e=int(indexed['ainglish'][base+'/english-cold']['correct'])-int(indexed['english'][base+'/english-cold']['correct'])
            value={'frame':case['frame'],'ainglish_delta':delta_a,'english_delta':delta_e,'difference_in_differences':delta_a-delta_e}
            values.append(value);clusters[case['frame']].append(value)
        primary={}
        for key in ('ainglish_delta','english_delta','difference_in_differences'):
            rng=random.Random(2026090602);boot=[];keys=sorted(clusters)
            for _ in range(2000):
                sampled=[r for cluster in rng.choices(keys,k=len(keys)) for r in clusters[cluster]]
                boot.append(100*sum(r[key] for r in sampled)/len(sampled))
            boot.sort()
            primary[key]={'percentage_points':100*sum(r[key] for r in values)/len(values),'exploratory_cluster_ci95':[boot[49],boot[1949]],'clusters':len(clusters)}
        a=report['conditions']['ainglish'];e=report['conditions']['english']
        boundary_delta=100*(a['boundary']['ainglish-cold']['accuracy']-e['boundary']['ainglish-cold']['accuracy'])
        guard=primary['english_delta']['percentage_points']>=-5 and boundary_delta>=-5
        primary['boundary_delta_pp']=boundary_delta
        primary['nonregression_guard_passed']=guard
        primary['interpretation']='selective-development-signal' if guard and primary['ainglish_delta']['percentage_points']>0 and primary['difference_in_differences']['percentage_points']>0 else 'no-selective-benefit-established'
        report['primary']=primary
    else: report['primary']={'interpretation':'paired-trained-comparison-unavailable'}
    report['limits']=['One cached model, one seed, small synthetic task families.',
        'Held-out framings and names, not held-out concepts or independent human tasks.',
        'Closed answer selection, not execution of real work. Token counts cover one reading turn only.',
        'No tokenizer change, no external-lab training receipt, no governance progression claim.']
    dump(ROOT/'RESULT.json',report)
    print(json.dumps(report.get('primary'),indent=2))


if __name__=='__main__':main()
