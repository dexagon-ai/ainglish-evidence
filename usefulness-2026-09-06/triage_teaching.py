"""Separate literal audit noise from the small manually reviewed teaching finding."""
from collections import Counter
import json
from pathlib import Path
from teaching_mentions import MARKER

ROOT=Path(__file__).resolve().parent
source=json.loads((ROOT/'TEACHING-MENTIONS.json').read_text())
entries={e['slug']:e for e in source['register']['entries']}
rows=[]
for finding in source['findings']:
    row=dict(finding);marker=row['marker'];entry=entries[row['source_slug']]
    own=set(MARKER.findall(entry['form'])) | set((entry.get('slot') or {}).keys())
    if marker in own: status='own_marker_history_not_external_dependency'
    elif marker in ['load-bearing','it','all-or-nothing','exactly-one']:status='ordinary_prose_or_logical_gloss_not_syntax_claim'
    elif row['has_ratified_target']:status='literal_cross_reference_with_ratified_target'
    elif marker in ['req','will','ask','fyi','ack','obs','rep','wit','pred']:status='named_nonratified_marker_needs_explicit_teaching_status'
    else:status='context_review_not_a_gate'
    row['triage']=status;rows.append(row)
report={'source':'TEACHING-MENTIONS.json','counts':dict(Counter(r['triage'] for r in rows)),'rows':rows,
        'boundary':'The raw literal scan deliberately overselects. Own surface histories and normal hyphenated prose are not missing dependencies. Even named nonratified tags may be optional or negative examples; never mechanically invalidate a parent mapping or sentence.'}
with (ROOT/'TEACHING-TRIAGE.json').open('x') as h:json.dump(report,h,indent=2);h.write('\n')
print(json.dumps(report['counts']))
