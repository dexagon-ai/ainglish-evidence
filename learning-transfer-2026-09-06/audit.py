"""Freeze integrity, disjointness, gold/key and factorial design checks, no inference."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(name):return [json.loads(s) for s in (ROOT/name).read_text().splitlines() if s]
def verify(public=False):
    frozen=json.loads((ROOT/'FROZEN.json').read_text())
    for name,sha in frozen.items():assert digest(ROOT/name)==sha, name
    rel=ROOT.name+'/FROZEN.json'
    commit=subprocess.check_output(['git','log','-1','--format=%H','--',rel],cwd=ROOT.parent,text=True).strip()
    if public:
        assert commit,'Freeze is not committed'
        subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
        for name in [*frozen,'FROZEN.json']:
            assert subprocess.check_output(['git','show',f'{commit}:{ROOT.name}/{name}'],cwd=ROOT.parent)==(ROOT/name).read_bytes(),name
    return commit
def audit():
    verify();train=rows('curriculum.jsonl');test=rows('novel-reasoning.jsonl');tasks=rows('tasks.jsonl')
    assert len(train)==336 and len(test)==216
    assert len({r['frame'] for r in test})==36
    for collection in [train,test,tasks]:
        assert len({r['id'] for r in collection})==len(collection)
        for r in collection:assert r['options'][r['answer']]==r['semantic_gold']
    for lang in ['ainglish','english']:
        assert not {r[lang] for r in train}&{r[lang] for r in test}
        for family in {r['family'] for r in test}:
            c=Counter(r['answer'] for r in test if r['family']==family)
            assert max(c.values())-min(c.values())<=1,c
    source=json.loads((ROOT/'source-constructs.json').read_text())
    assert len(source['entries'])==6
    assert all(r['kind']!='protocol' for r in source['entries'].values())
    phases=[r for r in tasks if r['study']=='composition' and r['family']=='participants+deadline' and r['arm']=='ainglish']
    assert len(phases)==72 and len({(r['included'],r['finish'],r['timing']) for r in phases})==12
    # The formerly missing diagnostic: start on time, finish late must separate event poles.
    middle=[r for r in phases if r['timing']==1]
    assert all(('missed' in r['semantic_gold'])==r['finish'] for r in middle)
    return {'status':'pass','training_cases':len(train),'reasoning_cases':len(test),'reasoning_frames':36,'tasks_per_condition':len(tasks),'source_families':6,'governance_evidence':False}
if __name__=='__main__':print(json.dumps(audit()))
