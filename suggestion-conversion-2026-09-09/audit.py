"""Reproduce the descriptive bottleneck audit from a public-only frozen extract.

No model calls, credentials, suggestion-read tracking or behavioural inference.
`freeze PUBLIC_CAPTURE_DIR` builds the extract from SDK public responses; the
default action recomputes counts from the committed extract without networking.
"""
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ME = '52b1883a-464e-403c-9059-d57afe91a13c'
METRIC = 'comprehension_accuracy_delta'

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def write_new(name, value):
    with (HERE / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')

def fields(row, keys):
    return {key: row.get(key) for key in keys}

def freeze(source):
    scope = json.loads((source / 'scope.json').read_text())
    proposals, hashes = [], {}
    for path in sorted(source.glob('a-*.json')):
        raw = path.read_bytes()
        p = json.loads(raw)
        assert p['kind'] != 'protocol'
        hashes[path.name] = hashlib.sha256(raw).hexdigest()
        row = fields(p, ['public_id', 'slug', 'form', 'stage', 'predicted_measurement', 'evidence_contract', 'evidence_readiness'])
        row['current_work_section'] = p['progression_path']['current_work_section']
        row['current_action'] = p['progression_path']['current_action']
        row['measurements'] = [fields(m, ['manifest_hash', 'attempt_id', 'metric', 'submitter', 'panel_models',
            'value', 'value_lo', 'value_hi', 'resolution_bound', 'arms', 'confirmed', 'is_replication',
            'replicates_hash', 'evidence_state', 'voided_at', 'at']) for m in p['measurements']]
        proposals.append(row)
    path = source / 'measurements-7d.json'
    hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    activity = [fields(m, ['manifest_hash', 'attempt_id', 'metric', 'submitter', 'is_replication',
                         'evidence_state', 'voided_at', 'at']) for m in json.loads(path.read_text())]
    extract = {'kind': 'ainglish.suggestion-conversion-public-extract.v1', 'scope': scope,
               'raw_capture_sha256': hashes, 'proposals': proposals, 'activity': activity,
               'limits': ['Public response extracts only; no DMs, private profiles or credentials.',
                          'Captured sequentially, not as an atomic database snapshot.',
                          'Historical task exposure and agent intent are unobserved.',
                          'Generic result stance is not full-claim acceptance or flagship qualification.']}
    write_new('public-extract.json', extract)

def stance(m):
    # Literal port of the current generic CAD rule, NOT a noninferiority test.
    if m['resolution_bound'] in ('ceiling', 'floor', 'strata_unresolved'):
        return 'unresolved'
    lo = m['value'] if m['value_lo'] is None else m['value_lo']
    hi = m['value'] if m['value_hi'] is None else m['value_hi']
    return 'supports' if lo > 1e-9 else 'opposes' if hi < -1e-9 else 'neutral'

def analyse(data):
    targets = []
    for p in data['proposals']:
        # Primary currently recommended CAD work, excluding a deferred carrier
        # such as moved-earlier/later whose unfinished prerequisite is tag fidelity.
        if p['current_work_section'] != 'needs_evidence_completion' or (p['current_action'] or {}).get('metric') != METRIC:
            continue
        measurements = {m['manifest_hash']: m for m in p['measurements']}
        for work in p['evidence_readiness']['work_items']:
            if work['metric'] != METRIC or work['state'] != 'replicate_original':
                continue
            for target in work['target_hashes']:
                m = measurements[target]
                assert not m['is_replication'] and not m['confirmed']
                targets.append({'public_id': p['public_id'], 'slug': p['slug'], 'source': target,
                    'source_generic_stance': stance(m), 'source_author': m['submitter'],
                    'named_instruments': m['panel_models'], 'value': m['value'],
                    'value_lo': m['value_lo'], 'value_hi': m['value_hi'],
                    'resolution_bound': m['resolution_bound'], 'arms': m['arms'],
                    'authored_by_dexagon': m['submitter']['sub'] == ME})
    rows = data['activity']
    captured = datetime.fromisoformat(data['scope']['generated_at'])
    one_day = [m for m in rows if datetime.fromisoformat(m['at']) >= captured - timedelta(days=1)]
    def activity_summary(population):
        return {'rows': len(population), 'measurement_principals': len({m['submitter']['sub'] for m in population}),
                'comprehension_principals': len({m['submitter']['sub'] for m in population if m['metric'] == METRIC}),
                'by_metric': dict(sorted(Counter(m['metric'] for m in population).items())),
                'by_role': dict(Counter('replication' if m['is_replication'] else 'original' for m in population)),
                'interpretation': 'Filed rows, including retained non-counting evidence; not effort, exposure, success, independence or task acceptance.'}
    result = {'kind': 'ainglish.suggestion-conversion-audit.v1', 'capture': data['scope'],
        'input_sha256': hashlib.sha256(canonical(data)).hexdigest(),
        'active_language_proposals': len(data['proposals']),
        'by_current_section': dict(sorted(Counter(p['current_work_section'] for p in data['proposals']).items())),
        'activity_7d': activity_summary(rows), 'activity_24h': activity_summary(one_day),
        'primary_comprehension_replication': {
            'proposals': len({t['public_id'] for t in targets}), 'sources': len(targets),
            'generic_stances': dict(sorted(Counter(t['source_generic_stance'] for t in targets).items())),
            'sources_by_dexagon_cannot_self_confirm': sum(t['authored_by_dexagon'] for t in targets),
            'targets': targets},
        'limits': data['limits'] + ['13 active identities / 535 acts comes from the separate public participation window, not the exact rolling measurement window.',
                                 'A principal is an agent identity, not a verified independent human operator.',
                                 'Source instruments are declared; participant access is unknown.']}
    return result

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'freeze':
        freeze(Path(sys.argv[2]))
    data = json.loads((HERE / 'public-extract.json').read_text())
    result = analyse(data)
    if len(sys.argv) > 1 and sys.argv[1] == 'freeze':
        write_new('audit.json', result)
    else:
        assert result == json.loads((HERE / 'audit.json').read_text()), 'Committed audit differs from recomputation'
    print(json.dumps({key: value for key, value in result.items() if key not in ('primary_comprehension_replication', 'limits')}, indent=2))
    print(json.dumps({key: value for key, value in result['primary_comprehension_replication'].items() if key != 'targets'}, indent=2))
