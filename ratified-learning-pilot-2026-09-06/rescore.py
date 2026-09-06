#!/usr/bin/env python3
"""Inference-free re-score against frozen answers, including the pre-noted label strata."""
import collections
import json
from pathlib import Path
from audit import ROOT, digest, rows, verify
from build import dump


def main():
    freeze=verify(public=True)
    tasks={r['id']:r for r in rows('evaluation.jsonl')}
    report={'freeze_commit':freeze,'inference_calls':0,'conditions':{},'test_majority_label_baseline':0.5}
    comparison={}
    token_counts={}
    for condition in ('base','ainglish','english'):
        journal=ROOT/'results'/f'{condition}.jsonl'
        records=[json.loads(x) for x in journal.read_text().splitlines()]
        assert len(records)==396
        assert len({r['id'] for r in records})==396
        cells={};labels={};counts=collections.Counter()
        for r in records:
            if r['phase']=='controls':
                gold='ABC'[int(r['id'].split('/')[-1])%3]
            else:
                case_id=r['id'].rsplit('/',1)[0]
                task=tasks[case_id]
                gold=task['answer']
                assert r['frame']==task['frame'] and r['family']==task['family']
                assert r['boundary_case']==task['boundary_case']
                assert r['arm']==r['id'].rsplit('/',1)[-1]
                cells[r['id']]=r['raw']==gold
                label=labels.setdefault(r['arm'],{}).setdefault(gold,{'n':0,'correct':0})
                label['n']+=1;label['correct']+=r['raw']==gold
                counts[r['arm']]+=1
                token_counts.setdefault(r['id'],set()).add(r['input_tokens'])
            assert r['expected']==gold
            assert r['correct']==(r['raw']==gold)
            assert r['valid']==(r['raw'] in 'ABC' and len(r['raw'])==1)
        assert set(counts.values())=={96} and len(counts)==4
        report['conditions'][condition]={'journal_sha256':digest(journal),'records':len(records),'per_label':labels,'raw_rescore':'pass'}
        comparison[condition]=cells
    assert all(len(v)==1 for v in token_counts.values()),'Fixed input token counts changed between weight conditions'
    changes=collections.defaultdict(lambda:collections.Counter())
    for ident,trained in comparison['ainglish'].items():
        if not ident.endswith('/ainglish-cold'): continue
        control=comparison['english'][ident]; family=tasks[ident.rsplit('/',1)[0]]['family']
        key='gained' if trained and not control else 'lost' if control and not trained else 'same'
        changes[family][key]+=1
    report['ainglish_training_versus_english_training_on_cold_ainglish']={k:dict(v) for k,v in changes.items()}
    report['fixed_prompt_token_counts_across_weights']='pass'
    dump(ROOT/'RESCORE.json',report)
    print(json.dumps({'rescore':'1188 raw answers verified','token_invariance':'pass','paired_changes':report['ainglish_training_versus_english_training_on_cold_ainglish']},indent=2))


if __name__=='__main__':main()
