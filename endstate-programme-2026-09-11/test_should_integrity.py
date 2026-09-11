import unittest
from should_integrity import audit,POSITIVE

class ShouldIntegrityTests(unittest.TestCase):
    def fixture(self):
        item={'id':'synthetic','answer':POSITIVE,'options':[POSITIVE,'No'], 'settlement_stratum':'rule',
              'oracle':{'invokes_applicable_requirement':True},'aspect':'plain'}
        cell={'item_id':'synthetic','reader':'invented','arm':'english','expected':POSITIVE,'answer':POSITIVE,'correct':True}
        return item,cell
    def test_detects_wrong_scoring_flag(self):
        i,c=self.fixture();c['correct']=False
        self.assertTrue(audit([i],[c])['scoring_errors'])
    def test_detects_declared_gold_mismatch(self):
        i,c=self.fixture();i['oracle']['invokes_applicable_requirement']=False
        self.assertTrue(audit([i],[c])['scoring_errors'])
    def test_detects_duplicate_cell(self):
        i,c=self.fixture();self.assertTrue(audit([i],[c,c])['scoring_errors'])
    def test_legitimate_wrong_response_is_not_scoring_defect(self):
        i,c=self.fixture();c.update(answer='No',correct=False)
        self.assertEqual([],audit([i],[c])['scoring_errors'])

if __name__=='__main__':unittest.main()
