import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'taste_console'))
sys.path.insert(0,str(ROOT/'purpose_drift'))
from taste_purpose_gate_adapter import adapt
from purpose_drift_detector import detect
class Next3Plus1Tests(unittest.TestCase):
    def test_taste_blocks_block(self):
        r=adapt({'decision':'BLOCK','failures':['missing_purpose_lock'],'warnings':[],'approval_required':True})
        self.assertEqual(r['taste_verdict_ceiling'],'BLOCK')
    def test_taste_conditions(self):
        r=adapt({'decision':'PROMOTE_WITH_CONDITIONS','failures':[],'warnings':['approval pending'],'approval_required':True})
        self.assertEqual(r['taste_verdict_ceiling'],'PROMOTE_WITH_CONDITIONS')
    def test_drift_blocks_bad_contract(self):
        r=detect({'module_id':'bad','purpose_lock':{},'evidence_ledger':[],'test_plan':[],'promotion_gate':{'approval_status':'pending'},'production_ready_claimed':True})
        self.assertEqual(r['decision'],'BLOCK')
    def test_drift_no_block_for_pass_contract(self):
        r=detect({'module_id':'ok','purpose_lock':{'real_job':'x','human_benefit':'y','whole_system_usefulness':'z'},'evidence_ledger':[{}],'test_plan':['test'],'promotion_gate':{},'production_ready_claimed':False})
        self.assertNotEqual(r['decision'],'BLOCK')
    def test_dashboard_exists(self):
        self.assertTrue((ROOT/'dashboard/PURPOSE_GATE_STATUS_DASHBOARD.html').exists())
if __name__=='__main__': unittest.main()
