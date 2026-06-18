import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime'))
from agentic_aai_purpose_gate_adapter import decide

class AgenticAAIAdapterTests(unittest.TestCase):
    def load(self, rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
    def test_pass_promotes_with_conditions(self):
        r=decide(self.load('samples/pass/purpose_gate_result_pass.json'), self.load('samples/pass/promotion_request_pass.json'))
        self.assertEqual(r['decision'],'PROMOTE_WITH_CONDITIONS')
    def test_block_when_purpose_gate_blocks(self):
        r=decide(self.load('samples/block/purpose_gate_result_block.json'), self.load('samples/block/promotion_request_block.json'))
        self.assertIn(r['decision'], {'BLOCK','HOLD'})
        self.assertTrue(r['failures'])
    def test_merge_requires_approval(self):
        pg=self.load('samples/pass/purpose_gate_result_pass.json')
        req=self.load('samples/pass/promotion_request_pass.json'); req['requested_actions']=['merge_to_main']; req['approval_status']='pending'
        r=decide(pg,req)
        self.assertEqual(r['decision'],'HOLD')
    def test_missing_evidence_blocks(self):
        pg=self.load('samples/pass/purpose_gate_result_pass.json')
        req=self.load('samples/pass/promotion_request_pass.json'); req['evidence_refs']=[]
        r=decide(pg,req)
        self.assertEqual(r['decision'],'BLOCK')
    def test_approved_merge_no_auto_production_claim(self):
        pg={'decision':'PROMOTE','failures':[],'warnings':[],'module_id':'x'}
        req={'module_id':'x','requested_actions':['merge_to_main'],'approval_status':'approved','evidence_refs':['e']}
        r=decide(pg,req)
        self.assertEqual(r['decision'],'PROMOTE')

if __name__=='__main__': unittest.main()
