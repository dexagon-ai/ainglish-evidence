#!/usr/bin/env python3
"""No-model validation, release pins, semantic oracle checks and the public freeze."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from build import ROOT, SLUGS, messages, row


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name):
    return [json.loads(line) for line in (ROOT/name).read_text().splitlines() if line]


def validate():
    plan = json.loads((ROOT/'PLAN.json').read_text())
    for name, expected in plan['outputs'].items():
        assert digest(ROOT/name) == expected, ('source digest drift', name)
    source = json.loads((ROOT/'source-constructs.json').read_text())
    assert set(source['entries']) == set(SLUGS)
    assert all(x['status'] == 'current' and x['ratified_at'] for x in source['entries'].values())
    train, test = rows('curriculum.jsonl'), rows('evaluation.jsonl')
    assert len(train)==144 and len(test)==96
    assert len({r['id'] for r in train+test})==240
    assert len({r['frame'] for r in test}) == 12
    assert not {r['frame'] for r in train} & {r['frame'] for r in test}
    assert not {r['ainglish'] for r in train} & {r['ainglish'] for r in test}
    assert not {r['english'] for r in train} & {r['english'] for r in test}
    assert all(set(r['options'])==set('ABC') and r['answer'] in r['options'] for r in train+test)
    assert all(len(set(r['options'].values())) == 3 for r in train+test)
    for language in ('ainglish','english'):
        actual = rows(f'train-{language}.jsonl')
        assert len(actual)==len(train)
        for task, encoded in zip(train, actual):
            assert encoded['id']==task['id']
            assert encoded['messages']==messages(task,language+'-cold')+[{'role':'assistant','content':task['answer']}]
    # Independent expected consequences for the boundary/near-miss cases.
    def answer(family, variant):
        case = row(family,'observatory',variant,'test')
        return case['options'][case['answer']]
    assert answer('deadline',0)=='Yes'  # inclusive actual-start deadline
    assert answer('deadline',2)=='No'   # queue entry is not execution
    assert answer('deadline',4)=='Yes'  # exact-time successful completion
    assert answer('deadline',6)=='No'   # failed stop is not completion
    assert answer('participants',2)=='Not determined'
    assert answer('multiplicity',6)=='5'  # simultaneous independent actions
    assert answer('alternatives',2)=='No' # inclusive choice still forbids neither
    assert answer('alternatives',6)=='No' # other prohibitions still bind
    assert answer('unknown',6).startswith('Neither')
    assert answer('unknown',7)=='No' # no authority from a status report
    assert answer('update',2)=='Yes' # reference-local replacement
    assert answer('update',4).startswith('The whole update is invalid')
    assert answer('update',6)=='No' # in-flight effects not cancelled
    return {'status':'pass','train_pairs':144,'test_cases':96,'test_clusters':12,'families':6}


def verify(public=False):
    validate()
    frozen = ROOT/'SHA256SUMS.frozen'
    assert frozen.exists(), 'No freeze'
    paths=[]
    for line in frozen.read_text().splitlines():
        expected,name=line.split('  ',1)
        assert digest(ROOT/name)==expected, ('frozen drift',name)
        paths.append(str((ROOT/name).relative_to(ROOT.parent)))
    paths.append(str(frozen.relative_to(ROOT.parent)))
    for path in paths:
        subprocess.run(['git','ls-files','--error-unmatch',path],cwd=ROOT.parent,check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['git','diff','--exit-code','HEAD','--',*paths],cwd=ROOT.parent,check=True,stdout=subprocess.DEVNULL)
    commit=subprocess.check_output(['git','log','-1','--format=%H','--',str(frozen.relative_to(ROOT.parent))],cwd=ROOT.parent,text=True).strip()
    if public:
        subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
    return commit


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--freeze',action='store_true'); args=parser.parse_args()
    report=validate()
    if args.freeze:
        if (ROOT/'results').exists(): raise SystemExit('Cannot refreeze after exposure')
        files=sorted(p for p in ROOT.iterdir() if p.is_file() and p.name!='SHA256SUMS.frozen')
        (ROOT/'SHA256SUMS.frozen').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in files))
    print(json.dumps(report))
