"""Same-input audit of recent canonical sources; never an independent replication."""
from datetime import datetime, timezone
import importlib.metadata
from unittest.mock import patch
import json
import sys
from ainglish import token_measurement
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from instrument import ROOT, save

cached = '--cached-v2' in sys.argv
client = None if cached else ainglish_client()
page = json.loads((ROOT / 'source-audit/discovery.json').read_text()) if cached else client.measurements(metric='token_delta', role='original', since='2026-09-05T00:00:00Z', limit=100)
if not cached:
    save('source-audit/discovery.json', page)
assert not page['has_more'], 'Paginate the source inventory before making coverage claims'
sources = [r for r in page['measurements'] if r['submitter']['sub'] == '08a036ce-13fb-4331-905f-08c5f1187a43']
results = []
for brief in sources:
    source_path = 'source-audit/' + brief['manifest_hash'] + '.json'
    source = json.loads((ROOT / source_path).read_text()) if cached else client.measurement(brief['manifest_hash'])
    if not cached:
        save(source_path, source)
    manifest = source['manifest']
    assert manifest_commitment(manifest) == source['manifest_hash']
    result = {'hash': source['manifest_hash'], 'attempt_id': source['attempt_id'], 'value': source['value'],
              'proposal': source['proposal'], 'evidence_state': source['evidence_state'],
              'declared_version': manifest.get('tokenizer_provenance',{}).get('library_version'),
              'installed_version': importlib.metadata.version('tiktoken'),
              'pairs': len(manifest.get('test_set',[]))}
    if result['declared_version'] != result['installed_version']:
        result['status'] = 'not_recounted_different_or_undeclared_library'
    else:
        try:
            # GET receipts serialize absent optional submission fields as null.
            # The verifier expects POST shape: remove ONLY those known null fields;
            # never alter the manifest, inputs, numerical claims or non-null roles.
            payload = dict(source)
            normalized = []
            for optional in ('replicates_hash', 'stratum_results'):
                if optional in payload and payload[optional] is None:
                    normalized.append(optional)
                    del payload[optional]
            result['api_null_fields_omitted_for_post_verifier'] = normalized
            with patch('tiktoken.load.read_file', side_effect=RuntimeError('No downloads; existing encoding cache only')):
                result['verification'] = token_measurement.verify_payload(payload)
            result['status'] = 'canonical_arithmetic_verified'
        except (Exception, SystemExit) as exc:
            result.update(status='verification_refused', reason=str(exc), error_type=type(exc).__name__)
    results.append(result)
    print(source['proposal']['title'], source['manifest_hash'][:8], result['status'], flush=True)
save('source-audit/report-v2.json' if cached else 'source-audit/report.json', {'at':datetime.now(timezone.utc).isoformat(),'sources':results,
     'audit_correction': 'The first audit passed GET receipts directly to a POST-payload verifier. Its null-field shape refusals are audit-adapter failures, not defects in the scientific sources. Version 2 preserves that report and normalizes only optional null fields.' if cached else None,
     'boundary':'Exact-source count audit, not fresh-input replication, semantic certification, comprehension or future efficiency.'})
