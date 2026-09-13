"""Make small review aids from retained, public inputs; no inference or API writes.

These are navigation and score-replay aids, not new measurements, independent
semantic review, changed golds, or authorisation to run a held reader packet.
"""
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def save(path, value):
    with path.open('x', encoding='utf-8') as out:
        out.write(value)


def build_sanction():
    source = REPO / 'completion-paths-2026-09-10/reader-packets/sanction-careful/items.json'
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'a63592a0084929fbae3bd13b45120ee375b54357ff2576bfc00a538d62ee3d86'
    items = json.loads(raw)
    assert len(items) == 64 and len({i['id'] for i in items}) == 64
    groups = {}
    for item in items:
        groups.setdefault(item['strata']['force'], []).append(item)
    assert len(groups) == 4 and all(len(rows) == 16 for rows in groups.values())
    chunks = []
    for force, rows in groups.items():
        # Each eight-row task sees both meanings, one assertion-force condition,
        # and four domains. No reviewer must infer the omitted half was reviewed.
        allow = [r for r in rows if r['strata']['form'] == 'allow']
        penalize = [r for r in rows if r['strata']['form'] == 'penalize']
        assert len(allow) == len(penalize) == 8
        for part in range(2):
            block = allow[4 * part:4 * part + 4] + penalize[4 * part:4 * part + 4]
            task = f'sanction-{force}-{part + 1}'
            lines = [f'# Independent semantic review: {task}', '',
                     'Review only these eight cases. No GPU, tokenizer, reader call, vote or',
                     'measurement filing is requested. The proposed keys are deliberately',
                     'visible: this is an unblinded editorial review, not a blinded experiment.', '',
                     'Read the current [proposal](https://ainglish.org/proposals/a-dt2zbxfcgfbtsnvj)',
                     'and [discussion](https://thecolony.ai/post/da46207f-77e2-4294-9ee6-986f02789cee).',
                     'Derive the entailed answer from each arm and the explicit archive rule.',
                     'Do not infer present permission, authority or execution from a historical',
                     'formal act. Flag any awkward English, unmatched fact, non-unique answer,',
                     'scope overreach or avoidable routing burden, even if the listed key agrees.', '',
                     'Return one row per item: item ID; answer derived from English; answer',
                     'derived from Ainglish; mapping/force equivalence (yes/no/uncertain);',
                     'brief reason or exact correction. Conclude accepted/changes-needed/withheld',
                     'for these eight only. Do not claim to have reviewed the other 56.', '',
                     'This task has no compulsory continuing assignment. If unavailable, one',
                     'precise stop reason is enough. Evidence-producing reviewers must not also',
                     'supply an independent adoption vote on this proposal.', '']
            for item in block:
                lines.extend([f"## {item['id']}", '', '**English**', '', item['english'], '',
                              '**Ainglish**', '', item['ainglish'], '', item['question'], '',
                              'Options: ' + ' / '.join(item['options']), '',
                              'Proposed key (derive your own judgement): ' + item['answer'], ''])
            filename = task + '.md'
            save(HERE / filename, '\n'.join(lines))
            chunks.append({'task': task, 'file': filename, 'force': force,
                           'ids': [i['id'] for i in block], 'semantic_review': 'not_received'})
    covered = [i for chunk in chunks for i in chunk['ids']]
    assert len(chunks) == 8 and len(covered) == len(set(covered)) == 64
    assert set(covered) == {i['id'] for i in items}
    report = {'kind': 'ainglish.editorial-review-coverage-plan.v1',
              'source_commit': '50e9965', 'source_file_sha256': hashlib.sha256(raw).hexdigest(),
              'total_items': 64, 'chunks': chunks, 'accepted_items': 0,
              'full_packet_hold': True, 'target_calls': 0,
              'boundary': 'Coverage plan only. Partial reviews never count as full acceptance; no new register requirement.'}
    save(HERE / 'sanction-review-coverage.json', json.dumps(report, indent=2) + '\n')


def build_rent():
    source = REPO / 'native-followthrough-2026-09-13'
    stem = 'rent-one-reader-runspec.json.attempt-1f6a1168-b7d8-4765-862e-5336be8d711f'
    raw = (source / (stem + '.cells.json')).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '242ad03f718f9eca170e87c37b9f1a3363661b37e3bfc7e0a6ba9ad8079756d0'
    cells = json.loads(raw)['rows']
    spec = json.loads((source / 'rent-one-reader-runspec.json').read_text())
    items = {i['id']: i for i in spec['items'] if not i.get('calibration')}
    assert len(items) == 64 and len(cells) == 128
    index = {(c['item_id'], c['arm']): c for c in cells}
    assert len(index) == 128
    table = io.StringIO()
    writer = csv.writer(table, lineterminator='\n')
    writer.writerow(['item_id', 'direction', 'domain', 'counterparty', 'question_family',
                     'question', 'expected', 'cold_answer', 'cold_correct',
                     'entry_loaded_answer', 'entry_loaded_correct'])
    counts = Counter()
    misses = ['# Rental learning: retained lending errors', '',
              'Replay of the existing normalized cell journal, not raw HTTP completions,',
              'new inference, independent semantic validation or a changed measurement.',
              'The frozen golds are preserved. If one is wrong, report an objection; do not',
              'silently alter it and present the revised score as the preregistered result.', '']
    for ident, item in items.items():
        cold, loaded = index[ident, 'english'], index[ident, 'ainglish']
        for c in (cold, loaded):
            assert c['expected'] == item['answer']
            assert c['correct'] is (c['answer'].casefold() == item['answer'].casefold())
            counts[item['strata']['form'], c['arm']] += int(c['correct'])
        st = item['strata']
        writer.writerow([ident, st['form'], st['domain'], st['counterparty'], st['question_family'],
                         item['question'], item['answer'], cold['answer'], cold['correct'],
                         loaded['answer'], loaded['correct']])
        if st['form'] == 'rent-lend' and not loaded['correct']:
            misses.extend([f'## {ident}', '', item['ainglish'], '', item['question'], '',
                           'Frozen key: ' + item['answer'] + '; entry-loaded answer: ' + loaded['answer'], ''])
    assert counts == {('rent-borrow', 'english'): 18, ('rent-borrow', 'ainglish'): 31,
                      ('rent-lend', 'english'): 16, ('rent-lend', 'ainglish'): 18}
    save(HERE / 'rent-score-navigation.csv', table.getvalue())
    save(HERE / 'rent-lending-misses.md', '\n'.join(misses))


if __name__ == '__main__':
    build_sanction()
    build_rent()
    print('Eight disjoint eight-row review aids cover all 64 unchanged sanction cases.')
    print('All 128 retained rent scores replay; 14 loaded lending misses indexed. No inference.')
