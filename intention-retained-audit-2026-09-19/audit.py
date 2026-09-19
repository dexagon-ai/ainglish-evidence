"""Offline audit of existing public post-parser answers. Never inference or submission."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'intention-reader-review-2026-09-18'
INDEX_SHA = 'acdbca8e07c77a3a0b51ea6bb2ca6b34e196f9b1119b2afb4b319fca82ee76db'


def load_checked(path, sha, size=None):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == sha, path.name
    assert size is None or len(raw) == size, path.name
    return json.loads(raw)


def audit_rows(bank, measurement, scientific, calibration):
    items = {item['id']: item for item in bank['items']}
    readers = [reader['name'] for reader in measurement['manifest']['readers']]
    assert len(readers) == len(set(readers)) == 2
    journal_rows = measurement['interval_provenance_attestation']['cells']
    journal = {(row['item_id'], row['reader'], row['arm']): row['correct'] for row in journal_rows}
    assert len(journal_rows) == len(journal) == 192
    assert len(scientific) == 192 and len(calibration) == 48
    expected_scientific = set()
    expected_calibration = set()
    for item in items.values():
        for reader in readers:
            if item.get('calibration'):
                expected_calibration.update((item['id'], reader, arm) for arm in ('english', 'ainglish'))
            else:
                first = hashlib.sha256(f"{measurement['manifest']['seed']}|{reader}|{item['id']}".encode()).digest()[0]
                expected_scientific.add((item['id'], reader, 'ainglish' if first % 2 else 'english'))
    key = lambda row: (row['item_id'], row['reader'], row['arm'])
    assert {key(row) for row in scientific} == expected_scientific == set(journal)
    assert {key(row) for row in calibration} == expected_calibration
    for row in scientific + calibration:
        item = items[row['item_id']]
        assert row['expected'] == item['answer']
        assert row['answer'] in item['options']
        assert type(row['correct']) is bool
        assert row['correct'] is (row['answer'] == row['expected'])
    assert all(row['correct'] is journal[key(row)] for row in scientific)
    errors = [row for row in scientific if not row['correct']]
    error_answers = Counter(row['answer'] for row in errors)
    assert error_answers == {'no': 41, 'cannot-tell': 1}
    assert {row['reader'] for row in errors} == {'gemma3-12b-opaque-choice-q4_k_m'}
    assert {items[row['item_id']]['settlement_stratum'] for row in errors} == {'on-purpose-plan-match'}
    groups = defaultdict(list)
    for row in scientific:
        groups[items[row['item_id']]['settlement_stratum']].append(row)
    strata = {name: {arm: {'correct': sum(row['correct'] for row in rows if row['arm'] == arm),
                                'total': sum(row['arm'] == arm for row in rows)}
                    for arm in ('english', 'ainglish')} for name, rows in sorted(groups.items())}
    return {
        'kind': 'dexagon.retained-parsed-answer-audit.v1',
        'status': 'retrieval_closed_with_raw_response_limit',
        'measurement': measurement['manifest_hash'],
        'scientific_cells_checked': 192, 'calibration_cells_checked': 48,
        'scientific_correct': sum(row['correct'] for row in scientific),
        'calibration_correct': sum(row['correct'] for row in calibration),
        'wrong_scientific_answers': dict(error_answers), 'strata': strata,
        'all_retained_labels_in_options': True, 'all_retained_grades_match_expected': True,
        'all_scientific_cells_match_filed_boolean_journal': True,
        'demonstrated_grading_error': False,
        'preparser_raw_available': False, 'raw_qualification_responses_available': False,
        'independent_inference': False, 'measurement_rewritten': False,
        'reader_calls': 0, 'attempts': 0, 'measurements': 0,
        'scope': 'Post-parser consistency only; not authentication of lost raw bytes, clean-instrument certification, new inference, regrading or independent confirmation.',
    }


def audit():
    index = load_checked(ROOT / 'source-index.json', INDEX_SHA)
    for key in ['raw_scientific_response_bytes_retained', 'raw_calibration_response_bytes_retained',
                'raw_qualification_response_bytes_retained']:
        assert index['retention_boundary'][key] is False
    sets = []
    for name in ('scientific_cells', 'calibration_cells'):
        ref = index['retained_artifacts'][name]
        sets.append(load_checked(ROOT / (name + '.json'), ref['sha256'], ref['bytes'])['rows'])
    bank = json.loads((SOURCE / 'items.json').read_text())
    canonical = json.dumps(bank['items'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    assert hashlib.sha256(canonical).hexdigest() == index['frozen_inputs']['items_sha256']
    measurement = json.loads((SOURCE / 'measurement.json').read_text())
    assert measurement['manifest_hash'] == index['measurement_manifest_hash']
    result = audit_rows(bank, measurement, *sets)
    result['source_index_sha256'] = INDEX_SHA
    return result


if __name__ == '__main__':
    result = audit()
    (ROOT / 'audit-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
