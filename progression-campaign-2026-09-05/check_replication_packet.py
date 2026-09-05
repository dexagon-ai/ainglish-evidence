"""Read-only source/route/freshness checks. Never mint, tokenize, call a reader or submit."""
from collections import Counter
import argparse
import json
from pathlib import Path
from ainglish import panel
from ainglish.client import AinglishClient, manifest_commitment
from dossier_refresh import TARGETS

ROOT = Path(__file__).resolve().parent


def items_of(value):
    rows = value.get('items') if isinstance(value, dict) else value
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected a nonempty item array or an items wrapper')
    for row in rows:
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k].strip() for k in ('english', 'ainglish')):
            raise ValueError('Every item must retain the complete English and Ainglish texts')
    return rows


def check_fresh(source_items, fresh_items, manifest):
    source, fresh = items_of(source_items), items_of(fresh_items)
    norm = lambda text: ' '.join(text.split())
    seen = {norm(row[arm]) for row in source for arm in ('english', 'ainglish')}
    if any(norm(row[arm]) in seen for row in fresh for arm in ('english', 'ainglish')):
        raise ValueError('Reused source surface: same-input or one-arm reuse is not independent fresh evidence')
    real = [r for r in fresh if not r.get('calibration')]
    source_real = [r for r in source if not r.get('calibration')]
    if len(real) != len(source_real):
        raise ValueError('This bounded package preserves the source sample count; do not silently change it')
    field = 'stratum' if manifest['metric'] == 'token_delta' else 'settlement_stratum'
    if Counter(r.get(field) for r in real) != Counter(r.get(field) for r in source_real):
        raise ValueError('Preserve every source stratum and its fixed sample count')
    if len({(r['english'], r['ainglish']) for r in real}) != len(real):
        raise ValueError('Duplicate fresh complete pairs')
    if manifest['metric'] != 'token_delta':
        if len({r.get('id') for r in fresh}) != len(fresh) or any(not isinstance(r.get('id'), str) or not r['id'] for r in fresh):
            raise ValueError('Panel item IDs must be present and unique')
        for row in fresh:
            if not isinstance(row.get('question'), str) or not row['question']:
                raise ValueError('A held-out question is required')
            options = row.get('options')
            if not isinstance(options, list) or len(options) != len(set(options)) or row.get('answer') not in options:
                raise ValueError('Every panel row requires distinct options and an exact legal frozen gold')
    return {'fresh_real_items': len(real), 'source_surface_overlap': 0,
            'stratum_counts': dict(Counter(r[field] for r in real)),
            'boundary': 'Text disjointness cannot establish semantic independence, faithful controls or adequate readers. Renaming IDs alone is not a new scientific carrier.'}


def inspect(client, target, fresh_items):
    public_id, digest = TARGETS[target]
    work = client.work_package(public_id, replicates_hash=digest)
    if work['status'] != 'offered':
        raise ValueError('Exact target is ' + work['status'] + '; stop, no substitute and no attempt')
    source = client.measurement(digest)
    if manifest_commitment(source['manifest']) != digest or source['manifest_hash'] != digest:
        raise ValueError('Source manifest no longer matches the exact hash')
    if source['is_replication'] or source.get('retraction') or source['evidence_state'] != 'valid':
        raise ValueError('The selected source is not an active valid original')
    if source.get('submitter', {}).get('sub') == client.whoami().get('sub'):
        raise ValueError('The source author cannot provide independent confirmation')
    manifest = source['manifest']
    original = manifest.get('test_set')
    if original is None:
        original, _ = panel.fetch_items(manifest['items_url'], manifest['items_sha256'])
    report = check_fresh(original, fresh_items, manifest)
    return dict(report, target_hash=digest, public_id=public_id, metric=source['metric'],
                source_value=source['value'], source_comparator=manifest.get('comparator') or manifest.get('comparison_identity'),
                route_generated_at=work['generated_at'], status='structural_checks_only_no_permission_to_skip_scientific_review')


def selftest():
    source = [{'english': 'original English', 'ainglish': 'original marked', 'stratum': 'one'}]
    fresh = [{'english': 'a genuinely fresh description', 'ainglish': 'fresh-marked description', 'stratum': 'one'}]
    m = {'metric': 'token_delta'}
    assert check_fresh(source, fresh, m)['source_surface_overlap'] == 0
    for bad in (source, [dict(fresh[0], english=' original   English ')],
                [dict(fresh[0], stratum='other')], fresh + fresh):
        try:
            check_fresh(source, bad, m)
        except ValueError:
            pass
        else:
            raise AssertionError('Unsafe freshness/sample/stratum change accepted')
    class Refused:
        def work_package(self, *args, **kwargs):
            return {'status': 'not_offered'}
        def measurement(self, *args):
            raise AssertionError('No source work after exact route refusal')
    try:
        inspect(Refused(), 'mean-faithful-cost', fresh)
    except ValueError:
        pass
    else:
        raise AssertionError('Not-offered target accepted')
    print('Freshness, stratum, sample and fail-closed route checks pass; no network, tokens or readers.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--target', choices=TARGETS)
    parser.add_argument('--fresh', type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        if not args.target or args.fresh is None:
            parser.error('--target and --fresh are both required')
        print(json.dumps(inspect(AinglishClient(), args.target, json.loads(args.fresh.read_text())), indent=2))
