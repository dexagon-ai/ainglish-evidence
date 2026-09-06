#!/usr/bin/env python3
"""Post-run exact-case sensitivity; do not replace the frozen primary estimand."""
import json
from audit import ROOT,rows
from build import dump
from clean_teaching_export import cleaned_files


def main():
    report={'post_hoc':True,'inference_calls':0,'primary_unchanged':True,'splits':{},'deduplicated_sensitivity':{}}
    for name in ('curriculum.jsonl','evaluation.jsonl'):
        groups={}
        for r in rows(name):
            signature=json.dumps({k:r[k] for k in ('ainglish','english','question','options','answer')},sort_keys=True)
            groups.setdefault(signature,[]).append(r['id'])
        report['splits'][name]={'rows':len(rows(name)),'distinct_cases':len(groups),'duplicate_groups':[g for g in groups.values() if len(g)>1]}
        if name=='evaluation.jsonl': retained={group[0] for group in groups.values()}
    for condition in ('base','ainglish','english'):
        observed=[json.loads(x) for x in (ROOT/'results'/f'{condition}.jsonl').read_text().splitlines()]
        report['deduplicated_sensitivity'][condition]={}
        for arm in ('ainglish-cold','ainglish-reference','english-cold','english-reference'):
            selected=[r for r in observed if r.get('arm')==arm and r['id'].rsplit('/',1)[0] in retained]
            assert len(selected)==84
            report['deduplicated_sensitivity'][condition][arm]={'n':84,'correct':sum(r['correct'] for r in selected)}
    # Verify the cleaned distribution still excludes evaluation/results and both parallel arms align.
    files=cleaned_files()
    a=[json.loads(x) for x in files['train-ainglish.jsonl'].splitlines()]
    e=[json.loads(x) for x in files['train-english.jsonl'].splitlines()]
    assert [r['id'] for r in a]==[r['id'] for r in e]
    assert all(x['messages'][-1]==y['messages'][-1] for x,y in zip(a,e))
    assert not any('evaluation' in name or 'results' in name for name in files)
    dump(ROOT/'DUPLICATE-AUDIT.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='splits'},indent=2))


if __name__=='__main__':main()
