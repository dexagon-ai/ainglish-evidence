"""Finite target-independent control development/validation, never a target rerun."""
from collections import Counter
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from unittest.mock import patch

from ainglish import panel
from ainglish.reader_qualification import run_screen, validate_screen

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / 'postdeploy-wave-2026-09-05'
READERS = ('mistral', 'gemma')


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def save(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write('\n')


def controls(prefix, count):
    assert count % 12 == 0
    rows, truth = [], {}
    # Every (known-answer position, other-answer position) pair occurs once per
    # twelve rows. Candidate rank in the stated list varies independently.
    positions = [(a, b) for a in range(4) for b in range(4) if a != b]
    for i in range(count):
        names = [f'{prefix}-person-{i}-{letter}' for letter in 'KLM']
        holder = names[(i // 4 + i % 3) % 3]
        shown = names[i % 3:] + names[:i % 3]
        known_pos, unknown_pos = positions[i % 12]
        meanings = [None] * 4
        meanings[known_pos] = holder
        meanings[unknown_pos] = 'not determined from the record'
        remaining = iter(n for n in names if n != holder)
        meanings = [next(remaining) if x is None else x for x in meanings]
        label = f'parcel {prefix}-{i}'
        common = f'Exactly one of {", ".join(shown)} holds {label}. '
        row = {
            'id': f'{prefix}-{i}',
            'detectable': common + f'The record identifies {holder} as its holder.',
            'other': common + 'The record does not identify its holder.',
            'question': f'Who holds {label}, according to this record? ' +
                ' '.join(f'{letter} = {meaning}.' for letter, meaning in zip('ABCD', meanings)),
            'options': list('ABCD'), 'answer': 'ABCD'[known_pos],
        }
        rows.append(row)
        truth[row['id']] = {'detectable': 'ABCD'[known_pos], 'other': 'ABCD'[unknown_pos]}
    assert len(set(r['id'] for r in rows)) == count
    assert set(Counter(r['answer'] for r in rows).values()) == {count // 4}
    assert set(Counter(t['other'] for t in truth.values()).values()) == {count // 4}
    return rows, truth


def build():
    for stage, count in [('development', 12), ('validation', 24)]:
        rows, truth = controls('overnight-' + stage, count)
        save(f'instrument/{stage}.truth.json', truth)
        for name in READERS:
            screen = json.loads((PRIOR / 'qualification' / f'{name}-screen.json').read_text())
            screen.update(controls=rows, min_gap_bps=5000, min_recovered_bps=9500)
            validate_screen(screen)
            save(f'instrument/{stage}.{name}.screen.json', screen)
    save('instrument/design.json', {
        'kind': 'ainglish.instrument-development.overnight.v1',
        'created_at': now(), 'configurations_per_reader': 1,
        'reader_settings': 'Unchanged digest-bound local Mistral Small 3.2 24B Q4 and Gemma 3 12B Q4; max_tokens=64, seed=2026090581, temperature=0.',
        'change': 'Control includes an honest not-determined option, not an instruction to guess. Known and unknown answer positions independently balanced over all distinct position pairs.',
        'order': ['12 development controls per reader', '24 untouched validation controls per reader'],
        'max_calls': 144, 'retries': 0,
        'gates': ['Each reader passes SDK >=.5 planted-key gap and >=.95 recovery.',
                  'Each reader has >=.95 semantic accuracy separately on explicit and under-specified arms.',
                  'Zero off-option, absent, truncated or transport-fault outputs.',
                  'Any development failure prevents validation. Any validation failure prevents target studies. No second configuration in this batch.'],
        'interpretation': 'SDK other_correct counts matches to the planted key, NOT semantic accuracy of the information-absent arm. That arm has its own independently specified not-determined key and semantic accuracy is reported separately.',
        'prior_failures': 'Earlier studies and the forced-guess control abort remain final. No rescoring, deletion or replacement of prior observations.',
        'target_exposure': 'These controls contain no Ainglish target constructs. Screens are not language-performance measurements.'
    })
    print('Frozen one configuration, 144-call maximum, separate development and validation.', flush=True)


def resources_free(readers):
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=10) as response:
        loaded = json.load(response)['models']
    allowed = {r['model'] for r in readers}
    if any(m.get('name', m.get('model')) not in allowed for m in loaded):
        raise RuntimeError('Unrelated loaded inference workload; no mint or reader spend')
    # Do not terminate/evict any job. Existing reader weights need no download.
    return [m.get('name', m.get('model')) for m in loaded]


def run(commit):
    for path in sorted((ROOT / 'instrument').glob('*screen.json')):
        stored = subprocess.run(['git', 'show', f'{commit}:{ROOT.name}/{path.relative_to(ROOT)}'],
                                cwd=ROOT.parent, check=True, capture_output=True).stdout
        assert stored == path.read_bytes(), 'Published screen bytes changed'
    readers = [json.loads((ROOT / 'instrument' / f'development.{n}.screen.json').read_text())['reader'] for n in READERS]
    resources_free(readers)
    save('instrument/started.json', {'at': now(), 'commit': commit, 'pid': os.getpid(), 'retries': 0})
    summaries = []
    for stage in ('development', 'validation'):
        for name in READERS:
            resources_free(readers)
            screen = json.loads((ROOT / 'instrument' / f'{stage}.{name}.screen.json').read_text())
            truth = json.loads((ROOT / 'instrument' / f'{stage}.truth.json').read_text())
            journal_path = ROOT / 'instrument' / f'{stage}.{name}.calls.jsonl'
            original_chat = panel.chat
            count = 0
            faults = []
            with journal_path.open('x') as journal:
                def chat(reader, prompt):
                    nonlocal count
                    started = time.monotonic()
                    record = {'at': now(), 'reader': name, 'stage': stage, 'ordinal': count}
                    try:
                        output, truncated = original_chat(reader, prompt)
                        record.update(raw_output=output, truncated=truncated)
                        if truncated or output.strip().upper() not in 'ABCD' or len(output.strip()) != 1:
                            faults.append(count)
                        return output, truncated
                    except BaseException as exc:
                        record['error_type'] = type(exc).__name__
                        faults.append(count)
                        raise
                    finally:
                        record['elapsed_seconds'] = round(time.monotonic() - started, 3)
                        journal.write(json.dumps(record) + '\n')
                        journal.flush(); os.fsync(journal.fileno())
                        count += 1
                        if count % 12 == 0:
                            print(stage, name, count, 'calls retained', flush=True)
                with patch.object(panel, 'chat', side_effect=chat):
                    result = run_screen(screen)
            save(f'instrument/{stage}.{name}.result.json', result)
            accuracy = {cell: sum(o['answer'] == truth[o['control_id']][cell]
                        for o in result['observations'] if o['cell'] == cell) / len(screen['controls'])
                        for cell in ('detectable', 'other')}
            passed = result['status'] == 'passed' and not faults and min(accuracy.values()) >= .95
            summary = {'stage': stage, 'reader': name, 'calls': count, 'sdk_status': result['status'],
                       'semantic_accuracy': accuracy, 'fault_ordinals': faults, 'admitted': passed}
            summaries.append(summary)
            save(f'instrument/{stage}.{name}.assessment.json', summary)
            print(json.dumps(summary), flush=True)
        if not all(x['admitted'] for x in summaries if x['stage'] == stage):
            save('instrument/finished.json', {'at': now(), 'state': 'stopped', 'summaries': summaries})
            return
    save('instrument/finished.json', {'at': now(), 'state': 'validated', 'summaries': summaries})


if __name__ == '__main__':
    {'build': build, 'run': lambda: run(sys.argv[2])}[sys.argv[1]]()
