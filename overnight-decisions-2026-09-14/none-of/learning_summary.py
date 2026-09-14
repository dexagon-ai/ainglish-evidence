"""Preplanned paired cold/entry-loaded counts. No new estimator or reader calls."""
from collections import Counter,defaultdict
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
path=ROOT/'learning.runspec.json.attempt-2dcf352a-9d97-4c1e-be71-bd8fe6754f4d.cells.json'
rows=json.loads(path.read_text())['rows']
groups=defaultdict(lambda:defaultdict(dict))
for r in rows:
 assert r['correct']==(r['answer']==r['expected'])
 groups[(r['reader'],r['strata']['form'])][r['item_id']][r['arm']]=r['correct']
report=[]
for (reader,form),items in sorted(groups.items()):
 assert all(set(c)=={'english','ainglish'} for c in items.values())
 cold=sum(c['english'] for c in items.values());loaded=sum(c['ainglish'] for c in items.values())
 report.append({'reader':reader,'form':form,'paired_items':len(items),'cold_correct':cold,'loaded_correct':loaded,
  'gain_pp':100*(loaded-cold)/len(items),'corrected':sum(not c['english'] and c['ainglish'] for c in items.values()),
  'regressed':sum(c['english'] and not c['ainglish'] for c in items.values())})
out={'kind':'paired-entry-loaded-descriptive-counts','target_calls':len(rows),'rows':report,
 'boundary':'The SDK arm named english is COLD MARKED TEXT in this learnability study, not careful English. The ainglish arm is identical text plus the full frozen entry. Not weight training, independent confirmation, human validation or erasure of cold CAD losses.'}
(ROOT/'learning.paired-report.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
