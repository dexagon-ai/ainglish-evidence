#!/usr/bin/env python3
"""Recount already-public token evidence. This is an audit, not a new measurement.

With --intake, read the local authenticated intake's *public measurement and attempt*
responses into sources/. Without it, reproduce the report solely from retained sources.
No model calls, credential files, or result-conditioned new measurement plans are used.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from ainglish.client import _canonical_json, manifest_commitment

ROOT = Path(__file__).resolve().parent
OUTCOME = {
    'careful_original': 'd9bc25ff537cc0d5a03dcb21b43c3eda434e547ab0f3af9b9c3c3578aa44f89b',
    'compact_original': '35874bf6da0cafac20b868fe87d1741a7827a236b01b2d33598790dd4702bb3b',
    'spark_overlap': '43aca8f5abe2cb2697a529705ae0ce0429cd9f3da024bb09bcac84e89c842698',
    'spark_fresh': 'f3c7eab6fd44b350ac545b0580f1a8037f215ce9f01642603236ca037e13c56b',
    'saturnia_careful': '4e664b27ea6103c0586a3e57008ce387245274dd72b0c1e2c35d114f9a25880b',
    'saturnia_compact': '1dbf3d33aa94d6585118b23a7bb612ee034042f9b2bfa8a86f478cda0654b1c3',
    'nemo_showcase': 'c86a965346b320f261eaeaf6672caae7f799cdbd072d3b562650be8dff72b1d3',
}


def read(path):
    return json.loads(path.read_text())


def write(path, obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    if path.exists():
        if path.read_text() != text:
            raise RuntimeError(f'Reproduction differs: {path}. Retain the original audit.')
    else:
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open('x') as f:
            f.write(text)


def pair(row):
    return tuple(row) if isinstance(row, list) else (row.get('english', row.get('baseline')), row['ainglish'])


def audit(m, a):
    mf = m['manifest']
    rows = mf.get('test_set', mf.get('pairs', []))
    if not rows or any(not isinstance(r, (dict, list)) for r in rows):
        return {'manifest_hash': m['manifest_hash'], 'status': 'unrecounted_noninline_inputs'}
    encodings = m['panel_models']
    if any(model not in ('cl100k_base', 'o200k_base', 'p50k_base') for model in encodings):
        return {'manifest_hash': m['manifest_hash'], 'status': 'unrecounted_unsupported_roster',
                'reported_roster': encodings, 'boundary': 'No guessed alias or replacement tokenizer.'}
    result = []
    for model in encodings:
        enc = tiktoken.get_encoding(model)
        deltas = [len(enc.encode(pair(row)[1])) - len(enc.encode(pair(row)[0])) for row in rows]
        strata = defaultdict(list)
        for row, delta in zip(rows, deltas):
            strata[row.get('stratum', 'all') if isinstance(row, dict) else 'all'].append(delta)
        by_stratum = {k: float(Fraction(sum(v), len(v))) for k, v in strata.items()}
        contract = mf.get('settlement_strata')
        if contract:
            mean = sum(Fraction(str(s['weight'])) * Fraction(sum(strata[s['id']]), len(strata[s['id']])) for s in contract) / sum(Fraction(str(s['weight'])) for s in contract)
        else:
            mean = Fraction(sum(deltas), len(deltas))
        result.append({'model': model, 'value': float(mean), 'per_pair': deltas, 'by_stratum': by_stratum})
    computed = max(r['value'] for r in result)
    own_digest = hashlib.sha256(_canonical_json(rows).encode()).hexdigest()
    comparison = mf.get('comparison_identity', {})
    member_values = [{'model': r['model'], 'value': r['value']} for r in result]
    return {
        'manifest_hash': m['manifest_hash'], 'attempt_id': m.get('attempt_id'),
        'url': m.get('url'), 'proposal': m.get('proposal'), 'submitter': m['submitter']['name'],
        'pair_count': len(rows), 'reported_value': m['value'], 'recomputed_value': computed,
        'headline_matches': computed == m['value'],
        'member_values_match': member_values == m.get('per_member'),
        'manifest_commitment_matches': manifest_commitment(mf) == m['manifest_hash'],
        'attempt_commitment_matches': a is not None and a['pin']['manifest_commitment'] == m['manifest_hash'],
        'top_items_digest_matches': None if 'items_sha256' not in mf else mf['items_sha256'] == own_digest,
        'nested_items_digest_matches': None if 'items_sha256' not in comparison else comparison['items_sha256'] == own_digest,
        'members': result, 'evidence_state_observed': m['evidence_state'],
        'settlement_eligible_observed': m.get('settlement_eligible'),
        'input_disjointness_observed': m.get('input_disjointness'),
        'reproduced_ok_observed': m.get('reproduced_ok'),
        'semantic_validity': 'Not inferred from matching arithmetic; see six-proposal-review.md.',
    }


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--intake', type=Path)
    args = ap.parse_args()
    if args.intake:
        paths = [args.intake / f'measurement-{h}.json' for h in OUTCOME.values()]
        paths += list((args.intake / 'candidates').glob('measurement-*.json'))
        for path in paths:
            value = read(path)
            if value['metric'] != 'token_delta':
                continue
            write(ROOT / 'sources' / path.name, value)
            if value.get('attempt_id'):
                attempt_path = path.parent / f"attempt-{value['attempt_id']}.json"
                if attempt_path.exists():
                    write(ROOT / 'sources' / attempt_path.name, read(attempt_path))
    import requests
    requests.get = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('No downloads authorised'))
    import tiktoken
    sources = {p.stem.removeprefix('measurement-'): read(p) for p in sorted((ROOT / 'sources').glob('measurement-*.json'))}
    audits = []
    for m in sources.values():
        apath = ROOT / 'sources' / f"attempt-{m.get('attempt_id')}.json"
        audits.append(audit(m, read(apath) if apath.exists() else None))
    sets = {name: {pair(r) for r in sources[h]['manifest']['test_set']} for name, h in OUTCOME.items()}
    spark = {
        'v1_target_overlap': len(sets['spark_overlap'] & sets['careful_original']),
        'v2_target_overlap': len(sets['spark_fresh'] & sets['careful_original']),
        'v2_v1_overlap': len(sets['spark_fresh'] & sets['spark_overlap']),
        'chronology_boundary': 'Stored mint and closure timestamps do not independently prove when local counting first occurred. No inference of a breach is made.',
        'eligibility_boundary': 'Legacy unpinned comparison identity checks are inert; a v1 comparison-identity mismatch alone is not a settlement prohibition.',
    }
    report = {'kind': 'ainglish.public-source-recount-audit.v1', 'tiktoken': tiktoken.__version__,
              'role': 'Diagnostic recount of existing evidence, never filed as new replication.',
              'sources': audits, 'spark': spark}
    write(ROOT / 'source-audit.json', report)
    print('AUDITED', len(audits), 'sources')
    print('MISMATCHES', [(a['manifest_hash'], a.get('headline_matches'), a.get('member_values_match')) for a in audits if a.get('headline_matches') is False or a.get('member_values_match') is False])
    print('UNRECOUNTED', [a for a in audits if a.get('status')])
    print('SPARK', spark)
