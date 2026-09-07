"""Structural, pairing, freeze and split checks; no tokenizer or inference calls."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import verify_freeze
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rows(name):return [json.loads(s) for s in (ROOT/name).read_text().splitlines() if s]
def verify(public=False):
    for name,expected in json.loads((ROOT/'FROZEN.json').read_text()).items():assert digest(ROOT/name)==expected,name
    return verify_freeze(ROOT) if public else None
def audit():
    verify();cases=rows('cases.jsonl');tasks=rows('tasks.jsonl')
    assert len(cases)==192 and len({r['frame'] for r in cases})==24 and len(tasks)==480
    assert Counter(r['family'] for r in cases)==dict.fromkeys(['alternatives','deadline','multiplicity','participants','unknown','update'],32)
    assert len({r['id'] for r in tasks})==480
    for case in cases:
        assert case['options'][case['answer']]==case['semantic_gold']
        paired=[r for r in tasks if r['case_id']==case['id']]
        assert {r['arm'] for r in paired}=={'ainglish','english'}
        assert all((r['answer'],r['gold_bits'],r['options'])==(case['answer'],case['gold_bits'],case['options']) for r in paired)
    for frame in {r['frame'] for r in cases}:
        assert Counter(r['answer'] for r in cases if r['frame']==frame)==dict.fromkeys('ABCD',2)
    a,e=rows('train-ainglish.jsonl'),rows('train-english.jsonl')
    assert len(a)==len(e)==768 and a[576:]==e[576:]
    for x,y in zip(a,e):
        assert x['id']==y['id'] and x['messages'][-1]==y['messages'][-1]
        assert len(x['messages'])==len(y['messages'])==3
    # The prior naive rotation would have taught a fixed answer label per domain.
    # Every domain now spans all four labels across its teaching frames.
    teaching_domains={r['id'].split('/')[-1] for r in a[:576]}
    for domain in teaching_domains:
        assert Counter(r['messages'][-1]['content'] for r in a[:576] if r['id'].split('/')[-1]==domain)==dict.fromkeys('ABCD',12)
    target_prompts={r['messages'][1]['content'] for r in tasks}
    for train in [a,e]:
        assert len({r['id'] for r in train})==768
        assert not target_prompts & {r['messages'][1]['content'] for r in train}
    source=json.loads((ROOT.parent/'contextual-teaching-2026-09-07/source-constructs.json').read_text())
    assert len(source['entries'])==6 and all(r['status']=='current' and r['ratified_at'] and r['kind']!='protocol' for r in source['entries'].values())
    return {'training_per_arm':768,'structural_cases':192,'authored_frames':24,'target_calls_per_condition':480,
        'governance_evidence':False,'exact_train_target_prompt_overlap':0,'label_balance_per_frame':dict.fromkeys('ABCD',2)}
if __name__=='__main__':print(json.dumps(audit()))
