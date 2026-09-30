"""Create unmeasured review material only; no tokenizer, inference, mint or filing."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
subjects = [
    ('ticket K17', 'closed'), ('task P24', 'timed_out'),
    ('claim M31', 'confirmed'), ('construct J42', 'deprecated'),
    ('test B58', 'passed'), ('order V63', 'cancelled'),
    ('shipment F74', 'delivered'), ('subscription C85', 'expired'),
    ('appeal R96', 'dismissed'), ('grant H12', 'revoked'),
    ('invoice D23', 'paid'), ('inspection S34', 'failed'),
    ('reservation W45', 'released'), ('batch N56', 'accepted'),
    ('account L67', 'suspended'), ('case Q78', 'resolved'),
]
pairs = []
for i, (subject, status) in enumerate(subjects):
    event = f'events/E{i+101}'
    rule = f'status-rule-{i+101}@3'
    pairs.append({'stratum':'on-record', 'ainglish':f'{subject}: {status} on-record({event}).',
        'english':f'{subject}: {status}, recorded at onset in immutable event {event}.',
        'facts':{'subject':subject, 'status':status, 'status_stating_event':event,
                 'event_immutable':True, 'event_written_at_status_onset':True,
                 'current_truth':'not asserted', 'locator_resolves':'stipulated in this hypothetical case'}})
    relayed = i >= 8
    time = '2026-09-30T08:00Z' if relayed else None
    pairs.append({'stratum':'derived-at-read',
        'ainglish':f'{subject}: {status} derived-at-read({rule})'+(f' as_of({time})' if relayed else '')+'.',
        'english':f'{subject}: {status}, computed '+(f'at {time}' if relayed else 'when this message was written')+f' using {rule}; no event records that status.',
        'facts':{'subject':subject, 'status':status, 'rule_version':rule,
                 'computation_time':time or 'message composition', 'cached_or_relayed':relayed,
                 'status_stating_event':None, 'current_truth':'not asserted',
                 'reproduction_needs':'complete original inputs and clock when used, plus this rule version'}})
assert len(pairs) == 32
assert len({p['ainglish'] for p in pairs}) == 32
assert all(sum(p['stratum']==s for p in pairs)==16 for s in ['on-record','derived-at-read'])
out = {'status':'REVIEW DRAFT - NOT FROZEN OR MEASURED',
       'proposal':'a-48a9vdwkbamejar6',
       'content_digest':'dd8c47e79c444cd9bdfefe0eef7be71c6f550205bcbc21d7dc033f8d5fb885fa',
       'comparator_review':'Candidate concise complete renderings, not a demonstrated shortest-English optimum. Author must review onset/immutability, time and no-record scope before freeze.',
       'sampling_unit':'32 authored complete statements; 16 subject/status slots reused across forms, not 32 independent natural-world draws',
       'planned_reducer':'maximum mean across each form and each fixed tokenizer; pooled equal-form mean diagnostic only',
       'calls':0, 'pairs':pairs}
(ROOT/'on-record-token-review-draft.json').write_text(json.dumps(out,indent=2)+'\n')
print('32 unmeasured review pairs, 16 per form; no tokenizer or model called')
