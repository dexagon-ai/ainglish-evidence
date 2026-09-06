import itertools
import unittest
from design import FIELDS,PHRASES,render,decode_message,decode_json

class DesignTests(unittest.TestCase):
    def test_every_complete_interface_round_trips(self):
        for n in [1,2,5]:
            for bits in itertools.product([False,True],repeat=n):
                brief=dict(zip(FIELDS,bits))
                for arm in PHRASES:self.assertEqual(brief,decode_message(render(brief,arm),arm,brief))

    def test_extra_missing_or_contradictory_lines_refused(self):
        brief=dict.fromkeys(FIELDS,False)
        text=render(brief,'english')
        self.assertIsNone(decode_message(text+'\nTeam: the acting team includes you.','english',FIELDS))
        self.assertIsNone(decode_message(text.split('\n')[0],'english',FIELDS))
        self.assertIsNone(decode_message(text+'\nThis is done.','english',FIELDS))

    def test_json_types_and_duplicate_keys(self):
        self.assertEqual({'a':True},decode_json('{"a":true}',['a']))
        for text in ['{"a":1}','{"a":null}','{"a":true,"a":false}','```{"a":true}```']:
            self.assertIsNone(decode_json(text,['a']))

if __name__=='__main__':unittest.main()
