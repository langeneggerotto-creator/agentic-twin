import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"runtime"))
from purpose_gate_validator import validate, scores, mse

class PurposeGateTests(unittest.TestCase):
    def load(self,p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
    def test_pass_contract(self):
        r=validate(self.load("samples/pass/module_contract_pass.json"))
        self.assertEqual(r["failures"],[])
        self.assertIn(r["decision"],{"PROMOTE_WITH_CONDITIONS","PROMOTE"})
    def test_fail_contract_blocks(self):
        r=validate(self.load("samples/fail/module_contract_fail.json"))
        self.assertEqual(r["decision"],"BLOCK")
        self.assertTrue(r["failures"])
    def test_physical_action_blocks(self):
        c=self.load("samples/pass/module_contract_pass.json"); c["physical_action_requested"]=True
        self.assertIn("physical_action_requires_separate_human_safety_gate",validate(c)["failures"])
    def test_production_ready_requires_approval(self):
        c=self.load("samples/pass/module_contract_pass.json"); c["production_ready_claimed"]=True
        self.assertIn("production_ready_claim_without_production_maturity",validate(c)["failures"])
    def test_scores_normalized(self):
        self.assertTrue(all(0<=v<=1 for v in scores(self.load("samples/pass/module_contract_pass.json")).values()))
    def test_perfect_mse_zero(self):
        sc={k:1.0 for k in scores(self.load("samples/pass/module_contract_pass.json")).keys()}
        self.assertEqual(mse(sc),0.0)
if __name__=="__main__": unittest.main()
