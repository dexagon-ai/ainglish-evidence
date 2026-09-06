"""Post-collection integrity audit, not a change to the frozen scorer or analysis."""
import hashlib
import json
import os
from pathlib import Path
from design import ROOT, FIELDS, GUIDES, SENDER_SYSTEM, RECEIVER_SYSTEM
from run import decode, verify


def control_messages(i):
    gold = {k: bool((i >> j) & 1) for j, k in enumerate(FIELDS)}
    return gold, [{'role': 'system', 'content': 'Copy the supplied JSON object exactly. No markdown or additional text.'},
                  {'role': 'user', 'content': json.dumps(gold)}]


def conversation(case, arm, stage, previous):
    sender = [{'role': 'system', 'content': SENDER_SYSTEM + '\n' + GUIDES[arm]},
        {'role': 'user', 'content': case['common'] + '\nCommunicate this intended plan, in '
         + ('Ainglish' if arm == 'ainglish' else 'explicit ordinary English') + ':\n' + json.dumps(case['semantic_brief'])}]
    if stage == 'sender':
        return sender
    receiver = [{'role': 'system', 'content': RECEIVER_SYSTEM + '\n' + GUIDES[arm]},
        {'role': 'user', 'content': case['common'] + '\nSender instruction:\n' + previous['sender']['raw']}]
    if stage == 'receiver':
        return receiver
    if stage == 'clarification':
        return sender + [{'role': 'assistant', 'content': previous['sender']['raw']},
            {'role': 'user', 'content': 'The receiver proposed this interpretation:\n' + previous['receiver']['raw']
             + '\nRestate all five choices explicitly once, correcting any mismatch with your intended plan. This clarification is required even if the first interpretation was correct.'}]
    assert stage == 'receiver-final'
    return receiver + [{'role': 'assistant', 'content': previous['receiver']['raw']},
        {'role': 'user', 'content': 'The sender clarifies:\n' + previous['clarification']['raw'] + '\nReturn the complete revised five-field plan.'}]


def validate(rows, receipt, plan, cases, condition, count_input):
    assert len({case['id'] for case in cases}) == len(cases)
    assert len(cases) == plan['episodes_per_condition_arm']
    assert receipt['status'] in ['complete', 'aborted-controls']
    assert receipt['governance_evidence'] is False
    expected = [('control', str(i)) for i in range(plan['qualification']['control_items'])]
    if receipt['status'] == 'complete':
        expected += [('target', arm, case['id'], stage) for arm in plan['arms'] for case in cases for stage in plan['stages']]
        assert receipt['episodes'] == len(cases) * len(plan['arms'])
    else:
        assert receipt['episodes'] == 0
    actual = [(r['phase'], r['id']) if r['phase'] == 'control'
              else (r['phase'], r['arm'], r['episode'], r['stage']) for r in rows]
    assert actual == expected, 'Missing, duplicate, extra or reordered calls'
    by_id = {case['id']: case for case in cases}
    previous = {}
    controls = []
    for row in rows:
        assert row['condition'] == condition
        assert type(row['ended']) is bool
        assert isinstance(row['raw'], str)
        if row['phase'] == 'control':
            gold, messages = control_messages(int(row['id']))
            decoded = decode(row['raw'], row['ended'])
            controls.append({'correct': decoded == gold, 'valid': decoded is not None})
            cap = 128
        else:
            key = (row['arm'], row['episode'])
            prior = previous.setdefault(key, {})
            messages = conversation(by_id[row['episode']], row['arm'], row['stage'], prior)
            prior[row['stage']] = row
            cap = plan['max_tokens'][row['stage']]
        assert row['messages'] == messages, 'Transmitted prompt differs from frozen conversation'
        assert type(row['input_tokens']) is int and 0 < row['input_tokens'] <= plan['max_prompt_tokens']
        assert count_input(messages) == row['input_tokens'], 'Input token recount differs'
        assert type(row['output_tokens']) is int and 0 < row['output_tokens'] <= cap
    assert receipt['controls'] == controls
    qualified = sum(r['correct'] for r in controls) >= plan['qualification']['minimum_correct'] and all(r['valid'] for r in controls)
    assert qualified == (receipt['status'] == 'complete')
    return {'condition': condition, 'status': receipt['status'], 'calls': len(rows),
            'controls': len(controls), 'target_calls': len(rows) - len(controls),
            'input_tokens_recounted': sum(r['input_tokens'] for r in rows),
            'journalled_output_tokens': sum(r['output_tokens'] for r in rows),
            'exact_prompt_schedule_verified': True}


def main():
    assert (ROOT / 'results/finished.json').is_file(), 'Wait for the original collection process to finish'
    freeze = verify()
    plan = json.loads((ROOT / 'PLAN.json').read_text())
    cases = json.loads((ROOT / 'cases.json').read_text())
    receipts = {name: json.loads((ROOT / 'results' / (name + '.receipt.json')).read_text()) for name in plan['conditions']}
    complete = [r for r in receipts.values() if r['status'] == 'complete']
    assert complete, 'No complete condition with tokenizer provenance'
    revision = complete[0]['base_revision']
    snapshot = Path('/home/dexagon/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots') / revision
    assert snapshot.is_dir(), 'Cached exact tokenizer required; no downloads'
    tokenizer_sha = hashlib.sha256((snapshot / 'tokenizer.json').read_bytes()).hexdigest()
    assert all(r['base_revision'] == revision and r['tokenizer_sha256'] == tokenizer_sha for r in complete)
    for key in ['HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE']:
        os.environ[key] = '1'
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True, use_fast=True)
    def count_input(messages):
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return len(tokenizer.encode(prompt, add_special_tokens=False))
    results = []
    for name in plan['conditions']:
        path = ROOT / 'results' / (name + '.jsonl')
        raw = path.read_bytes()
        assert raw.endswith(b'\n'), 'Incomplete journal tail'
        rows = [json.loads(line) for line in raw.splitlines()]
        audit = validate(rows, receipts[name], plan, cases, name, count_input)
        if receipts[name]['status'] == 'complete':
            assert receipts[name]['guide_tokens'] == {k: len(tokenizer.encode(v, add_special_tokens=False)) for k, v in GUIDES.items()}
        results.append(dict(audit, journal_sha256=hashlib.sha256(raw).hexdigest()))
    result = {'kind': 'ainglish.sender-receiver-journal-audit.v1', 'freeze': freeze,
        'tokenizer_sha256': tokenizer_sha, 'conditions': results,
        'boundary': 'Post-collection mechanical integrity audit. Does not change the frozen scorer, exclude failures, retry inference or supply governance evidence. Input tokens recounted from every transmitted prompt. Output counts are checked against caps but cannot be independently reconstructed exactly: raw generated token IDs were not journalled and decoded text was stripped.'}
    with (ROOT / 'JOURNAL-AUDIT.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
