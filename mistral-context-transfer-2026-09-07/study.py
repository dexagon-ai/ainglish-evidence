"""Fresh contextual reader/writer study with guarded real disposable operations."""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import re
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'overnight-runtime-2026-09-06'))
from runtime import Journal, disk_guard, save_new, verify_freeze
scoped_spec = importlib.util.spec_from_file_location('scoped_reader_interface', ROOT.parent / 'field-scoped-communication-2026-09-07/study.py')
scoped = importlib.util.module_from_spec(scoped_spec)
scoped_spec.loader.exec_module(scoped)
decode, scoped_controls, reader_messages = scoped.decode, scoped.controls, scoped.reader_messages
sys.path.insert(0, str(ROOT.parent / 'communication-diagnostics-2026-09-06'))
from design import FIELDS, PREFIXES, PHRASES, render, sender_messages
sys.path.insert(0, str(ROOT.parent / 'disposable-task-benchmark-2026-09-07'))
from executor import execute, follows_intended_plan, success

MODEL = 'mistral-small3.2:24b-instruct-2506-q4_K_M'
DIGEST = '5a408ab55df5c1b5cf46533c368813b30bf9e4d8fc39263bf2a3338cfa3b895b'
OPTIONS = {'num_gpu': 0, 'num_thread': 8, 'num_ctx': 8192, 'num_predict': 512,
           'temperature': 0, 'seed': 20260907}
CONTEXTS = [
    ('archive', 'You are Mira, coordinating archive conservation with Noor and Ivo. The named check is inspecting the humidity log. A note attributed to a visitor concerns tomorrow\'s separate archive project, not this authorized plan.'),
    ('waterlab', 'You are Mira, scheduling a water-testing laboratory handover with Noor and Ivo. The named check is checking the sample seals. A worksheet marked DRAFT has not been accepted and gives no instructions for this handover.'),
    ('theatre', 'You are Mira, helping Noor and Ivo prepare a theatre wardrobe loan. The named check is checking the costume inventory. An archived rehearsal memo refers to last month\'s team, not the acting team specified in the current message.'),
]

def api(path, body=None):
    request = urllib.request.Request('http://127.0.0.1:11434/api/' + path,
        data=None if body is None else json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)

def available_ram():
    return next(int(line.split()[1]) * 1024 for line in Path('/proc/meminfo').read_text().splitlines()
                if line.startswith('MemAvailable:'))

def writer_controls():
    labels = ['Handling', 'Surface', 'Label', 'Battery', 'Shape']
    names = ['fragile', 'waterproof', 'labelled', 'charged', 'folded']
    words = [('robust', 'fragile'), ('absorbent', 'waterproof'), ('unlabelled', 'labelled'),
             ('empty', 'charged'), ('flat', 'folded')]
    rows = []
    for i in range(16):
        bits = [bool(i & (1 << j)) for j in range(4)]
        bits.append(bits[0] ^ bits[1] ^ bits[2] ^ bits[3])
        brief = dict(zip(names, bits))
        table = '\n'.join(f'{label}: choose "{word[0]}" when {name} is false, "{word[1]}" when true.'
                          for label, name, word in zip(labels, names, words))
        gold = '\n'.join(f'{label}: {word[int(bit)]}.' for label, word, bit in zip(labels, words, bits))
        rows.append({'id': f'parcel-writer-{3100+i}', 'brief': brief, 'gold': gold,
            'messages': [{'role': 'system', 'content': 'Write exactly five labelled lines from the permitted table. '
                         'No JSON, explanation, quotations or Markdown. One optional terminal full stop per line is accepted.'},
                         {'role': 'user', 'content': table + '\nIntended values:\n' + json.dumps(brief)}]})
    return rows

def fixed_lines(raw):
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    return [line[:-1].rstrip().casefold() if line.endswith('.') else line.casefold() for line in lines]

def parse_writer(raw, arm):
    expected = {f'{label}: {options[int(value)]}'.casefold(): (field, value)
                for field, label, options in zip(FIELDS, PREFIXES, PHRASES[arm]) for value in [False, True]}
    result = {}
    for line in fixed_lines(raw):
        selected = expected.get(line)
        if selected is None or selected[0] in result:
            return None
        result[selected[0]] = selected[1]
    return result if set(result) == set(FIELDS) else None

def cases():
    rows = []
    for name, context in CONTEXTS:
        for bits in product([False, True], repeat=5):
            brief = dict(zip(FIELDS, bits))
            opposite = {k: not v for k, v in brief.items()}
            # A different, explicitly inactive scope; the same complete foil is seen by both arms.
            foil = 'Irrelevant archived or unaccepted note (not the current plan):\n' + render(opposite, 'english')
            rows.append({'id': name + '/' + ''.join(str(int(v)) for v in bits), 'dimensions': 5,
                         'context': context + '\n' + foil + '\nOnly the CURRENT authoritative message below determines the five answers.',
                         'brief': brief, 'messages': {arm: render(brief, arm) for arm in PHRASES}})
    return rows

def build():
    plan = {'kind': 'ainglish.mistral-context-transfer.v1', 'governance_evidence': False,
        'model': MODEL, 'digest': DIGEST, 'options': OPTIONS, 'reader_controls': 16, 'writer_controls': 16,
        'neutral_gate': 'Each role separately needs >=14/16 exact correct, zero truncated controls. Reader controls are the target-independent five-field scoped screen, never prior target results. Writer control correctness uses exactly five ordinary labelled lines, optional one terminal period, case-insensitive.',
        'reference_gate': 'After a passing neutral reader screen, run all 192 reference calls. Both arms separately need >=80% exact joint accuracy and zero truncations. Sender/receiver and executor require this gate AND the separate neutral writer pass. A failed gate remains failed; do not substitute readers or samples.',
        'targets': '96 new five-bit cases in three new contexts with clearly inactive opposite-scope distractors. Both arms have full explicit guides. Within each arm the same model reads and writes; not independent agents.',
        'order': '32 neutral controls, then every eligible reference call, then conditional sender/handoff pairs in case and arm order. No outcome-selected retries.',
        'writer_parser': 'Exactly the five permitted labelled lines, case-insensitive, zero or one final period on each line; no fences, commentary, duplicate labels or semantic repairs.',
        'executor': 'Conditional reader outputs map only team inclusion, collective/individual work and start/complete deadline into three closed enums. Real hashing and generated review files in owned TemporaryDirectory; no shell, model-chosen paths or external effects. The clock is the executor\'s fixed simulator, not an assertion about real UTC compliance. Plan following and deadline success are separate.',
        'maximum_calls': 608, 'resources': 'Cached CPU-only Ollama, 8 threads, 8192 context, 512 output; verify size_vram=0, no service changes, model downloads or unrelated eviction. Stop on uncertain transport, unexpected model, or <3GiB RAM.',
        'analysis': 'All absolute accuracy/parse/truncation counts by role, arm and authored context. Compare receivers against both intended brief and parsed actual sender meaning. Report measured prompt_eval_count/eval_count and latency, not exact token IDs or invoiced charges.',
        'limits': ['Synthetic contextual stress test, not broad operational efficacy or human validation.',
                   'Public ratified forms, fully supplied guides; no cold-reading or future-tokenizer inference.',
                   'Three templates with 32 controlled combinations each are not 96 independent contexts.',
                   'Does not settle proposals or unlock earlier failed Qwen adapter-training gates.']}
    save_new(ROOT / 'PLAN.json', plan)
    save_new(ROOT / 'cases.json', cases())
    save_new(ROOT / 'controls.json', {'reader': [r for r in scoped_controls() if r['dimensions'] == 5], 'writer': writer_controls()})
    paths = ['study.py', 'test_study.py', 'PLAN.json', 'cases.json', 'controls.json',
             '../field-scoped-communication-2026-09-07/study.py', '../communication-diagnostics-2026-09-06/design.py',
             '../communication-diagnostics-2026-09-06/source-constructs.json',
             '../disposable-task-benchmark-2026-09-07/executor.py', '../overnight-runtime-2026-09-06/runtime.py']
    save_new(ROOT / 'FROZEN.json', {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})

def run():
    commit = verify_freeze(ROOT); plan = json.loads((ROOT / 'PLAN.json').read_text())
    neutral = json.loads((ROOT / 'controls.json').read_text()); targets = json.loads((ROOT / 'cases.json').read_text())
    if api('ps')['models']:
        raise RuntimeError('Shared service occupied; no eviction')
    tags = {m['name']: m for m in api('tags')['models']}
    if tags[MODEL]['digest'] != DIGEST or available_ram() < tags[MODEL]['size'] * 1.1 + 4 * 1024**3:
        raise RuntimeError('Cached model identity or RAM reserve unavailable')
    save_new(ROOT / 'execution/intent.json', {'freeze': commit, 'ollama_version': api('version'), 'target_calls_started': 0})
    with Journal(ROOT / 'execution/calls.jsonl', {'freeze': commit, **plan}) as journal:
        def call(key, messages):
            disk_guard()
            if available_ram() < 3 * 1024**3 or any(m['name'] != MODEL for m in api('ps')['models']):
                raise RuntimeError('Resource reserve or shared-caller conflict; no new spend')
            request = {'model': MODEL, 'messages': messages, 'stream': False, 'keep_alive': '5m', 'options': OPTIONS}
            journal.begin(key, request); started = time.monotonic()
            response = api('chat', request); resident = api('ps')['models']
            row = journal.end(key, {'raw': response['message']['content'], 'response': response,
                'resident_after': resident, 'latency_s': time.monotonic() - started})
            if not resident or any(m['name'] == MODEL and m.get('size_vram', -1) != 0 for m in resident):
                raise RuntimeError('CPU-only placement not verified; raw answer retained without retry')
            return row['raw'], response.get('done') is True and response.get('done_reason') == 'stop'
        checks = {}
        for role in ['reader', 'writer']:
            rows = []
            for c in neutral[role]:
                raw, ended = call('qualification/' + role + '/' + c['id'], c['messages'])
                correct = decode(raw, c['brief']) == c['brief'] if role == 'reader' else fixed_lines(raw) == fixed_lines(c['gold'])
                rows.append({'id': c['id'], 'correct': ended and correct, 'truncated': not ended})
            checks[role] = {'passed': sum(r['correct'] for r in rows) >= 14 and not any(r['truncated'] for r in rows), 'rows': rows}
            print(role, sum(r['correct'] for r in rows), '/16', flush=True)
        save_new(ROOT / 'execution/qualification.json', checks)
        references = []; handoffs = []
        if checks['reader']['passed']:
            for c in targets:
                for arm in ['ainglish', 'english']:
                    raw, ended = call('reference/' + c['id'] + '/' + arm, reader_messages(c, arm, c['messages'][arm]))
                    parsed = decode(raw, c['brief'])
                    references.append({'id': c['id'], 'arm': arm, 'parsed': parsed is not None,
                                       'correct': ended and parsed == c['brief'], 'truncated': not ended})
                    if len(references) % 24 == 0:
                        print('References', len(references), '/192', flush=True)
        reference_gate = bool(references) and all(
            sum(r['correct'] for r in references if r['arm'] == arm) >= .8 * 96
            and not any(r['truncated'] for r in references if r['arm'] == arm) for arm in ['ainglish', 'english'])
        save_new(ROOT / 'execution/reference-gate.json', {'passed': reference_gate, 'references': references})
        if reference_gate and checks['writer']['passed']:
            def choice(brief):
                return {'team': 'include' if brief['include_recipient'] else 'exclude',
                        'work': 'one' if brief['collective'] else 'each',
                        'deadline': 'complete' if brief['finish_deadline'] else 'start'}
            for c in targets:
                fixture = json.dumps({'inventory': [{'case': c['id'], 'checked_item': 'bounded demonstration'}]}, sort_keys=True).encode()
                for arm in ['ainglish', 'english']:
                    messages = sender_messages(c, arm)
                    messages[0]['content'] += ' Use no more than one terminal full stop per line; no Markdown fences.'
                    raw, writer_ended = call('sender/' + c['id'] + '/' + arm, messages)
                    sender = parse_writer(raw, arm)
                    reply, ended = call('handoff/' + c['id'] + '/' + arm, reader_messages(c, arm, raw))
                    received = decode(reply, c['brief'])
                    row = {'id': c['id'], 'arm': arm, 'sender_parsed': sender is not None,
                        'sender_correct': writer_ended and sender == c['brief'], 'sender_truncated': not writer_ended,
                        'receiver_parsed': received is not None, 'receiver_correct': ended and received == c['brief'],
                        'receiver_tracks_sender': None if sender is None else ended and received == sender,
                        'receiver_truncated': not ended, 'execution': None}
                    if writer_ended and ended and received is not None:
                        receipt = execute(choice(received), fixture, instrument_qualified=True)
                        row['execution'] = {'receipt': receipt, 'follows_intended_plan': follows_intended_plan(receipt, choice(c['brief'])),
                                            'task_success': success(receipt, choice(c['brief']), fixture)}
                    handoffs.append(row)
                    if len(handoffs) % 24 == 0:
                        print('Handoffs', len(handoffs), '/192', flush=True)
        save_new(ROOT / 'RESULTS.json', {'freeze': commit, 'governance_evidence': False, 'qualification': checks,
            'reference_gate': reference_gate, 'references': references, 'handoffs': handoffs, 'limits': plan['limits']})
    loaded = api('ps')['models']
    if loaded and all(m['name'] == MODEL for m in loaded):
        api('generate', {'model': MODEL, 'keep_alive': 0})
    print('Finished', len(references), 'references;', len(handoffs), 'handoffs', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['build', 'run']); args = parser.parse_args()
    build() if args.action == 'build' else run()
