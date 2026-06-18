import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime'))
from purpose_gate_validator import validate
from purpose_drift_detector import detect
from apex_automation_orchestrator import run

class V13Tests(unittest.TestCase):
    def load(self,p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
    def test_pass_orchestrates(self): self.assertIn(run(self.load('samples/pass/module_contract_pass.json'))['decision'], {'PROMOTE_WITH_CONDITIONS','PROMOTE'})
    def test_fail_blocks(self): self.assertEqual(run(self.load('samples/fail/module_contract_fail.json'))['decision'],'BLOCK')
    def test_no_drift_pass(self): self.assertEqual(detect(self.load('samples/pass/module_contract_pass.json'))['decision'],'NO_DRIFT')
    def test_fail_drift_blocks(self): self.assertEqual(detect(self.load('samples/fail/module_contract_fail.json'))['decision'],'BLOCK')
    def test_physical_blocks(self):
        c=self.load('samples/pass/module_contract_pass.json'); c['physical_action_requested']=True
        self.assertIn('physical_action_requires_separate_human_safety_gate', validate(c)['failures'])
    def test_production_claim_blocks(self):
        c=self.load('samples/pass/module_contract_pass.json'); c['production_ready_claimed']=True
        self.assertIn('production_ready_claim_without_production_maturity', validate(c)['failures'])

if __name__=='__main__': unittest.main()
