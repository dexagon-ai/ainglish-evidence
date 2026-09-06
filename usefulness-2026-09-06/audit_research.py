"""Prospective local checks; no reader calls, no register gate."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from ainglish.experiment_audit import audit_items

ROOT=Path(__file__).resolve().parent


def rows(name):return [json.loads(line) for line in (ROOT/name).read_text().splitlines() if line.strip()]
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(public=False):
    pins=json.loads((ROOT/'FROZEN.json').read_text())
    for name,sha in pins.items():assert digest(ROOT/name)==sha, name+' changed after freeze'
    plan=json.loads((ROOT/'PLAN.json').read_text())
    for name,key in [('source-constructs.json','source_mapping_sha256'),('build.py','grammar_sha256'),('run.py','runner_sha256')]:
        assert digest(ROOT.parent/'ratified-learning-pilot-2026-09-06'/name)==plan[key]
    relative=str((ROOT/'FROZEN.json').relative_to(ROOT.parent))
    commit=subprocess.check_output(['git','log','-1','--format=%H','--',relative],cwd=ROOT.parent,text=True).strip()
    if public:
        assert commit
        subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
        for name in [*pins,'FROZEN.json']:
            saved=subprocess.check_output(['git','show',f'{commit}:{ROOT.name}/{name}'],cwd=ROOT.parent)
            assert saved==(ROOT/name).read_bytes(), name+' differs from public freeze'
    return commit


def panel_shape(items):
    result=[]
    for row in items:
        question=row['question']+'\n'+'\n'.join(k+'. '+v for k,v in row['options'].items())
        result.append({'id':row['id'],'english':row['english'],'ainglish':row['ainglish'],'question':question,
                       'options':list(row['options']),'answer':row['answer'],'boundary_case':row['boundary_case'],
                       'settlement_stratum':row['family']})
    return result


def audit():
    train,test=rows('curriculum.jsonl'),rows('retention.jsonl')
    report=audit_items(panel_shape(test),panel_shape(train),require_balanced=True)
    assert report['ok'],report
    tasks=rows('research-tasks.jsonl');assert len({r['id'] for r in tasks})==len(tasks)
    for row in tasks:
        assert row['answer'] in row['options']
        assert row['options'][row['answer']]==row['semantic_gold']
        assert len(set(row['options'].values()))==len(row['options'])
        assert len(row['messages'])==2 and all(isinstance(m['content'],str) for m in row['messages'])
        assert len(row['messages'][1]['content'])<10000
    for family in {r['family'] for r in test}:
        counts=Counter(r['answer'] for r in test if r['family']==family)
        assert max(counts.values())-min(counts.values())<=1
    workflow=[r for r in tasks if r['study']=='workflow']
    for row in workflow:
        expected=(['A and B'] if row['checkpoint']==0 else
                  ['A, B and C' if row['addition'] else 'B and C'] if row['checkpoint']==1 else
                  ['A completed external file is not undone by this instruction update.' if row['completed'] else 'The instruction update does not establish that an in-flight upload stopped or that a file was deleted.'])
        assert row['semantic_gold']==expected[0]
    report['research_tasks']={}
    for study in sorted({r['study'] for r in tasks}):
        group=[r for r in tasks if r['study']==study]
        report['research_tasks'][study]={'cells_per_condition':len(group),'distinct_case_ids':len({r['case_id'] for r in group}),
             'declared_frame_labels':len({r['frame'] for r in group}),'arms':dict(Counter(r['arm'] for r in group)),
             'decoded_answer_counts':dict(Counter(r['answer'] for r in group)),
             'semantic_answer_counts':dict(Counter(r['semantic_gold'] for r in group))}
    report['grammar_overlap']='Training and retention use the same pre-existing eight case grammars per family. Disjoint domain words are not unseen semantic structures.'
    report['sampling']='Authored cases; template/domain repetition is disclosed, not independent population sampling. Workflow has eight structural scenarios expanded to 32 named episodes.'
    return report


if __name__=='__main__':
    report=audit();print(json.dumps(report,indent=2))
