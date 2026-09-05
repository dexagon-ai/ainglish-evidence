"""Make a review queue from the fixed public sweep; never moderate anything."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'corpus-reviewed/report.json').read_text())
results=data['results']
rows=[]
for row in results:
    if row['status']!='mismatch':continue
    rows.append({k:row.get(k) for k in ['attempt_id','manifest_hash','proposal','submitter','filed_value',
        'evidence_state','counts_toward_verdict','retraction','is_replication','replicates_hash','headline_difference']}
        | {'derived_value':row['derived']['floor'],'classification':'candidate requiring exact-target review, not an adjudication'})
rows.sort(key=lambda r:(not bool(r['counts_toward_verdict']),r['evidence_state']!='valid',r['attempt_id']))
out={'kind':'ainglish.token-integrity-review-queue.v1','snapshot_at':data['at'],
     'status_counts':dict(Counter(r['status'] for r in results)),
     'mismatch_snapshot_states':dict(Counter(
         'already_excluded' if r['evidence_state']!='valid' or r['retraction'] else
         'counting' if r['counts_toward_verdict'] else 'not_currently_counting' for r in rows)),
     'claim_boundary':'Fresh-read exact attempt before any action. Current tokenizer recount only; no model inference, fresh-input replication, automatic moderation, or language-quality verdict.',
     'rows':rows}
with (ROOT/'review-queue.json').open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
