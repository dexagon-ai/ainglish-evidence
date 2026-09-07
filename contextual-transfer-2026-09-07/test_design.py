import unittest
from build import structural,labelled,FRAME_NAMES,general
from analyse import contrast

class DesignTest(unittest.TestCase):
    def test_every_arm_has_the_same_question_gold_and_distinct_surface(self):
        for family in FRAME_NAMES:
            for frame in range(4):
                for i in range(8):
                    a,q,g=structural(family,frame,i,'ainglish');e,eq,eg=structural(family,frame,i,'english')
                    self.assertEqual((q,g),(eq,eg));self.assertNotEqual(a,e);self.assertEqual(2,len(g))
                    self.assertTrue(all(isinstance(x,bool) for x in g))
    def test_decisive_boundaries_not_just_recomputed_answer_keys(self):
        self.assertEqual((False,True),structural('deadline',0,1,'ainglish')[2]) # completion late
        self.assertEqual((True,True),structural('deadline',0,3,'ainglish')[2]) # completion exactly at deadline
        self.assertEqual((False,False),structural('deadline',1,1,'ainglish')[2]) # terminal failure is not success
        self.assertEqual((False,False),structural('deadline',3,0,'ainglish')[2]) # acknowledgement and queueing do not begin
        self.assertEqual((False,True),structural('alternatives',0,1,'ainglish')[2]) # inclusive does not permit neither
        self.assertEqual((False,False),structural('alternatives',0,6,'ainglish')[2]) # exclusive rejects both
        self.assertEqual((True,False),structural('alternatives',3,3,'ainglish')[2]) # separate capacity rule still binds
        self.assertEqual((True,False),structural('update',1,0,'ainglish')[2]) # uncommitted successor not active
        self.assertEqual((False,True),structural('update',1,2,'ainglish')[2]) # committed replacement retires B
        self.assertEqual((False,True),structural('update',2,2,'ainglish')[2]) # printed history remains
        for i in [0,1,2]:self.assertEqual((False,True),structural('update',3,i,'ainglish')[2])
        self.assertEqual((True,False),structural('update',3,3,'ainglish')[2])
    def test_labels_and_ordinary_data_are_frozen_disjoint_instances(self):
        for i in range(192):
            r=general(i,'rehearsal');t=general(i,'retention')
            self.assertNotEqual(r['messages'],t['messages']);self.assertEqual(r['options'][r['answer']],r['semantic_gold'])
        for i in range(4):
            opts,letter=labelled(['v','w','x','y'],'w',i);self.assertEqual('ABCD'[i],letter);self.assertEqual('w',opts[letter])
    def test_cluster_interval_retains_adverse_sign(self):
        a=[{'case_id':str(i),'frame':str(i//2),'correct':False} for i in range(8)]
        b=[{**r,'correct':True} for r in a]
        result=contrast(a,b);self.assertEqual(-100,result['delta_pp']);self.assertEqual([-100,-100],result['exploratory_frame_cluster_95'])
        with self.assertRaises(AssertionError):contrast(a,b[:-1])

if __name__=='__main__':unittest.main()
