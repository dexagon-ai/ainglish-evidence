import copy
import unittest
import remote_handoffs as h


class RemoteHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states=h.load(h.HERE/'reader-proposal-snapshots.json')

    def test_three_actual_packets_no_readers_or_claimed_outcomes(self):
        r=h.build(self.states)
        self.assertFalse(r['executable']);self.assertFalse(r['measurement'])
        self.assertEqual([64,96,64],[p['target_count'] for p in r['packages']])
        self.assertEqual([144,112,80],[p['call_budget_per_reader']['total'] for p in r['packages']])
        for p in r['packages']:
            self.assertEqual('prepared_not_run',p['status'])
            self.assertEqual([],p['reader_qualifications'])
            self.assertEqual([],p['accepted_executors'])
            self.assertIsNone(p['scientific_attempt_id'])
            self.assertEqual(0,p['reader_calls_made'])

    def test_changed_claim_stays_held(self):
        states=copy.deepcopy(self.states)
        states['sanction']['predicted_measurement']='invented changed claim'
        r=h.build(states)['packages'][2]
        self.assertEqual('hold_changed_proposal',r['status'])
        self.assertEqual(['predicted_measurement'],r['changed_proposal_fields'])

    def test_sanction_two_lineage_requirement_is_not_relaxed(self):
        p=h.build(self.states)['packages'][2]
        self.assertEqual('not_allowed_by_declared_sanction_plan',p['reader_scope']['one_lineage_option'])


if __name__=='__main__':unittest.main()
