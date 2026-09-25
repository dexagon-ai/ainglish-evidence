"""Offline audit of an unchanged public raw record; no inference or governance writes.

Does not execute the archived author's code or attest that historical HTTP calls
really happened. It checks internal consistency against the frozen and served record.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket

from ainglish import panel
from ainglish.client import manifest_commitment

ROOT = Path(__file__).resolve().parent
RAW_SHA = '325a160371809737671d3070424984c04b11a42ebbcc2c94cd157baa49924f2b'
SOURCE = 'e47e7f73745b8d74c253ec83c5ac14657e34dcc612346c169ce90e6e079b8f72'


def forbidden_network(*args, **kwargs):
    raise AssertionError('This audit must remain offline')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def prompt(text, question, options):
    choices = '\n'.join(f'{chr(65+i)}: {v}' for i, v in enumerate(options))
    return (f'Read this message written by one agent to another:\n\n---\n{text}\n---\n\n'
            f'Question: {question}\nChoices:\n{choices}\n'
            'Answer with EXACTLY one choice code and nothing else.')


def parse_call(raw, reader, text, question, options):
    req, resp = raw['request_body'], raw['response']
    assert 'exception' not in raw
    assert req['model'] == resp['model'] == reader['model']
    assert req['messages'] == [{'role': 'user', 'content': prompt(text, question, options)}]
    for field in ('max_tokens', 'seed', 'temperature', 'top_p'):
        assert req[field] == reader[field], field
    assert len(resp['choices']) == 1
    answer = resp['choices'][0]
    assert answer['finish_reason'] == 'stop'
    code = answer['message']['content'].strip().upper()
    assert code in ('A', 'B')
    return options[ord(code) - 65]


def check_order(records):
    assert [r['sequence'] for r in records] == list(range(1, len(records)+1))
    for i, row in enumerate(records):
        assert row['started_at'] <= row['finished_at']
        if i:
            assert records[i-1]['finished_at'] <= row['started_at']


def main():
    socket.socket = forbidden_network
    socket.create_connection = forbidden_network
    raw = (ROOT/'overslip-raw-recovered.json').read_bytes()
    assert len(raw) == 456074 and hashlib.sha256(raw).hexdigest() == RAW_SHA
    archive = json.loads(raw)
    live = json.loads((ROOT/'overslip-source-live.json').read_bytes())
    result, frozen = archive['measurement'], archive['frozen_design']
    manifest = frozen['manifest']
    assert manifest_commitment(result['manifest']) == SOURCE == live['manifest_hash']
    assert result['manifest'] == live['manifest']
    assert result['attempt_id'] == live['attempt_id'] == archive['attempt_id']
    assert archive['attempt_pin'] == live['attempt']['pin']
    assert digest(manifest['items']) == result['manifest']['items_sha256']
    items = {r['id']: r for r in manifest['items']}
    assert len(items) == len(manifest['items']) == 72
    readers = {r['name']: r for r in manifest['panel']}
    assert len(readers) == 2
    scientific = archive['scientific_cells']['rows']
    calibration = archive['calibration_cells']['rows']
    assert len(scientific) == 128 and len(calibration) == 32
    rows = calibration + scientific
    assert len(rows) == len(archive['panel_http']) == 160
    seen = set()
    counts = defaultdict(Counter)
    for row, http in zip(rows, archive['panel_http'], strict=True):
        ident = (row['item_id'], row['reader'], row['arm'])
        assert ident not in seen
        seen.add(ident)
        item, reader = items[row['item_id']], readers[row['reader']]
        answer = parse_call(http, reader, item[row['arm']], item['question'], item['options'])
        assert answer == row['answer'] and row['expected'] == item['answer']
        assert row['correct'] == (answer == item['answer'])
        if not item.get('calibration'):
            assert row['arm'] == panel.arm_for(manifest['seed'], row['reader'], item['id'])
            assert item['answer'] == ('yes' if item['settlement_stratum']=='accidental' else 'no')
            assert item['english'].replace('an unintentional omission', 'an overslip') == item['ainglish']
            counts[(item['settlement_stratum'], row['reader'], row['arm'])].update(
                n=1, correct=int(row['correct']))
    expected_cells = {(i['id'], name, arm) for i in items.values() for name in readers
                      for arm in (('english','ainglish') if i.get('calibration')
                                  else (panel.arm_for(manifest['seed'],name,i['id']),))}
    assert seen == expected_cells
    assert len(archive['qualification_http']) == 48
    q = 0
    for screen, result_q in zip(frozen['screens'], archive['qualification_results'], strict=True):
        reader = screen['reader']
        observations = result_q['observations']
        assert len(observations) == 24 and len(screen['controls']) == 12
        cq = Counter()
        for i, control in enumerate(screen['controls']):
            for j, arm in enumerate(('detectable', 'other')):
                http, obs = archive['qualification_http'][q], observations[2*i+j]
                q += 1
                answer = parse_call(http, reader, control[arm], control['question'], control['options'])
                assert obs['control_id'] == control['id'] and obs['cell'] == arm
                assert answer == obs['answer'] and obs['expected'] == control['answer']
                assert obs['correct'] == (answer == control['answer'])
                cq[arm] += int(obs['correct'])
        receipt = result_q['receipt']
        assert cq == Counter(detectable=12, other=0)
        assert receipt in result['manifest']['reader_qualifications']
        assert receipt['result']['detectable_correct'] == cq['detectable']
        assert receipt['result']['other_correct'] == cq['other']
        assert receipt['qualified_at'] <= archive['panel_http'][0]['started_at'] < receipt['valid_until']
    assert q == 48
    check_order(archive['qualification_http'])
    check_order(archive['panel_http'])
    assert archive['qualification_http'][-1]['finished_at'] <= archive['panel_http'][0]['started_at']
    for name in readers:
        cells = [r for r in calibration if r['reader']==name]
        assert len(cells) == 16
        assert all(r['correct'] == (r['arm']=='ainglish') for r in cells)
        assert result['calibration']['by_reader'][name]['gap'] == 1
        assert result['calibration']['by_reader'][name]['recovered'] == 1
    real = [i for i in items.values() if not i.get('calibration')]
    scoring = [(r['item_id'], r['arm'], r['reader'], r['answer']) for r in scientific]
    contract = panel._settlement_contract(manifest, real, manifest['panel'], manifest['seed'])
    value, arms, strata = panel._stratified_accuracy(scoring, real, contract)
    lo, hi, att = panel.attested_bootstrap_accuracy(scoring, real, manifest['panel'],
                                                 contract=contract, seed=manifest['seed'])
    assert (value, arms, strata) == (result['value'], result['arms'], result['stratum_results'])
    assert (value, panel._register_round(lo, 4), panel._register_round(hi, 4)) == (
        live['value'], live['value_lo'], live['value_hi'])
    assert att == live['interval_provenance_attestation'] == result['interval_provenance']
    report = {
        'kind': 'dexagon.overslip-recovered-raw-audit.v1',
        'at': datetime.now(timezone.utc).isoformat(),
        'sdk_version': importlib.metadata.version('ainglish'),
        'raw_archive_sha256': RAW_SHA, 'raw_archive_bytes': len(raw),
        'source_manifest_hash': SOURCE, 'new_inference_calls': 0,
        'archived_author_code_executed': False, 'network_disabled_during_audit': True,
        'checks': ['unchanged archive digest', 'frozen item digest', 'server manifest and attempt pin',
                   '208 rendered requests and raw answers against saved parsed cells',
                   'model names, request settings, stopping and recorded chronological order',
                   'complete allocated target/control cell inventory with no duplicate cells',
                   'qualification and calibration answers', '64 keys and exact arm substitution',
                   'official stratified estimator and 2000-draw item bootstrap journal'],
        'qualification_calls_replayed': 48, 'panel_controls_replayed': 32,
        'scientific_calls_replayed': 128, 'value': value, 'interval': [lo,hi],
        'counts': [{'key': list(k), **v} for k,v in sorted(counts.items())],
        'served_settlement_state': live['settlement_state'],
        'served_confirmed': live['confirmed'],
        'limits': [
            'Internal archival consistency, not independent proof of historical execution.',
            'Not a disjoint replication, new measurement, confirmation or retraction.',
            'The replica raw HTTP archive remains unavailable to this audit.',
            'Question wording differs between studies alongside domain/context changes; causal attribution unresolved.',
            'Related cases and shared model training limit independence; bootstrap is item-level, not domain-clustered.',
            'Current unglossed cached-reader performance does not predict future training or tokenizer effects.',
        ],
    }
    (ROOT/'overslip-raw-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
