"""POST-HOC sensitivity audit. Never edits frozen scores, gates or target calls."""
import json
from collections import Counter
from design import ROOT, decode_message, decode_json

def main():
    cases = json.loads((ROOT/'cases.json').read_text())
    events = [json.loads(line) for line in (ROOT/'results/base.jsonl').read_text().splitlines()]
    calls = {e['data']['call_id']:e['data'] for e in events if e['kind']=='end'}
    counts = Counter()
    examples = []
    for case in cases:
        for arm in ['ainglish','english']:
            key = case['id']+'/'+arm
            if case['dimensions']==1:
                raw = calls['reference/'+key]['raw']
                try:
                    data = json.loads(raw)
                    subset = {k:data[k] for k in case['brief']}
                    counts['one_field_'+arm+'_requested_values_correct'] += subset == case['brief'] and all(type(v) is bool for v in subset.values())
                    counts['one_field_'+arm+'_extra_keys'] += set(data) != set(case['brief'])
                except (ValueError, KeyError, TypeError):
                    pass
            if case['dimensions'] != 5: continue
            raw = calls['sender/'+key]['raw']
            # Only punctuation sensitivity: remove terminal colons/periods from each line.
            # No phrase correction, key replacement, selected retries, or new scoring gate.
            adjusted = '\n'.join(line.rstrip().rstrip(':.').rstrip() for line in raw.splitlines())
            strict = decode_message(raw, arm, case['brief'])
            punct = decode_message(adjusted, arm, case['brief'])
            counts[arm+'_strict_parsed'] += strict is not None
            counts[arm+'_punctuation_parsed'] += punct is not None
            counts[arm+'_punctuation_correct'] += punct == case['brief']
            if strict is None and punct is not None and len([e for e in examples if e['arm']==arm]) < 2:
                examples.append({'id':case['id'],'arm':arm,'raw':raw,'intended':case['brief'],'punctuation_only_decoded':punct})
    result = {'kind':'ainglish.communication-diagnostic.posthoc-format-audit.v1',
        'posthoc':True,'changes_frozen_gate':False,'new_reader_calls':0,'counts':dict(counts),'examples':examples}
    (ROOT/'FORMAT-AUDIT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(result['counts'],indent=2))

if __name__=='__main__':main()
