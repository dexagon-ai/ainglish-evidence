import unittest
from study import decode_json,reader_messages

class ParserTest(unittest.TestCase):
    def testBareAndSingleFence(self):
        for raw in ['{"a":true}','```json\n{"a":true}\n```','```\n{"a":true}\n```']:
            self.assertEqual({'a':True},decode_json(raw,{'a':True}))
    def testNoCommentaryCoercionOrMultipleObjects(self):
        for raw in ['Explanation\n{"a":true}','{"a":true,"a":false}','{"a":1}','{"a":true,"b":false}','```json\n{"a":true}\n``` trailing','{"a":true}{"a":false}']:
            self.assertIsNone(decode_json(raw,{'a':True}))
    def testTargetInstructionMatchesDeclaredWrapperProtocol(self):
        case={'brief':{'include_recipient':True},'context':'A neutral test context.'}
        messages=reader_messages(case,'ainglish','we-including-you')
        self.assertIn('single JSON code fence is accepted',messages[0]['content'])

if __name__=='__main__':unittest.main()
