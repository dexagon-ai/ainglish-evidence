import unittest
from finish import table

class ReportTest(unittest.TestCase):
    def test_missing_false_and_true_stay_separate(self):
        rows=[{'id':'archive/0','arm':'english','correct':True},
              {'id':'archive/1','arm':'english','correct':False},
              {'id':'archive/2','arm':'english','correct':None},
              {'id':'theatre/0','arm':'ainglish','correct':False}]
        out=table(rows,['correct'])
        self.assertEqual(out[0],{'context':'archive','arm':'english','n':3,'correct':{'true':1,'false':1,'missing':1}})
        self.assertEqual(out[1]['correct'],{'true':0,'false':1,'missing':0})
        self.assertEqual(table([],['correct']),[])

if __name__=='__main__':unittest.main()
