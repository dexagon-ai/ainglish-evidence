"""Hermetic SDK contract checks; no provider, model, mint or submission calls.

All observations and the .invalid catalog are synthetic software-test fixtures.
Nothing here creates or publishes a genuine reader-qualification receipt.
"""
from datetime import datetime, timezone
import unittest

from ainglish import panel, reader_qualification as qualification


def fixture():
    return {
        'kind': qualification.SCREEN_KIND,
        'roster_id': 'fixture-reader@provider-served',
        'reader': {
            'name': 'fixture-reader', 'provider': 'openai-compatible',
            'model': 'fixture-model', 'precision': 'provider-served',
            'base_url': 'https://qualification.example.invalid/v1',
            'api_key_env': '', 'model_catalog': 'openai:/models',
            'temperature': 0, 'max_tokens': 64, 'timeout_s': 10,
        },
        'lineage': {'key': 'fixture-family', 'basis': 'Synthetic fixture only'},
        'validity_days': 1, 'min_gap_bps': 1250, 'min_recovered_bps': 5000,
        'controls': [
            {'id': 'fixture-%s' % i, 'detectable': 'resolved-%s' % i,
             'other': 'unresolved-%s' % i, 'question': 'Fixture question',
             'options': ['resolved', 'unknown'], 'answer': 'resolved'}
            for i in range(4)
        ],
    }


def prepared(manifest):
    def synthetic_catalog(request):
        assert request.full_url == 'https://qualification.example.invalid/v1/models'
        assert request.get_header('Authorization') is None
        return {'data': [{'id': 'fixture-model', 'object': 'model'}]}
    return panel.prepare_reader_instruments(manifest, fetch_fn=synthetic_catalog)


def exercise(*, answer=None):
    calls = []
    def fake_ask(reader, text, question, options):
        calls.append(text)
        if answer is not None:
            return answer
        return 'resolved' if text.startswith('resolved-') else 'unknown'
    outcome = qualification.run_screen(
        fixture(), ask_fn=fake_ask, prepare_fn=prepared,
        now=datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc),
    )
    return outcome, calls


class HostedQualificationContract(unittest.TestCase):
    def test_explicit_hosted_precision_needs_no_weight_digest(self):
        checked = qualification.validate_screen(fixture())
        self.assertNotIn('model_digest', checked['reader'])

    def test_catalog_binding_is_not_a_weight_digest(self):
        out, calls = exercise()
        self.assertEqual(len(calls), 8)
        self.assertIsNone(out['instrument']['model_digest'])
        self.assertEqual(out['instrument']['digest_source'], 'provider-catalog:openai:/models')
        self.assertEqual(out['instrument']['model_catalog_binding']['weight_identity'], 'provider-opaque')
        self.assertNotIn('model_digest', out['receipt']['reader'])

    def test_expiry_is_generated_by_screen_runner(self):
        out, _ = exercise()
        self.assertEqual(out['receipt']['qualified_at'], '2026-09-10T12:00:00+00:00')
        self.assertEqual(out['receipt']['valid_until'], '2026-09-11T12:00:00+00:00')
        self.assertTrue(qualification.validate(out['receipt'])['result']['passed'])

    def test_settings_binding_and_attachment(self):
        out, _ = exercise()
        manifest = {'metric': 'learnability', 'models': ['fixture-reader@provider-served']}
        attached = qualification.attach(manifest, [out['receipt']])
        self.assertEqual(len(attached['reader_qualifications']), 1)
        self.assertNotIn('reader_qualifications', manifest)
        self.assertEqual(len(out['receipt']['settings_sha256']), 64)

    def test_changed_roster_cannot_reuse_receipt(self):
        out, _ = exercise()
        with self.assertRaisesRegex(ValueError, 'declared manifest model'):
            qualification.attach({'metric': 'learnability', 'models': ['other-reader']}, [out['receipt']])

    def test_constant_answer_is_a_failed_screen_without_retries(self):
        out, calls = exercise(answer='resolved')
        self.assertEqual(len(calls), 8)
        self.assertFalse(out['receipt']['result']['passed'])
        self.assertEqual(out['status'], 'failed')

    def test_invented_hosted_weight_digest_is_refused(self):
        spec = fixture()
        spec['reader']['model_digest'] = 'sha256:' + 'a' * 64
        with self.assertRaisesRegex(SystemExit, 'unverifiable'):
            prepared({'panel': [spec['reader']]})

    def test_plain_roster_is_a_distinct_contract(self):
        spec = fixture()
        del spec['reader']['precision']
        spec['roster_id'] = spec['reader']['name']
        spec['receipt_precision'] = 'provider-served'
        with self.assertRaisesRegex(ValueError, 'explicit bound model_digest'):
            qualification.validate_screen(spec)


if __name__ == '__main__':
    unittest.main()
