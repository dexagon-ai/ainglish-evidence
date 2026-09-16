"""Detect hidden-intent gold conflicts; no inference and no automatic moderation."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT.parent

def digest(obj):
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    folder=EVIDENCE/'one-or-more-exactly-one-comprehension-carrier-v2-2026-09-03'
    banks={};checks=[]
    for form,prefix in (('one-or-more','c6d3e3bd'),('exactly-one','ac6bb7c6')):
        items=json.loads((folder/f'items-{form}-bare.json').read_text())['items']
        m=json.loads((ROOT/f'candidate-role-{prefix}.json').read_text())
        assert digest(items)==m['manifest']['items_sha256']
        banks[form]={i['scenario_id']:i for i in items if not i.get('calibration')}
        checks.append({'form':form,'manifest_hash':m['manifest_hash'],'items_sha256':digest(items),
                       'comparator':m['manifest']['comparator'],'target_items':len(banks[form])})
    a,b=banks['one-or-more'],banks['exactly-one']
    assert set(a)==set(b)
    same=[];conflicts=[]
    for k in a:
        x,y=a[k],b[k]
        equivalent=(x['english']==y['english'] and x['question']==y['question']
                    and set(x['options'])==set(y['options']))
        if equivalent:same.append(k)
        if equivalent and x['answer']!=y['answer']:
            conflicts.append({'scenario_id':k,'english':x['english'],'question':x['question'],
                              'one_or_more_options':x['options'],'exactly_one_options':y['options'],
                              'one_or_more_gold':x['answer'],'exactly_one_gold':y['answer'],
                              'stratum':x['strata']['stratum']})
    assert len(same)==120 and len(conflicts)==20
    report={'kind':'role-cardinality-visible-input-gold-audit-v1','model_calls':0,'banks':checks,
            'same_english_question_and_answer_vocabulary_pairs':len(same),
            'opposite_gold_pairs':len(conflicts),
            'conflict_strata':dict(Counter(c['stratum'] for c in conflicts)),
            'note':'Option ordering differs. It provides no semantic information about the hidden intended cardinality. These can describe recovery of an assigned intention, but cannot establish comprehension of what the ambiguous English actually states. Both polarities are retained, irrespective of score direction.',
            'conflicts':conflicts}
    (ROOT/'role-gold-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('same_english_question_and_answer_vocabulary_pairs','opposite_gold_pairs','conflict_strata','model_calls')}))

if __name__=='__main__':main()
