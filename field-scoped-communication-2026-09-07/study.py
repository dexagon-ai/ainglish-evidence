"""Prospective field-scoped successor, never a rescore of the previous study."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'overnight-runtime-2026-09-06'))
from runtime import Journal, LocalReader, save_new, verify_freeze
sys.path.insert(0, str(ROOT.parent / 'communication-diagnostics-2026-09-06'))
from design import FIELDS, PHRASES, MEANINGS, COMMON, decode_json as strict_decode

def decode(raw, fields):
    candidate = raw.strip()
    fence = re.fullmatch(r'```(?:json)?[ \t]*\n([\s\S]*?)\n```', candidate, re.IGNORECASE)
    return strict_decode(fence.group(1) if fence else candidate, fields)

def interface(fields, record, guide, questions):
    return [
        {'role': 'system', 'content': 'Read the record without performing any action. Return exactly one JSON object. '
            'The ONLY allowed keys are: ' + ', '.join(fields) + '. Every value must be true or false. '
            'Do not add other keys. One optional JSON code fence is accepted; no explanation or other content.'},
        {'role': 'user', 'content': 'Reference for the requested keys only:\n' + guide +
            '\nRecord:\n' + record + '\nAnswer these questions only:\n' + questions +
            '\nRequired output keys: ' + ', '.join(fields)},
    ]

def reader_messages(case, arm, text):
    fields = list(case['brief'])
    guide = '\n'.join(f'{f}: false = {PHRASES[arm][FIELDS.index(f)][0]}; '
                      f'true = {PHRASES[arm][FIELDS.index(f)][1]}.' for f in fields)
    questions = '\n'.join(f'{f}: {MEANINGS[FIELDS.index(f)]}' for f in fields)
    return interface(fields, COMMON + '\n' + case['context'] + '\nMessage:\n' + text, guide, questions)

def controls():
    names = ['insulated', 'rotating', 'portable', 'certified', 'illuminated']
    words = [('uninsulated', 'insulated'), ('stationary', 'rotating'), ('fixed', 'portable'),
             ('uncertified', 'certified'), ('dark', 'illuminated')]
    rows = []
    for dimension in [1, 2, 5]:
        for i in range(16):
            bits = [bool(i & (1 << j)) for j in range(4)]
            bits.append(bits[0] ^ bits[1] ^ bits[2] ^ bits[3])
            brief = dict(zip(names[:dimension], bits))
            guide = '\n'.join(f'{n}: false = {w[0]}; true = {w[1]}.' for n, w in zip(names[:dimension], words))
            facts = '; '.join(f'{n}: {w[int(brief[n])]}' for n, w in zip(names[:dimension], words))
            rows.append({'id': f'neutral-{dimension}-{2200+i}', 'dimensions': dimension, 'brief': brief,
                'messages': interface(list(brief), f'Display unit {2200+i}: {facts}.', guide,
                                      '\n'.join(f'{n}: Is the unit {words[j][1]} rather than {words[j][0]}?'
                                                for j, n in enumerate(brief)))})
    return rows

def build():
    plan = {
        'kind': 'ainglish.field-scoped-reader-diagnostic.v1', 'governance_evidence': False,
        'snapshot': '/home/dexagon/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28',
        'transport': 'native offline HF, GPU0 only, NF4 double quantization, BF16, greedy; inherited runtime seed 20260906',
        'dimensions': [1, 2, 5], 'controls_per_dimension': 16, 'minimum_correct': 14,
        'control_truncations_allowed': 0, 'output_cap': 256, 'prompt_cap': 4096,
        'qualification': 'Run all 48 neutral controls before any language target. Each dimension independently needs >=14/16 exact, non-truncated answers and zero control truncations. Only qualifying dimensions proceed. No repeats or reader substitutions.',
        'interface': 'Only requested fields appear in guide, questions and system output schema. Strict boolean JSON with one optional JSON fence; missing, extra and duplicate keys refused.',
        'targets': 'All previously published communication-diagnostics-2026-09-06 reference cases for qualifying dimensions, both arms in fixed order. No writers, adapter training or operations in this study.',
        'analysis': 'Exact joint accuracy, parse rate and truncation count by dimension, language and context. Qualification failures are shown separately, never counted as zero target accuracy. No pooled advantage claim or independent-sample confidence interval.',
        'limits': ['New prospective prompt and neutral screen; earlier failures remain unchanged.',
            'Previously exposed synthetic reference cases, not an independent holdout or governance replication.',
            'Both language guides are supplied. Current-tokenizer counts do not predict future training or tokenization.',
            'One cached model/configuration, three authored templates; repeated bit patterns are not independent humans.'],
    }
    save_new(ROOT / 'PLAN.json', plan)
    save_new(ROOT / 'controls.json', controls())
    paths = ['study.py', 'test_study.py', 'PLAN.json', 'controls.json',
             '../communication-diagnostics-2026-09-06/cases.json',
             '../communication-diagnostics-2026-09-06/design.py',
             '../communication-diagnostics-2026-09-06/source-constructs.json',
             '../overnight-runtime-2026-09-06/runtime.py']
    save_new(ROOT / 'FROZEN.json', {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})

def run(resume=False):
    commit = verify_freeze(ROOT)
    plan = json.loads((ROOT / 'PLAN.json').read_text())
    neutral = json.loads((ROOT / 'controls.json').read_text())
    cases = json.loads((ROOT.parent / 'communication-diagnostics-2026-09-06/cases.json').read_text())
    with Journal(ROOT / 'execution/calls.jsonl', {'freeze': commit, **plan}, resume=resume) as journal:
        reader = LocalReader(plan['snapshot'])
        if not (ROOT / 'execution/provenance.json').exists():
            save_new(ROOT / 'execution/provenance.json', reader.provenance)
        checks = defaultdict(list)
        for c in neutral:
            r = reader.call(journal, 'qualification/' + c['id'], c['messages'], cap=plan['output_cap'])
            checks[c['dimensions']].append({'id': c['id'], 'correct': r['ended'] and decode(r['raw'], c['brief']) == c['brief'],
                                            'parsed': decode(r['raw'], c['brief']) is not None, 'ended': r['ended']})
        qualified = {d: sum(c['correct'] for c in rows) >= plan['minimum_correct'] and all(c['ended'] for c in rows)
                     for d, rows in checks.items()}
        if not (ROOT / 'execution/qualification.json').exists():
            save_new(ROOT / 'execution/qualification.json', {'checks': checks, 'qualified': qualified,
                                                           'target_calls_before_qualification': 0})
        print('Qualification', {d: (sum(c['correct'] for c in rows), qualified[d]) for d, rows in checks.items()}, flush=True)
        results = []
        for c in cases:
            if not qualified[c['dimensions']]:
                continue
            for arm in ['ainglish', 'english']:
                r = reader.call(journal, 'target/' + c['id'] + '/' + arm,
                                reader_messages(c, arm, c['messages'][arm]), cap=plan['output_cap'])
                decoded = decode(r['raw'], c['brief'])
                results.append({'id': c['id'], 'dimensions': c['dimensions'], 'arm': arm,
                    'context': c['id'].split('/')[0], 'parsed': decoded is not None,
                    'correct': r['ended'] and decoded == c['brief'], 'truncated': not r['ended'],
                    'input_tokens': r['input_tokens'], 'output_tokens': r['output_tokens']})
                if len(results) % 24 == 0:
                    print('Targets', len(results), flush=True)
        groups = defaultdict(list)
        for r in results:
            groups[(r['dimensions'], r['arm'], r['context'])].append(r)
        summaries = [{'dimensions': d, 'arm': a, 'context': c, 'n': len(rows),
            **{k: sum(r[k] for r in rows) for k in ['correct', 'parsed', 'truncated', 'input_tokens', 'output_tokens']}}
            for (d, a, c), rows in groups.items()]
        save_new(ROOT / 'RESULTS.json', {'freeze': commit, 'governance_evidence': False, 'qualified': qualified,
            'control_calls': len(neutral), 'target_calls': len(results), 'targets': results,
            'summaries': summaries, 'limits': plan['limits']})
        print(json.dumps(summaries, indent=2), flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('action', choices=['build', 'run']); p.add_argument('--resume', action='store_true')
    args = p.parse_args()
    build() if args.action == 'build' else run(args.resume)
