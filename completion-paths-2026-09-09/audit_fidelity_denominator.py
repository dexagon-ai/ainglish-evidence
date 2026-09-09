"""Retrospective audit of our own scalar: no new experiment or independent confirmation."""
import hashlib,json,re
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'moved-direction-tag-fidelity-carrier-2026-08-26'
packet=json.loads((OLD/'fidelity-cases.json').read_text())
result=json.loads((OLD/'fidelity-result.json').read_text())
items=packet['items']
canonical=json.dumps(items,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
assert hashlib.sha256(canonical).hexdigest()==packet['sha256']
by_id={x['id']:x for x in items}
def truth(row):
    text=row['source_event']
    if 'previous schedule is unavailable' in text or 'no notice supersedes the other' in text:return 'unknown'
    match=re.fullmatch(r'The .+ was scheduled for (.+) and is now rescheduled to (.+)\.',text)
    if match:
        a,b=map(datetime.fromisoformat,match.groups())
        return 'moved-earlier' if b<a else 'moved-later' if b>a else 'unchanged'
    if 'no schedule change occurred' in text:return 'unchanged'
    raise ValueError('Unrecognized retained record')
truths={key:truth(row) for key,row in by_id.items()}
summary=[]
for reader in sorted({x['reader'] for x in result['rows']}):
    rows=[x for x in result['rows'] if x['reader']==reader]
    assert len(rows)==96 and len({x['case_id'] for x in rows})==96
    claims=[x for x in rows if x['parsed'] in ('moved-earlier','moved-later')]
    known=[x for x in claims if truths[x['case_id']]!='unknown']
    valid=[x for x in known if x['parsed']==truths[x['case_id']]]
    summary.append({'reader':reader,'old_classification_denominator':96,
      'old_classification_correct':sum(x['correct'] for x in rows),
      'abstentions':sum(x['parsed']=='neither tag is warranted' for x in rows),
      'emitted_tag_choices':len(claims),'unverifiable_emitted_choices':len(claims)-len(known),
      'known_ground_truth_choices':len(known),'true_known_choices':len(valid),
      'retrospective_known_choice_fraction':len(valid)/len(known) if known else None,
      'limitations':'A post-hoc controlled-choice audit, not a prospectively registered fidelity study or organic use.'})
report={'kind':'ainglish.own-fidelity-denominator-audit.v1','measurement':'b6c4621d4357cd61492a0956f0dbdba5d98505bc0741d7148dc92213aa3231ed',
 'attempt':'79efbec4-36fc-4daf-8af6-4da17e268731','items_digest':packet['sha256'],
 'defect':'The filed scalar is 3-class exact classification accuracy over all 96 rows, including correct abstentions and unavailable/conflicting baselines. It is not the protocol fraction of audited tagged claims that survive ground-truth checking.',
 'cases':len(items),'unknown_ground_truth_cases':sum(x=='unknown' for x in truths.values()),'readers':summary,
 'action':'Retract own misclassified tag_fidelity evidence; retain all raw cells as controlled classification diagnostics. Do not substitute these post-hoc denominators as a new preregistered pass.',
 'new_inference_calls':0,'independent_confirmation':False}
with (ROOT/'fidelity-denominator-audit.json').open('x') as f:json.dump(report,f,indent=2,ensure_ascii=False)
print(json.dumps(report,indent=2))
