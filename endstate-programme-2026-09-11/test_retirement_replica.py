"""Hermetic runner tests; synthetic fixtures are NOT governance evidence."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import retirement_replica as r


class RetirementReplicaTests(unittest.TestCase):
    def test_original_author_stops_before_any_mint(self):
        client=Mock()
        client.suggestions.return_value={'suggestions': []}
        client.whoami.return_value={'sub': 'same'}
        client.measurement.return_value={'submitter': {'sub': 'same'}}
        with self.assertRaisesRegex(ValueError, 'original author'):
            r.eligibility(client)
        client.mint_attempt.assert_not_called()

    def test_different_handle_without_exact_eligibility_is_not_enough(self):
        client=Mock()
        client.suggestions.return_value={'suggestions': [{'replicates_hash': r.TARGET, 'executable_now': False}]}
        client.whoami.return_value={'sub': 'replicator'}
        client.measurement.return_value={'submitter': {'sub': 'author'}, 'evidence_state': 'valid'}
        client.proposal.return_value={'public_id': r.PID, 'stage': 'seconded'}
        with self.assertRaisesRegex(ValueError, 'not currently offered'):
            r.eligibility(client)

    def test_census_requires_complete_full_withdrawn_details(self):
        c={'records': [{'public_id': 'synthetic', 'stage': 'withdrawn'}], 'withdrawn_details': {}}
        with self.assertRaises(ValueError):r.validate_census(c)
        c['withdrawn_details']['synthetic']={'public_id': 'synthetic', 'stage': 'withdrawn'}
        with self.assertRaises(ValueError):r.validate_census(c)
        c['withdrawn_details']['synthetic']['full_measurement_envelopes']=True
        r.validate_census(c)
        c['records'].append(c['records'][0])
        with self.assertRaises(ValueError):r.validate_census(c)

    def test_database_guard_refuses_shared_or_remote_database(self):
        for url in ['mysql://x:y@db/ainglish_test', 'mysql://x:y@production/ainglish_retirement_replica_abcdefgh',
                    'mysql://x:y@localhost/production', 'sqlite:///tmp/db', '']:
            with self.subTest(url=url), self.assertRaises(ValueError):r.safe_database(url)
        self.assertEqual('ainglish_retirement_replica_abcdefgh',
                         r.safe_database('mysql://x:y@127.0.0.1/ainglish_retirement_replica_abcdefgh'))

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt.json';r.save(path, {'a': 1})
            with self.assertRaises(FileExistsError):r.save(path, {'a': 2})

    def simulate(self, fail=False, refuse=False, flip=0):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);checkout=root/'web';out=root/'freeze';checkout.mkdir()
            (checkout/'composer.lock').write_text('{}')
            (checkout/'suite.php').write_text('synthetic test fixture')
            r.save(out/'input-census.json', {'records': [{'public_id': 'invented', 'stage': 'seconded'}], 'withdrawn_details': {}})
            r.save(out/'source-boundary.json', {'fixture': 'not a real boundary'})
            manifest={'replicates_hash': r.TARGET, 'metric': 'unclaimed_verdict_flips', 'method': 'synthetic fixture',
                'models': ['synthetic'], 'admissibility_gates': ['synthetic'],
                'planned_sample': {'public_proposals': 1}, 'supplementary_tests': ['suite.php'],
                'against': {'input_census_sha256': r.sha(out/'input-census.json'),
                    'source_boundary_sha256': r.sha(out/'source-boundary.json'),
                    'runner_sha256': r.sha(r.HERE/'retirement_replica.py'),
                    'probe_sha256': r.sha(r.HERE/'retirement_probe.php'),
                    'composer_lock_sha256': r.sha(checkout/'composer.lock'),
                    'supplementary_test_sha256': {'suite.php': r.sha(checkout/'suite.php')}}}
            r.save(out/'manifest.json', manifest)
            calls=[];client=Mock()
            client.health.return_value={'deployment': {'commit': 'synthetic'}}
            client.preflight_attempt.side_effect=lambda *a,**k: calls.append('preflight') or {'accepted': not refuse, 'kind': 'ainglish.attempt-preflight.v1'}
            client.mint_attempt.side_effect=lambda *a,**k: calls.append('mint') or {'attempt': {'attempt_id': 'synthetic'}}
            client.measure.side_effect=lambda *a,**k: calls.append(('measure',a[1])) or {'fixture': True}
            client.attempt.return_value={'attempt': {'state': 'open'}}
            client.abort_attempt.return_value={'fixture': 'aborted'}
            client.proposal.return_value={'fixture': 'after'}
            def command(*args,**kwargs):
                calls.append('command')
                self.assertIn('mint', calls)
                return SimpleNamespace(returncode=1 if fail else 0, stderr='',
                    stdout=json.dumps({'value': flip,'domain_count': 1}))
            with patch.object(r,'eligibility',return_value=({'manifest': manifest}, {})), \
                 patch.object(r,'source_boundary',return_value={'fixture': 'not a real boundary'}), \
                 patch.object(r.subprocess,'run',side_effect=command):
                kwargs=dict(client=client,checkout=checkout,out=out,php='never-executed',
                    freeze_url='https://example.invalid/immutable/fixture',
                    database_url='mysql://x:y@db/ainglish_retirement_replica_abcdefgh', accept_database=True)
                if fail or refuse:
                    with self.assertRaises((RuntimeError,ValueError)):r.run(**kwargs)
                else:r.run(**kwargs)
            return calls,client

    def test_mint_precedes_every_outcome_and_hash_is_in_both_places(self):
        calls,client=self.simulate(flip=1)
        self.assertEqual(['preflight','mint','command','command'], calls[:4])
        payload=client.measure.call_args.args[1]
        self.assertEqual(1,payload['value']) # nonzero must not be converted to zero
        self.assertEqual(r.TARGET,payload['replicates_hash'])
        self.assertEqual(r.TARGET,payload['manifest']['replicates_hash'])

    def test_failed_instrument_is_aborted_not_reported_as_zero(self):
        calls,client=self.simulate(fail=True)
        client.measure.assert_not_called();client.abort_attempt.assert_called_once()

    def test_preflight_refusal_never_mints_or_runs(self):
        calls,client=self.simulate(refuse=True)
        self.assertEqual(['preflight'],calls);client.mint_attempt.assert_not_called()


if __name__=='__main__':unittest.main()
