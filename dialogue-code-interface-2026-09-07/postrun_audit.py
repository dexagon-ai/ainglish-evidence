"""Retained-journal audit only. It cannot make model calls or change the frozen score."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import Journal,save_new
from study import score

events=Journal._validate((ROOT/'execution/calls.jsonl').read_text())
begins={r['data']['call_id']:r['data'] for r in events if r['kind']=='begin'}
ends={r['data']['call_id']:r['data'] for r in events if r['kind']=='end'}
controls=json.loads((ROOT/'controls.json').read_text());result=json.loads((ROOT/'RESULTS.json').read_text())
assert set(begins)==set(ends)=={r['id'] for r in controls}
assert not result['qualified'] and not result['rows'] and not result['dictionary_reads']
scored=[score(ends[r['id']]['raw'],ends[r['id']]['ended'],r['gold']) for r in controls]
for r in ends.values():assert len(r['input_ids'])==r['input_tokens'] and len(r['output_ids'])==r['output_tokens']
audit={'kind':'ainglish.dialogue-code-qualification-readback.v1','controls':len(controls),
    'correct':sum(r['correct'] for r in scored),'valid_shape':sum(r['valid'] for r in scored),
    'truncated':sum(r['truncated'] for r in scored),'language_target_calls':0,'model_calls_by_audit':0,
    'input_tokens':sum(r['input_tokens'] for r in ends.values()),'output_tokens':sum(r['output_tokens'] for r in ends.values()),
    'qualification_floor':28,'required_all_valid':True,'governance_evidence':False,
    'boundary':'Same-author reconstruction of the original frozen score, not independent replication. No failed response was repaired or retried.'}
save_new(ROOT/'POSTRUN-AUDIT.json',audit)
lines=['# Five-character dialogue interface: qualification stopped the study','',
    f"The frozen neutral screen scored {audit['correct']}/32 exact answers, against28/32 required; {audit['valid_shape']}/32 met the declared five-character shape, with{audit['truncated']} truncated outputs.",'',
    'No Ainglish or English target dialogue was run. There are no measured dictionary-lookup, history, repair or per-success costs for this study. The original JSON screen remains a separate4/16 failure; this successor changed both wrapper and neutral vocabulary and does not isolate either effect.',
    '', 'The public journal retains all32 requests and completed outputs, exact token IDs and the unchanged parser. This readback makes zero inference calls and is not independent replication. No qualification retries or post-hoc score repairs were made.']
with (ROOT/'RESULTS.md').open('x') as f:f.write('\n'.join(lines)+'\n')
print(json.dumps(audit))
