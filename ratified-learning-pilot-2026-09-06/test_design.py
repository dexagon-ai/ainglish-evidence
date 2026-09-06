import unittest
import tempfile
import zipfile
from pathlib import Path
from audit import validate
from build import row, messages
from export_training import export, ALLOWED


class DesignTests(unittest.TestCase):
    def test_complete_design(self):
        self.assertEqual('pass',validate()['status'])

    def test_no_answer_in_reader_metadata(self):
        case=row('update','observatory',4,'test')
        reader=messages(case,'ainglish-cold')
        self.assertEqual(['system','user'],[m['role'] for m in reader])
        self.assertNotIn(case['id'],reader[1]['content'])

    def test_reference_is_explicit(self):
        case=row('deadline','observatory',4,'test')
        self.assertNotIn('Reading reference:',messages(case,'ainglish-cold')[1]['content'])
        self.assertIn('Reading reference:',messages(case,'ainglish-reference')[1]['content'])
        self.assertIn('Reading reference:',messages(case,'english-reference')[1]['content'])

    def test_labels_do_not_determine_meaning(self):
        answers=[row('participants','observatory',v,'test') for v in range(8)]
        yes=[r['answer'] for r in answers if r['options'][r['answer']]=='Yes']
        self.assertGreater(len(set(yes)),1)

    def test_export_excludes_evaluation_and_is_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            first=Path(directory)/'first.zip';second=Path(directory)/'second.zip'
            self.assertEqual(export(first)['sha256'],export(second)['sha256'])
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(set(ALLOWED)|{'README.txt','MANIFEST.json'},set(archive.namelist()))
                self.assertNotIn('evaluation.jsonl',archive.namelist())
                self.assertFalse(any('results' in n for n in archive.namelist()))
            with self.assertRaises(ValueError):export(first)


if __name__=='__main__': unittest.main()
