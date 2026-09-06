"""Continue only unstarted calls after an external shared-service collision.

The original source, qualification, target order, prompts, scoring and settings
are immutable. A changed request, uncertain in-flight call or non-prefix journal
is refused. This is not an inference retry or a replacement experiment.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import time
from study import ROOT, api, ram, Journal, disk_guard, save_new, verify_freeze, decode_json, reader_messages


def requests(plan, controls, cases):
    model = plan['models'][2][0]
    def request(messages):
        return {'model': model, 'messages': messages, 'stream': False,
                'keep_alive': '5m', 'options': plan['options']}
    result = [('control/' + c['id'], request(c['messages'])) for c in controls]
    result += [(c['id'] + '/' + arm, request(reader_messages(c, arm, c['messages'][arm])))
               for c in cases for arm in ['ainglish', 'english']]
    return result


def validate_prefix(journal, planned):
    keys = [e['data']['call_id'] for e in journal.events if e['kind'] == 'begin']
    if keys != [key for key, request in planned[:len(keys)]]:
        raise RuntimeError('Journal is not a completed prefix of the original call order')
    for key, request in planned[:len(keys)]:
        if journal.lookup(key, request) is None:
            raise RuntimeError('Previous call is not durably complete; no replay')
    return len(keys)


def main(commit, check_only):
    original = verify_freeze(ROOT)
    assert original.startswith('37382e6')
    for filename in ['resume_unstarted_calls.py', 'test_resume.py', 'RECOVERY.md']:
        relative = (ROOT / filename).relative_to(ROOT.parent).as_posix()
        assert subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=ROOT.parent) == (ROOT / filename).read_bytes()
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'origin/main'], cwd=ROOT.parent, check=True)
    assert not (ROOT / 'RESULTS.json').exists(), 'Study is complete; no additional spend'
    plan = json.loads((ROOT / 'PLAN.json').read_text())
    controls = json.loads((ROOT / 'controls.json').read_text())
    cases = [c for c in json.loads((ROOT.parent / 'communication-diagnostics-2026-09-06/cases.json').read_text())
             if c['dimensions'] in plan['target_dimensions']]
    model, model_digest = plan['models'][2]
    prior = [json.loads((ROOT / f'execution/result-{i}.json').read_text()) for i in [0, 1]]
    assert all(not r['qualified'] and not r['targets'] for r in prior)
    qualified = json.loads((ROOT / 'execution/qualification-2.json').read_text())
    assert qualified['qualified'] and sum(c['correct'] for c in qualified['qualification']) == 16
    planned = requests(plan, controls, cases)
    assert len(planned) == 232
    with Journal(ROOT / 'execution/reader-2.jsonl', dict(plan, selected_model=model), resume=True) as journal:
        completed_before = validate_prefix(journal, planned)
        assert completed_before >= 16
        print(json.dumps({'completed': completed_before, 'unstarted': len(planned) - completed_before,
                          'uncertain': 0, 'original_freeze': original, 'continuation_commit': commit}), flush=True)
        if check_only:
            return
        if api('ps')['models']:
            raise RuntimeError('Shared service occupied; no new call or eviction')
        tags = {m['name']: m for m in api('tags')['models']}
        assert tags[model]['digest'] == model_digest
        disk_guard()
        if ram() < tags[model]['size'] * 1.1 + 4 * 1024**3:
            raise RuntimeError('Pre-load RAM reserve unavailable; no call started')
        receipt = {'original_freeze': original, 'continuation_commit': commit,
                   'completed_before': completed_before, 'unstarted_before': len(planned) - completed_before,
                   'previous_tail': journal.events[-1]['hash'], 'retries': 0,
                   'reason': 'Shared caller stopped the previous process before its next request. Continue the unchanged sequence from its durably completed prefix.'}
        save_new(ROOT / f'execution/continuation-{completed_before}.json', receipt)
        for key, request in planned:
            if journal.lookup(key, request) is not None:
                continue
            disk_guard()
            if ram() < 3 * 1024**3:
                raise RuntimeError('Host RAM reserve reached before next call')
            if any(m['name'] != model for m in api('ps')['models']):
                raise RuntimeError('Another shared caller arrived; stop before next call')
            journal.begin(key, request)
            start = time.monotonic()
            response = api('chat', request)
            after = api('ps')['models']
            journal.end(key, {'raw': response['message']['content'], 'response': response,
                'resident_after': after, 'latency_s': time.monotonic() - start})
            own = [m for m in after if m['name'] == model]
            if len(own) != 1 or own[0]['digest'] != model_digest or own[0].get('size_vram') != 0:
                raise RuntimeError('CPU-only pinned placement not verified; preserve the received answer')
            if (len(journal.completed) - 16) % 24 == 0:
                print(len(journal.completed) - 16, 'target answers retained, zero retries', flush=True)
        assert validate_prefix(journal, planned) == 232
        row = dict(qualified, targets=[])
        for case in cases:
            for arm in ['ainglish', 'english']:
                end = journal.completed[case['id'] + '/' + arm]
                decoded = decode_json(end['raw'], case['brief'])
                ended = end['response'].get('done') is True and end['response'].get('done_reason') == 'stop'
                row['targets'].append({'id': case['id'], 'dimensions': case['dimensions'],
                    'context': case['id'].split('/')[0], 'arm': arm, 'parsed': decoded is not None,
                    'correct': ended and decoded == case['brief'], 'truncated': not ended})
        save_new(ROOT / 'execution/result-2.json', row)
    loaded = api('ps')['models']
    if loaded and all(m['name'] == model for m in loaded):
        api('generate', {'model': model, 'keep_alive': 0})
    results = prior + [row]
    summaries = []
    for reader in results:
        groups = defaultdict(list)
        for target in reader['targets']:
            groups[(target['arm'], target['dimensions'])].append(target)
        summaries.extend({'model': reader['model'], 'arm': arm, 'dimensions': dimension, 'n': len(group),
            **{key: sum(r[key] for r in group) for key in ['correct', 'parsed', 'truncated']}}
            for (arm, dimension), group in groups.items())
    save_new(ROOT / 'RESULTS.json', {'governance_evidence': False, 'models': results,
        'summaries': summaries, 'limits': plan['limits'], 'continuation': receipt})
    print(json.dumps(summaries, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    main(args.commit, args.check_only)
