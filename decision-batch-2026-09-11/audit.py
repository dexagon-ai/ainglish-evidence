"""Bounded public-artifact audit, no reader calls or governance writes.

The semantic check is deliberately narrow: quantity final-value and determinacy
items. Unrecognised frames are unassessed, never assumed correct. This is an
author's audit, not an independent replication or a rewritten official score.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
from urllib.request import HTTPRedirectHandler, build_opener

from ainglish.client import manifest_commitment

ALLOWED = (
    'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/',
    'https://raw.githubusercontent.com/reticuli-labs/panel-artifacts/',
    'https://dpaste.com/4WKQ8BUT9.txt', 'https://dpaste.com/CHBX3M4QG.txt',
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('artifact redirect requires explicit review')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def write(path, value):
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def artifact(manifest, root):
    url = manifest.get('items_url')
    if not url:
        return manifest.get('test_set', manifest.get('items')), 'inline', None
    if not any(url.startswith(prefix) for prefix in ALLOWED[:2]) and url not in ALLOWED[2:]:
        raise ValueError('unreviewed artifact origin: ' + url)
    path = root / 'artifacts' / (hashlib.sha256(url.encode()).hexdigest() + '.json')
    if not path.exists():
        with build_opener(NoRedirect()).open(url, timeout=30) as response:
            body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError('artifact exceeds 2 MB audit limit')
        value = json.loads(body)
        # Generated archive keeps the parsed public object, not private transport data.
        write(path, value)
    value = json.loads(path.read_text())
    return value.get('items', value) if isinstance(value, dict) else value, url, str(path.relative_to(root))


def quantity(row):
    """Re-derive arithmetic from visible marked text, not supplied ledger gold."""
    text = row['ainglish'].split('\n\n')[-1]
    known = re.search(r'Its starting value is (-?\d+)\b', text)
    legacy = re.search(r'For job [^,]+, the .+? is (-?\d+)\b', text)
    if known or legacy:
        current = int((known or legacy)[1])
    elif 'not known' in text or 'not supplied' in text or 'unknown' in text or 'not stated' in text:
        current = None
    else:
        return {'status': 'unassessed', 'reason': 'unrecognised initial-value frame'}
    first = re.search(r'First (increase|decrease|set) this quantity (by|to) ([+-]?\d+)\s', text)
    if 'First ' in text and first is None:
        return {'status': 'unassessed', 'reason': 'unrecognised shared first update'}
    if first:
        n = int(first[3])
        if first[1] == 'set' and first[2] == 'to':
            current = n
        elif first[1] in ('increase', 'decrease') and first[2] == 'by':
            current = None if current is None else current + (n if first[1] == 'increase' else -n)
        else:
            return {'status': 'unassessed', 'reason': 'inconsistent shared first update'}
    operations = re.findall(r'(set-to|adjust-by)\(([+-]?\d+)\s+[^)]+\)', text)
    if not operations:
        return {'status': 'unassessed', 'reason': 'no numeric marked operations'}
    for op, operand in operations:
        n = int(operand)
        current = n if op == 'set-to' else None if current is None else current + n
    question = row['question']
    duplicate = False
    if 'is the final numeric value determined' in question:
        semantic = 'yes' if current is not None else 'no'
        valid = [semantic]
        if current is None and 'the final value is not determined' in row['options']:
            valid.append('the final value is not determined')
            duplicate = True
    elif 'what is the final value?' in question:
        answers = re.findall(r'\b([A-D]) = ([^.]*)\.', question)
        valid = [key for key, value in answers if
                 (current is None and value.strip().startswith('not determined')) or
                 (current is not None and re.match(r'^' + re.escape(str(current)) + r'\s', value.strip()))]
    elif 'would a requirement for ' in question and ' fit within ' in question:
        match = re.search(r'requirement for (-?\d+)\s', question)
        if not match:
            return {'status': 'unassessed', 'reason': 'unrecognised requirement'}
        valid = ['the final value is not determined' if current is None else
                 'yes' if int(match[1]) <= current else 'no']
    else:
        return {'status': 'unassessed', 'reason': 'unrecognised question'}
    return {'status': 'checked', 'computed_final': current, 'valid_answers': valid,
            'key_semantically_valid': row['answer'] in valid,
            'non_unique_correct_answer': duplicate or len(valid) > 1}


def inspect(source, root):
    m = source['manifest']
    rows, url, archive = artifact(m, root)
    if not isinstance(rows, list):
        raise ValueError('no retained item list')
    real = [r for r in rows if not r.get('calibration')]
    source_cells = (source.get('interval_provenance_attestation') or {}).get('cells', [])
    semantic = []
    if source['proposal']['public_id'] == 'a-k2d3rxn56qysr74n':
        for row in real:
            check = quantity(row)
            semantic.append({'item_id': row['id'], 'stratum': row.get('settlement_stratum'), **check})
    bad_ids = {r['item_id'] for r in semantic if r.get('non_unique_correct_answer') or r.get('key_semantically_valid') is False}
    affected = [c for c in source_cells if c['item_id'] in bad_ids]
    questions = collections.Counter('determinacy' if 'is the final numeric value determined' in r['question']
                                    else 'final_numeric_value' if 'what is the final value?' in r['question']
                                    else 'consequence_or_other' for r in real)
    return {
        'manifest_hash': source['manifest_hash'], 'proposal_public_id': source['proposal']['public_id'],
        'manifest_hash_verified': manifest_commitment(m) == source['manifest_hash'],
        'items_url': url, 'archive': archive, 'items_canonical_sha256': digest(rows),
        'items_pin_matches': None if not m.get('items_sha256') else digest(rows) == m['items_sha256'],
        'real_items': len(real), 'declared_item_counts': m.get('item_counts'),
        'strata': dict(collections.Counter(r.get('settlement_stratum', 'unlabelled') for r in real)),
        'question_families': dict(questions),
        'duplicate_text_questions': len(real) - len({r['question'] for r in real}),
        'comparator': m.get('comparator'),
        'definition_prefaces': sum(r['ainglish'].startswith('Reference:') for r in real),
        'reader_settings': [{k: reader.get(k) for k in ('name','model','model_digest','precision','max_tokens','temperature','seed','num_ctx','reasoning_effort')}
                           for reader in m.get('readers', [])],
        'declared_models': m.get('models'), 'panel_neff': source.get('panel_neff'),
        'sampling_unit': (m.get('interval_estimator') or {}).get('sampling_unit'),
        'interval': [source.get('value_lo'), source.get('value_hi')], 'value': source.get('value'),
        'replicates_hash': source.get('replicates_hash'), 'settlement_eligible': source.get('settlement_eligible'),
        'reproduced_ok': source.get('reproduced_ok'), 'counts_toward_verdict': source.get('counts_toward_verdict'),
        'semantic_checks': semantic,
        'non_unique_gold_items': sorted(r['item_id'] for r in semantic if r.get('non_unique_correct_answer')),
        'invalid_gold_items': sorted(r['item_id'] for r in semantic if r.get('key_semantically_valid') is False),
        'affected_scored_cells': len(affected),
        'affected_correctness_by_arm': {arm: dict(collections.Counter(str(c.get('correct')) for c in affected if c.get('arm') == arm))
                                        for arm in sorted({c.get('arm') for c in affected})},
        'boundary': 'Artifact and narrow arithmetic semantics audit. No new official scores, independent confirmation, causal attribution to training, or lifecycle decision.'
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--capture', type=Path)
    ap.add_argument('--root', type=Path, default=Path(__file__).parent)
    args = ap.parse_args()
    sources = args.root / 'measurements'
    if args.capture:
        for path in args.capture.glob('*.json'):
            if re.fullmatch(r'[0-9a-f]{64}\.json', path.name):
                write(sources / path.name, json.loads(path.read_text()))
    reports = []
    for path in sorted(sources.glob('*.json')):
        source = json.loads(path.read_text())
        try:
            result = inspect(source, args.root)
        except Exception as error:
            result = {'manifest_hash': source['manifest_hash'], 'unassessed': type(error).__name__ + ': ' + str(error)}
        reports.append(result)
        print(path.stem[:12], result.get('real_items'), len(result.get('non_unique_gold_items', [])), result.get('unassessed', ''), flush=True)
    write(args.root / 'audit-report.json', {'kind': 'ainglish.semantic-comparability-audit.v1', 'reports': reports,
          'boundary': __doc__})
    primary = next(r for r in reports if r['manifest_hash'].startswith('c9d8d897817d'))
    raw_url = 'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/ef2dde890f118cbeaee0f95f2117ad8fba717199/next-wave-2026-09-05/quantity.attempt-c709a96c-4e12-472c-b017-8d410b4996d4.cells.json'
    raw, _, archive = artifact({'items_url': raw_url}, args.root)
    index = {r['item_id']: r for r in primary['semantic_checks']}
    examined = []
    for row in raw['rows']:
        check = index[row['item_id']]
        if check.get('non_unique_correct_answer'):
            examined.append({**row, 'semantically_correct': row['answer'] in check['valid_answers']})
    write(args.root / 'raw-scoring-audit.json', {
        'kind': 'ainglish.semantic-gold-raw-audit.v1', 'original_manifest_hash': primary['manifest_hash'],
        'raw_url': raw_url, 'archive': archive, 'rows': examined,
        'wrongly_marked_incorrect': sum(r['semantically_correct'] and r['correct'] is False for r in examined),
        'boundary': 'No official rescore. Non-unique gold invalidates this instrument; retract the original rather than select a more favourable post-hoc score.'})


if __name__ == '__main__':
    main()
