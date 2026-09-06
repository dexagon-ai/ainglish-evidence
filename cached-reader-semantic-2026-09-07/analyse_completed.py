"""Recompute the declared completed-study scores and show context/format counts.

Refuses partial results. No new inference, relaxed scoring, selected exclusions
or alteration of either qualification gate.
"""
from collections import defaultdict
import json
from pathlib import Path
from study import ROOT, Journal, decode_json, verify_freeze


def grouped(rows, fields):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in fields)].append(row)
    return [{**dict(zip(fields, key)), 'n': len(values),
             **{name: sum(row[name] for row in values) for name in ['correct', 'parsed', 'truncated']}}
            for key, values in groups.items()]


def main():
    freeze = verify_freeze(ROOT)
    result = json.loads((ROOT / 'RESULTS.json').read_text())
    plan = json.loads((ROOT / 'PLAN.json').read_text())
    cases = {c['id']: c for c in json.loads((ROOT.parent / 'communication-diagnostics-2026-09-06/cases.json').read_text())}
    scored = []
    counts = []
    for index, model in enumerate(result['models']):
        events = Journal._validate((ROOT / f'execution/reader-{index}.jsonl').read_text())
        starts = [e['data']['call_id'] for e in events if e['kind'] == 'begin']
        ends = {e['data']['call_id']: e['data'] for e in events if e['kind'] == 'end'}
        assert len(starts) == len(set(starts)) == len(ends)
        assert set(starts) == set(ends)
        assert len(ends) == 16 + (216 if model['qualified'] else 0)
        targets = []
        for key, end in ends.items():
            is_control = key.startswith('control/')
            response = end['response']
            counts.append({'model': model['model'], 'phase': 'qualification' if is_control else 'target',
                'prompt_tokens': response['prompt_eval_count'], 'output_tokens': response['eval_count']})
            if is_control:
                continue
            identifier, arm = key.rsplit('/', 1)
            case = cases[identifier]
            decoded = decode_json(end['raw'], case['brief'])
            ended = response.get('done') is True and response.get('done_reason') == 'stop'
            target = {'id': identifier, 'dimensions': case['dimensions'], 'context': identifier.split('/')[0],
                'arm': arm, 'parsed': decoded is not None, 'correct': ended and decoded == case['brief'], 'truncated': not ended}
            targets.append(target)
            scored.append(dict(target, model=model['model']))
        assert targets == model['targets'], 'Stored scores differ from the frozen decoder and raw journal'
    summaries = grouped(scored, ['model', 'arm', 'dimensions'])
    assert summaries == result['summaries']
    context = grouped(scored, ['model', 'context', 'arm', 'dimensions'])
    token_groups = defaultdict(list)
    for row in counts:
        token_groups[(row['model'], row['phase'])].append(row)
    usage = [{'model': model, 'phase': phase, 'calls': len(values),
              'provider_reported_prompt_tokens': sum(r['prompt_tokens'] for r in values),
              'provider_reported_output_tokens': sum(r['output_tokens'] for r in values)}
             for (model, phase), values in token_groups.items()]
    report = {'kind': 'ainglish.completed-reader-diagnostic-audit.v1', 'freeze': freeze,
        'governance_evidence': False, 'relaxed_scoring': False, 'target_calls': len(scored),
        'qualification_calls': sum(r['phase'] == 'qualification' for r in counts),
        'summaries': summaries, 'by_context': context, 'usage': usage,
        'usage_boundary': 'Native provider counts retained. Generated token IDs and provider billing are not reconstructed.',
        'limits': plan['limits']}
    (ROOT / 'AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Cached reader comparison after prospective wrapper repair', '',
        'Only Mistral passed the fresh neutral screen: 16/16. Qwen scored 10/16 and Gemma 4/16, below the declared 14/16 floor. Failed readers received no language cases and are not assigned a language score of zero.', '',
        'The completed campaign retained 48 qualification answers and 216 target answers. All targets come from one qualified model over three authored contexts. The cases are the previously published reference-message diagnostic, deliberately reused with a different reader configuration; they are not a new independent holdout.', '',
        '| Reader | Fields required | Language | Exact joint answers | Parsed under declared protocol | Truncated |',
        '|---|---:|---|---:|---:|---:|']
    for row in summaries:
        lines.append(f"| {row['model']} | {row['dimensions']} | {row['arm']} | {row['correct']}/{row['n']} | {row['parsed']}/{row['n']} | {row['truncated']} |")
    lines += ['', 'The score requires the complete requested boolean object, bare or within one permitted JSON fence, with no extra/duplicate keys or additional prose. A parser refusal is reported separately above; it must not be described as a clean semantic error. No post-hoc projection or punctuation repair changes these scores.', '',
        '## Context breakdown', '', '| Context | Fields | Language | Exact joint answers | Parsed |', '|---|---:|---|---:|---:|']
    for row in context:
        lines.append(f"| {row['context']} | {row['dimensions']} | {row['arm']} | {row['correct']}/{row['n']} | {row['parsed']}/{row['n']} |")
    lines += ['', '## Interruption and accounting', '',
        'Another caller entered the shared service after the first three Mistral target answers. The guard stopped before the next request, with no uncertain in-flight call. The published continuation validated the exact completed prefix and reused those answers verbatim. Remaining requests used the unchanged order, prompts, model digest, CPU-only options, parser and 512-token budget. No scientific call was retried. See RECOVERY.md and the continuation receipt.', '',
        'AUDIT.json reproduces the stored scores from the hash-chained raw journals and records native provider token counts. These are not reconstructed generated-token IDs, cache discounts or a monetary bill.', '',
        '## What this establishes — and what it does not', '',
        'This diagnoses a particular reference-assisted reader interface. The earlier strict-wrapper failures remain failures; this successor changed both the declared wrapper protocol and neutral vocabulary prospectively. The two screens do not isolate the wrapper’s causal effect.', '',
        'Mistral’s qualification does not unlock the separate failed Qwen writer/reader gate, train an adapter, execute operational work, confirm a proposal or demonstrate human understanding. Three named model families were screened, but only one reached this language comparison.', '',
        'These model weights and tokenizers already know English. The observed comparison concerns those current conditions, not future learned Ainglish performance or language-inherent superiority. Unqualified readers, format failures and adverse observations remain in the report.']
    (ROOT / 'READING.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'target_calls': len(scored), 'qualification_calls': report['qualification_calls'], 'summaries': summaries}, indent=2))


if __name__ == '__main__':
    main()
