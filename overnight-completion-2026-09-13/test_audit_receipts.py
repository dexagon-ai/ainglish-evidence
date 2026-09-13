"""Recheck retained public audit receipts without inference or network access."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ainglish.client import manifest_commitment
from ainglish.experiment_audit import items_digest
from audit_sources import load_bank, recount
from summarize_audit import CAREFUL_PRIMARY, SELF

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text())


class AuditReceipts(unittest.TestCase):
    def test_contracts_conserve_the_named_warnings_without_changing_readiness(self):
        warnings = read('public-snapshot.json')['evidence_contract_audit']['success_criteria_reviews']
        inputs = read('contract-inputs.json')['rows']
        rows = read('contract-dispositions.json')['rows']
        identifiers = {w['public_id'] for w in warnings}
        self.assertEqual(32, len(identifiers))
        self.assertEqual(identifiers, {r['public_id'] for r in rows})
        self.assertEqual(identifiers, {r['public_id'] for r in inputs})
        self.assertEqual(10, len(CAREFUL_PRIMARY))
        self.assertLessEqual(CAREFUL_PRIMARY, identifiers)
        self.assertTrue(all(r['changes_readiness'] is False for r in rows))

    def test_source_receipts_bind_every_manifest_and_keep_missing_banks_unknown(self):
        rows = read('source-audit.json')['rows']
        self.assertEqual(59, len({r['source_manifest_hash'] for r in rows}))
        self.assertEqual(47, len({r['proposal_public_id'] for r in rows}))
        self.assertEqual(57, sum(r['structural_audit'] is not None for r in rows))
        self.assertTrue(all(r['structural_audit'] is None or r['structural_audit']['ok'] for r in rows))
        for row in rows:
            measurement = read('measurements/' + row['source_manifest_hash'] + '.json')
            self.assertEqual(row['source_manifest_hash'], manifest_commitment(measurement['manifest']))
            self.assertTrue(row['manifest_commitment_verified'])

    def test_retained_token_recounts_are_diagnostics_and_preserve_the_known_error(self):
        token_rows = [r for r in read('source-audit.json')['rows'] if r['metric'] == 'token_delta']
        self.assertEqual(19, len(token_rows))
        mismatches = []
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('No artifact network')):
            for row in token_rows:
                measurement = read('measurements/' + row['source_manifest_hash'] + '.json')
                bank, _ = load_bank(measurement['manifest'])
                result = recount(measurement, bank)
                self.assertEqual(row['token_recount'], result)
                self.assertEqual(.0005, result['comparison_tolerance_tokens'])
                if not result['equal_within_0_0005_tokens']:
                    mismatches.append((row['source_manifest_hash'], result['computed'], result['reported']))
        self.assertEqual([('f504b3fcb597190e4b71ef059b2bc2a47fe15c15f839bb1d058189f4fbfbb0ff', 1.5, 2)], mismatches)

    def test_disposition_routes_conserve_sources_and_do_not_assign_self_replication(self):
        disposition = read('source-dispositions.json')
        rows = disposition['rows']
        self.assertEqual(59, len(rows))
        self.assertEqual(dict(Counter(r['diagnostic_next_route'] for r in rows)), disposition['by_route'])
        own_readers = [r for r in rows if r['source_submitter_sub'] == SELF and r['metric'] != 'token_delta']
        self.assertEqual(24, len(own_readers))
        self.assertTrue(all(r['diagnostic_next_route'] == 'another_principal_required_to_replicate_own_original'
                            for r in own_readers))

    def test_cached_bank_receipts_still_bind_their_exact_items(self):
        banks = list((ROOT / 'banks').glob('*.json'))
        pins = {r['bank']['declared_pin'] for r in read('source-audit.json')['rows']
                if r.get('bank', {}).get('source') == 'downloaded'}
        self.assertEqual(34, len(banks))  # 36 source rows reference 34 distinct pinned banks.
        self.assertEqual(pins, {path.stem for path in banks})
        for path in banks:
            stored = json.loads(path.read_text())
            self.assertEqual(items_digest(stored['items']), stored['receipt']['canonical_items_sha256'])
            self.assertIn(path.stem, [stored['receipt']['canonical_items_sha256'], stored['receipt']['file_bytes_sha256']])

    def test_gpu_journal_is_one_complete_predeclared_control_pass(self):
        design = read('format-stress/design.json')
        start = read('format-stress/start.json')
        result = read('format-stress/result.json')
        cells = read('format-stress/cells.json')
        digest = hashlib.sha256((ROOT / 'format-stress/design.json').read_bytes()).hexdigest()
        self.assertEqual('08bf7130d00ed17559c54f56ac304e955c14dda7f2d74e0e48f0a57c0576762d', digest)
        self.assertEqual(digest, start['design_sha256'])
        self.assertEqual(digest, result['design_sha256'])
        self.assertEqual(256, len(cells))
        controls = {c['id']: c for c in design['controls']}
        self.assertEqual(128, len(controls))
        expected = {(r['name'], c['id']) for r in design['panel'] for c in design['controls']}
        self.assertEqual(expected, {(r['reader'], r['control_id']) for r in cells})
        for row in cells:
            control = controls[row['control_id']]
            self.assertEqual(control['answer'].casefold(), row['answer'].strip().casefold())
            self.assertTrue(row['accepted'] and row['correct'])
            self.assertFalse(row['absent'])
            self.assertNotIn('error_type', row)
        self.assertIsNone(result['stop'])
        self.assertEqual(256, sum(r['started'] for r in result['by_reader_and_style'].values()))
        self.assertEqual(256, sum(r['correct'] for r in result['by_reader_and_style'].values()))

    def test_sanction_bank_remains_unchanged_during_owner_review(self):
        path = ROOT.parent / 'completion-paths-2026-09-10/reader-packets/sanction-careful/items.json'
        self.assertEqual('a63592a0084929fbae3bd13b45120ee375b54357ff2576bfc00a538d62ee3d86',
                         hashlib.sha256(path.read_bytes()).hexdigest())
        items = json.loads(path.read_text())
        self.assertEqual(64, len(items))
        self.assertEqual('09becce008fb39df0bf0ea7cd8b6c47453ad2b4ce5b053e2adf6f4c381227667', items_digest(items))
        edits = {r['id'] for r in items if 'Larch ltd' in r['english']}
        self.assertEqual({'S-f96ce12c60', 'S-0b66af7934', 'S-614db603e7', 'S-d43de45f5d'}, edits)


if __name__ == '__main__':
    unittest.main()
