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

    def test_real_public_null_and_retraction_receipt_shapes(self):
        client = Mock()
        client.whoami.return_value = {'sub': 'synthetic-independent'}
        client.suggestions.return_value = {'suggestions': [
            {'replicates_hash': r.TARGET, 'executable_now': True}]}
        client.proposal.return_value = {'public_id': r.PID, 'stage': 'seconded'}
        source = {'submitter': {'sub': 'synthetic-original'}, 'evidence_state': 'valid',
                  'is_replication': False, 'retraction': None}
        client.measurement.return_value = source
        self.assertIs(source, r.eligibility(client)[0])
        for receipt in [{'reason': 'synthetic audit correction', 'at': '2026-09-12T00:00:00Z',
                         'replacement': None}, {}, False, 'malformed']:
            source['retraction'] = receipt
            with self.subTest(receipt=receipt), self.assertRaisesRegex(ValueError, 'valid effective original'):
                r.eligibility(client)
        client.mint_attempt.assert_not_called()

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

    def test_wrong_autoload_checkout_refuses(self):
        with patch.object(r.subprocess,'run',return_value=SimpleNamespace(returncode=1)):
            with self.assertRaisesRegex(ValueError,'autoload provenance'):
                r.runtime_source_check(Path('/invented-fixture'),'not-executed')

    def simulate(self, fail=False, refuse=False, flip=0, preparation=None, tamper=False):
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
            if tamper:
                (checkout/'suite.php').write_text('changed synthetic test fixture')
            calls=[];client=Mock()
            client.health.return_value={'deployment': {'commit': 'synthetic'}}
            client.preflight_attempt.side_effect=lambda *a,**k: calls.append('preflight') or {'accepted': not refuse, 'kind': 'ainglish.attempt-preflight.v1', 'replication_preparation': preparation}
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
                 patch.object(r,'runtime_source_check'), \
                 patch.object(r.subprocess,'run',side_effect=command):
                kwargs=dict(client=client,checkout=checkout,out=out,php='never-executed',
                    freeze_url='https://example.invalid/immutable/fixture',
                    database_url='mysql://x:y@db/ainglish_retirement_replica_abcdefgh', accept_database=True)
                if fail or refuse or preparation is not None or tamper or type(flip) is not int or not 0 <= flip <= 1:
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

    def test_instrument_changed_after_freeze_never_mints(self):
        calls,client=self.simulate(tamper=True)
        self.assertEqual([],calls);client.mint_attempt.assert_not_called()

    def test_preparation_obstruction_is_not_overridden_by_accepted_preflight(self):
        for preparation in [{'status':'known_obstruction','known_obstructions':['invented']},
                            {'status':'no_known_obstruction','known_obstructions':['invented']},
                            {'status':'unknown','known_obstructions':[]}]:
            with self.subTest(preparation=preparation):
                calls,client=self.simulate(preparation=preparation)
                self.assertEqual(['preflight'],calls)
                client.mint_attempt.assert_not_called()

    def test_invalid_count_is_retained_and_aborted_not_filed(self):
        for flip in [True, -1, 2, .5, None]:
            with self.subTest(flip=flip):
                calls,client=self.simulate(flip=flip)
                client.measure.assert_not_called()
                client.abort_attempt.assert_called_once()

    def test_source_state_and_unique_offer_are_required(self):
        def client():
            c=Mock()
            c.whoami.return_value={'sub':'independent'}
            c.measurement.return_value={'submitter':{'sub':'author'},'evidence_state':'valid'}
            c.proposal.return_value={'public_id':r.PID,'stage':'seconded'}
            c.suggestions.return_value={'suggestions':[{'replicates_hash':r.TARGET,'executable_now':True}]}
            return c
        for change in [{'is_replication':True},{'evidence_state':'invalid'},
                       {'retraction':{'retracted':True}}]:
            c=client();c.measurement.return_value.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):r.eligibility(c)
            c.mint_attempt.assert_not_called()
        c=client();c.suggestions.return_value['suggestions']*=2
        with self.assertRaises(ValueError):r.eligibility(c)
        c=client();c.proposal.return_value['stage']='withdrawn'
        with self.assertRaises(ValueError):r.eligibility(c)
        c=client();c.proposal.return_value['public_id']='invented-other'
        with self.assertRaises(ValueError):r.eligibility(c)

    def test_changed_census_detail_refuses(self):
        c={'records':[{'public_id':'invented','stage':'withdrawn'}],
           'withdrawn_details':{'invented':{'public_id':'invented','stage':'seconded','full_measurement_envelopes':True}}}
        with self.assertRaises(ValueError):r.validate_census(c)

    def test_source_only_guard_rejects_extra_causal_change(self):
        before='    public function assess(Proposal $p): void\n    {\n        '+r.OLD+'\n            return;\n        }\n    }\n\n    /** end */'
        after=before.replace(r.OLD,r.NEW)
        current=after.replace('return;','return; /* extra causal change */')
        with patch.object(r,'git',side_effect=[before,after,current]):
            with self.assertRaisesRegex(ValueError,'drifted'):
                r.source_boundary(Path('/invented-not-executed'),'invented')


if __name__=='__main__':unittest.main()
