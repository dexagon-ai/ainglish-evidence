import copy
import json
import unittest
import audit as a


class RetainedAuditTests(unittest.TestCase):
    def setUp(self):
        self.bank = json.loads((a.SOURCE / 'items.json').read_text())
        self.measurement = json.loads((a.SOURCE / 'measurement.json').read_text())
        self.science = json.loads((a.ROOT / 'scientific_cells.json').read_text())['rows']
        self.calibration = json.loads((a.ROOT / 'calibration_cells.json').read_text())['rows']

    def check(self):
        return a.audit_rows(self.bank, self.measurement, self.science, self.calibration)

    def test_pinned_complete_audit(self):
        self.assertEqual(a.audit()['scientific_correct'], 150)
        self.assertFalse(a.audit()['demonstrated_grading_error'])

    def test_missing_scientific_cell(self):
        self.science.pop()
        with self.assertRaises(AssertionError): self.check()

    def test_duplicated_scientific_cell(self):
        self.science[1] = copy.deepcopy(self.science[0])
        with self.assertRaises(AssertionError): self.check()

    def test_wrong_grade(self):
        self.science[0]['correct'] = not self.science[0]['correct']
        with self.assertRaises(AssertionError): self.check()

    def test_unknown_answer(self):
        self.science[0]['answer'] = 'not-an-option'
        with self.assertRaises(AssertionError): self.check()

    def test_gold_drift(self):
        self.science[0]['expected'] = 'no'
        with self.assertRaises(AssertionError): self.check()

    def test_assignment_drift(self):
        self.science[0]['arm'] = 'english' if self.science[0]['arm'] == 'ainglish' else 'ainglish'
        with self.assertRaises(AssertionError): self.check()

    def test_calibration_coverage(self):
        self.calibration[1] = copy.deepcopy(self.calibration[0])
        with self.assertRaises(AssertionError): self.check()

    def test_boolean_journal_drift(self):
        cell = self.measurement['interval_provenance_attestation']['cells'][0]
        cell['correct'] = not cell['correct']
        with self.assertRaises(AssertionError): self.check()


if __name__ == '__main__': unittest.main()
