import random
import unittest
from quantity_oracle import *

class OracleTest(unittest.TestCase):
    def test_unknown_is_not_zero(self):
        self.assertEqual(symbolic(None,[('adjust',0)]),Expr(1,0))
        self.assertEqual(symbolic(None,[('set',0)]),Expr(0,0))
        q={'kind':'at_least','bound':1}
        self.assertEqual(classify(symbolic(None,[('adjust',0)]),0,q),UNKNOWN)
        self.assertEqual(classify(symbolic(None,[('set',0)]),0,q),NO)

    def test_known_zero_and_order(self):
        self.assertEqual(numeric(10,[('set',0)]),0)
        self.assertEqual(numeric(10,[('adjust',0)]),10)
        self.assertEqual(numeric(10,[('set',30),('adjust',5)]),35)
        self.assertEqual(numeric(10,[('adjust',5),('set',30)]),30)

    def test_correlated_unknowns_are_not_independent(self):
        q={'kind':'equal'}
        self.assertEqual(classify(Expr(1,7),0,q,Expr(1,7)),YES)
        self.assertEqual(classify(Expr(1,7),0,q,Expr(1,8)),NO)
        self.assertEqual(classify(Expr(1,7),0,q,Expr(0,20)),UNKNOWN)
        self.assertEqual(classify(Expr(1,7),20,q,Expr(0,20)),NO)
        self.assertEqual(classify(Expr(0,20),0,q,Expr(1,7)),UNKNOWN)

    def test_no_invented_operator_unit_or_order(self):
        text=render(10,10,[('adjust',5)],'timeout','seconds',True)
        for bad in [text.replace('adjust-by(+5 seconds)','5 seconds'),
                    text.replace('adjust-by(+5','adjust-by(5'),
                    text.replace('(+5 seconds)','(+5 GiB)'),
                    text.replace('written order','concurrent order')]:
            with self.assertRaises(ValueError):parse(bad)
        with self.assertRaises(ValueError):symbolic(None,[('missing',3)])
        with self.assertRaises(ValueError):parse(render(5,5,[('set',0),('adjust',-1)],'timeout','seconds',True))
        with self.assertRaises(ValueError):parse(render(None,0,[('adjust',-1)],'timeout','seconds',False))

    def test_exactly_one_exhaustive_answer_per_row_and_per_arm(self):
        items,keys=build()
        for item,key in zip(items,keys):
            self.assertEqual(set(item['choices'].values()),set(ANSWERS))
            self.assertEqual(item['choices'][key['answer']],key['meaning'])
            results=[]
            for arm in item['arms'].values():
                start,lower,ops,_,_=parse(arm)
                answer=classify(symbolic(start,ops),lower,key['query'],symbolic(start,key['other_operations']))
                results.append(answer)
            self.assertEqual(results,[key['meaning']]*2)

    def test_random_small_domain_oracle_against_numeric_witnesses(self):
        rng=random.Random(230923)
        for _ in range(200):
            start=rng.choice([None,0,5,20]);lower=rng.randrange(20)
            ops=[(rng.choice(['set','adjust']),rng.randrange(-10,30)) for _ in range(rng.randrange(1,4))]
            other=[(rng.choice(['set','adjust']),rng.randrange(-10,30)) for _ in range(2)]
            queries=[{'kind':'equal'},{'kind':'above','bound':rng.randrange(50)},
                     {'kind':'at_least','bound':rng.randrange(50)}, {'kind':'within','lo':0,'hi':rng.randrange(50)}]
            for q in queries:
                self.assertEqual(classify(symbolic(start,ops),lower,q,symbolic(start,other)),
                                 enumerate_truth(start,lower,ops,q,other))

if __name__=='__main__':unittest.main()
