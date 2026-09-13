"""Inspect frozen public queue sources; no inference, filing or automatic disposition.

Only explicitly pinned GitHub/paste.rs HTTPS banks are downloaded (20 MiB cap).
Token recounts use installed encoders and forbid a network tokenizer fallback.
"""
from collections import Counter
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
from unittest.mock import patch

from ainglish.experiment_audit import audit_items, audit_token_pairs, items_digest
from ainglish.client import manifest_commitment
from ainglish.measure import token_delta

ROOT = Path(__file__).resolve().parent
LIMIT = 20 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise ValueError('Redirects are outside this bounded artifact audit')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def load_bank(manifest):
    inline = [manifest[k] for k in ['items', 'test_set', 'pairs'] if isinstance(manifest.get(k), list)]
    if len({items_digest(bank) for bank in inline}) > 1:
        raise ValueError('Conflicting inline input carriers')
    for key in ['items', 'test_set', 'pairs']:
        if isinstance(manifest.get(key), list):
            return manifest[key], {'carrier': key, 'source': 'inline',
                'canonical_items_sha256': items_digest(manifest[key]),
                'declared_pin': manifest.get('items_sha256')}
    url, pin = manifest.get('items_url'), manifest.get('items_sha256')
    if not isinstance(url, str) or not isinstance(pin, str) or len(pin) != 64:
        return None, {'source': 'not_recoverable', 'reason': 'missing_pinned_public_bank'}
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != 'https' or parts.hostname not in {'raw.githubusercontent.com', 'paste.rs'} \
            or parts.username or parts.password or parts.query:
        return None, {'source': 'not_fetched', 'reason': 'outside_explicit_public_artifact_hosts'}
    cache = ROOT / 'banks' / (pin + '.json')
    if cache.exists():
        stored = json.loads(cache.read_text())
        if items_digest(stored['items']) != stored['receipt']['canonical_items_sha256']:
            raise ValueError('Cached canonical items changed')
        if pin not in {stored['receipt']['canonical_items_sha256'], stored['receipt']['file_bytes_sha256']}:
            raise ValueError('Cached receipt does not bind the requested pin')
        return stored['items'], stored['receipt']
    request = urllib.request.Request(url, headers={'User-Agent': 'Dexagon-public-source-audit/1'})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=35) as response:
        if urllib.parse.urlsplit(response.geturl()).hostname != parts.hostname:
            raise ValueError('Unexpected redirect host')
        raw = response.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('Source exceeds bounded artifact size')
    doc = json.loads(raw)
    items = doc['items'] if isinstance(doc, dict) and 'items' in doc else doc
    canonical, byte_digest = items_digest(items), hashlib.sha256(raw).hexdigest()
    receipt = {'source': 'downloaded', 'url': url, 'canonical_items_sha256': canonical,
        'file_bytes_sha256': byte_digest, 'declared_pin': pin,
        'pin_basis': 'canonical_items' if canonical == pin else 'file_bytes' if byte_digest == pin else 'mismatch'}
    if receipt['pin_basis'] == 'mismatch':
        return None, receipt
    if isinstance(doc, dict) and doc.get('sha256') not in (None, canonical):
        return None, dict(receipt, embedded_pin_mismatch=True)
    save(cache, {'items': items, 'receipt': receipt})
    return items, receipt


def recount(row, bank):
    names = [name.removeprefix('tiktoken/') for name in row['panel_models']]
    if any(name not in {'cl100k_base', 'o200k_base', 'p50k_base'} for name in names):
        return {'status': 'not_recounted', 'reason': 'unavailable_exact_tokenizer_roster'}
    import tiktoken
    with ExitStack() as stack:
        stack.enter_context(patch('urllib.request.urlopen', side_effect=AssertionError('No tokenizer download')))
        stack.enter_context(patch('requests.get', side_effect=AssertionError('No tokenizer download')))
        result = token_delta(bank, names, encoder_factory=tiktoken.get_encoding)
    delta = result['floor'] - row['value']
    return {'status': 'recounted_retained_pairs', 'library': 'tiktoken', 'version': tiktoken.__version__,
        'formula': 'maximum across tokenizer means, not a mean across tokenizers',
        'computed': result['floor'], 'reported': row['value'], 'difference': delta,
        'equal_within_0_0005_tokens': abs(delta) <= 0.0005,
        'comparison_tolerance_tokens': 0.0005,
        'per_tokenizer_means': {n: v['mean'] for n, v in result['by_tokenizer'].items()},
        'boundary': 'Same-input diagnostic, not independent confirmation. Current installed tokenizer implementation; this does not certify semantic equivalence or historical software identity.'}


def main():
    snapshot = json.loads((ROOT / 'public-snapshot.json').read_text())
    queue = snapshot['queue']['needs_dispute_settlement']
    targets = {h: p for p in queue for h in p['evidence_work']['target_hashes']}
    rows = []
    for digest, proposal in sorted(targets.items()):
        m = json.loads((ROOT / 'measurements' / (digest + '.json')).read_text())
        row = {'proposal_public_id': proposal['public_id'], 'title': proposal['title'],
            'source_manifest_hash': digest, 'source_attempt_id': m.get('attempt_id'),
            'source_author': m['submitter']['name'] or 'Unknown display name',
            'source_submitter_sub': m['submitter']['sub'], 'metric': m['metric'],
            'value': m['value'], 'confirmed': m['confirmed'], 'stance': m['stance'],
            'agreements': m['replication_count'], 'disagreements': m['disagreement_count'],
            'readers': m['panel_models'], 'comparison': m['manifest'].get('comparator'),
            'required_strata': m['manifest'].get('settlement_strata'),
            'preregistered': (m.get('attempt') or {}).get('backfilled') is False,
            'author_notice': proposal.get('author_work_notice'),
            'result_attestation': m.get('interval_provenance_attestation'),
            'structural_audit': None, 'token_recount': None}
        try:
            if manifest_commitment(m['manifest']) != digest:
                raise ValueError('Retained manifest does not match the source commitment')
            row['manifest_commitment_verified'] = True
            bank, receipt = load_bank(m['manifest'])
            row['bank'] = receipt
            if bank is not None:
                if m['metric'] == 'token_delta':
                    row['structural_audit'] = audit_token_pairs(bank)
                    if row['structural_audit']['ok']:
                        row['token_recount'] = recount(m, bank)
                else:
                    row['structural_audit'] = audit_items(bank)
        except Exception as exc:
            row['audit_error_type'] = type(exc).__name__
        rows.append(row)
        print(json.dumps({'audited': len(rows), 'source': digest[:12], 'metric': m['metric'],
                          'bank': row.get('bank', {}).get('source'), 'error': row.get('audit_error_type')}), flush=True)
    summary = {'proposals': len(queue), 'disputed_originals': len(rows),
        'by_metric': dict(Counter(r['metric'] for r in rows)),
        'source_authors': dict(Counter(r['source_author'] for r in rows)),
        'bank_sources': dict(Counter(r.get('bank', {}).get('source', 'error') for r in rows)),
        'structural_errors': sum(r['structural_audit'] is not None and not r['structural_audit']['ok'] for r in rows),
        'token_recounted': sum(r['token_recount'] is not None and r['token_recount']['status'] == 'recounted_retained_pairs' for r in rows)}
    save(ROOT / 'source-audit.json', {'at': datetime.now(timezone.utc).isoformat(), 'summary': summary,
        'rows': rows, 'boundary': 'Diagnostic snapshot, no inference or live writes. A structural warning is not a semantic rejection; a successful recount is not an independent replication. Read current source state and author discussion before action.'})
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
