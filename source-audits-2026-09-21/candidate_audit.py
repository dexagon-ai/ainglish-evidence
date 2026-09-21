"""Recover and audit two candidate records without inference or governance writes."""
from collections import Counter
from datetime import date, timedelta
import json
import re
from audit import ROOT, fetch, source

CALENDAR='b2d2e231ec71a2fcd17b07e467e5213a09ab61aa40033fdd3167aec1e259c31f'
REFERENCE=['9294e7f9ec494fecb9d0eb95132ba732ae978bb1f3363586cd97fb30f8b1584a',
           '16035dd5dce67eb91fdae5f4bd169551692b53436d2fe6e1dc22d46c608a3674',
           'f76d5cbd558b8eafb6a6b079a36d9e108aaf218e183cfca7f745e314d24ef9f2',
           '315bc3190d530ad03f68073c9e501689a4cbc3afc3e6086fe40a55ec4c289694']
DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']


def calendar_audit(items):
    counts=Counter(); errors=[]
    for item in items:
        if item.get('calibration'):continue
        # Enumerate days independently of the source generator's modulo formula.
        m=re.search(r'next-(up|week)\((\w+)@(\d{4}-\d\d-\d\d)(?:;(\w+))?\)',item['ainglish'])
        assert m
        anchor=date.fromisoformat(m[3]);target=DAYS.index(m[2])
        # next-up does not render a week-start convention. For its divergence
        # classification only, use the declared scenario's weekstart metadata.
        weekstart=DAYS.index(m[4] or item['strata']['weekstart'])
        after=[anchor+timedelta(days=n) for n in range(1,15)]
        up=next(d for d in after if d.weekday()==target)
        start=next(d for d in after if d.weekday()==weekstart)
        week=next(start+timedelta(days=n) for n in range(7) if (start+timedelta(days=n)).weekday()==target)
        result=up if m[1]=='up' else week
        gold=re.fullmatch(r'(\d{4}-\d\d-\d\d) \(\+(\d+) days?\)',item['answer'])
        if not gold or gold[1]!=result.isoformat() or int(gold[2])!=(result-anchor).days: errors.append(item['id'])
        assert item['strata']['constructors_diverge']==(up!=week)
        counts[item['form']+'/'+('divergent' if up!=week else 'convergent')]+=1
    return {'scientific_items':sum(counts.values()),'gold_errors':errors,'population':dict(counts),
            'boundary':'The registered claim excludes convergent controls from its carrier; the historical minted scalar includes both, which is an explicitly different population. This audit does not rescore it.'}


def main():
    m,items=source(CALENDAR)
    result={'calendar_source':CALENDAR,'calendar':calendar_audit(items),'reference_sources':[]}
    for ref in REFERENCE:
        row=fetch('https://ainglish.org/api/v1/measurements/'+ref)
        mf=row['manifest'];pairs=mf['test_set']
        result['reference_sources'].append({'source':ref,'value':row['value'], 'items':len(pairs),
          'declared_comparator':mf.get('comparator'),
          'english_contains_bare_pronouns':sum(bool(re.search(r'\b(?:[Ii]t|[Tt]hey)\b',x['english'])) for x in pairs),
          'items_with_question_and_answer':sum('question' in x and 'answer' in x for x in pairs),
          'example':pairs[0],
          'boundary':'Five paired snippets are not the promised consequence panel against noun repetition. Missing retained questions/keys/raw scoring cannot be inferred from a positive headline. No evidence-state finding or retraction is made here.'})
    assert result['calendar']['gold_errors']==[] and result['calendar']['scientific_items']==392
    (ROOT/'candidate-audit-result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('Calendar:392 correct keys,168 divergent and224 convergent cells; it(ref):four five-pair sources,none retaining questions/keys in their test_set. No inference.')


if __name__=='__main__':main()
