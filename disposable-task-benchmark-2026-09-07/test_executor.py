from itertools import product
import unittest
from executor import execute,success,validate,follows_intended_plan

class ExecutorTest(unittest.TestCase):
    def testAllEightChoicesPerformTheDeclaredLocalIo(self):
        for team,work,deadline in product(['include','exclude'],['each','one'],['start','complete']):
            choice=dict(team=team,work=work,deadline=deadline)
            fixture=b'{"inventory":["camera","tripod"]}'
            result=execute(choice,fixture,instrument_qualified=True)
            self.assertTrue(follows_intended_plan(result,choice))
            self.assertEqual(deadline=='start',success(result,choice,fixture))
            self.assertFalse(success(result,choice,b'{"inventory":[]}'))
            self.assertEqual(work=='one' and 1 or (3 if team=='include' else 2),len(result['artifacts']))
            self.assertEqual(deadline=='start',result['requested_deadline_met'])
            self.assertTrue(result['temporary_files_removed_on_return'])
    def testQualificationIsNotOptional(self):
        with self.assertRaisesRegex(RuntimeError,'qualification'):
            execute({'team':'include','work':'each','deadline':'start'},b'{"inventory":[]}')
    def testCommandsAndPathLikeValuesAreRefused(self):
        base={'team':'include','work':'each','deadline':'start'}
        for value in ['../../file','rm -rf',None,True,[],{}]:
            with self.assertRaises(ValueError):validate(dict(base,team=value))
        with self.assertRaises(ValueError):validate(dict(base,path='/tmp/a'))

if __name__=='__main__':unittest.main()
