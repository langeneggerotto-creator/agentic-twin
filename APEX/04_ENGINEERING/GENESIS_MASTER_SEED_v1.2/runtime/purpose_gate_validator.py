#!/usr/bin/env python3
from pathlib import Path
import argparse, json
from statistics import mean

REQ=["module_id","module_version","module_name","current_maturity","target_maturity","purpose_lock","scope_boundary","truth_boundary","evidence_ledger","risk_register","test_plan","promotion_gate"]
PUREQ=["real_job","human_benefit","whole_system_usefulness","apex_governing_law_alignment","truth_status"]
DECISIONS={"PROMOTE","PROMOTE_WITH_CONDITIONS","REPAIR","HOLD","BLOCK","ROLLBACK","RESEED"}
TRUTH={"PROVEN","TESTED","PROTOTYPED","DESIGNED","ASSUMED","UNKNOWN","BLOCKED","NOT_YET_BUILT"}
DIMS=["intent_alignment","human_benefit","whole_system_usefulness","evidence_awareness","scope_control","dignity_preservation","testability","reversibility","deployment_discipline","learning_value"]

def ok(v):
    return bool(v) if not isinstance(v,str) else bool(v.strip())

def scores(c):
    p=c.get("purpose_lock",{}); s=c.get("scope_boundary",{}); g=c.get("promotion_gate",{})
    return {
      "intent_alignment":1.0 if ok(p.get("apex_governing_law_alignment")) else 0.0,
      "human_benefit":1.0 if ok(p.get("human_benefit")) else 0.0,
      "whole_system_usefulness":1.0 if ok(p.get("whole_system_usefulness")) else 0.0,
      "evidence_awareness":1.0 if ok(c.get("evidence_ledger")) else 0.0,
      "scope_control":1.0 if ok(s.get("may_do")) and ok(s.get("may_not_do")) else 0.0,
      "dignity_preservation":1.0 if ok(c.get("risk_register")) else 0.0,
      "testability":1.0 if ok(c.get("test_plan")) else 0.0,
      "reversibility":1.0 if any("rollback" in str(x).lower() or "reseed" in str(x).lower() for x in c.get("risk_register",[])) else 0.7,
      "deployment_discipline":1.0 if g.get("requested_decision") in DECISIONS else 0.0,
      "learning_value":1.0 if any("learn" in str(x).lower() or "next" in str(x).lower() for x in c.get("test_plan",[])) else 0.7,
    }

def mse(sc):
    return mean((1.0-sc[d])**2 for d in DIMS)

def validate(c):
    fails=[]; warns=[]
    for k in REQ:
        if not ok(c.get(k)): fails.append("missing_required_field:"+k)
    p=c.get("purpose_lock",{})
    for k in PUREQ:
        if not ok(p.get(k)): fails.append("missing_purpose_lock_field:"+k)
    if p.get("truth_status") and p.get("truth_status") not in TRUTH: fails.append("invalid_truth_status")
    g=c.get("promotion_gate",{})
    if g.get("requested_decision") and g.get("requested_decision") not in DECISIONS: fails.append("invalid_requested_decision")
    if c.get("physical_action_requested") is True: fails.append("physical_action_requires_separate_human_safety_gate")
    if c.get("production_ready_claimed") is True:
        if c.get("current_maturity")!="PRODUCTION_READY": fails.append("production_ready_claim_without_production_maturity")
        if g.get("approval_status")!="approved": fails.append("production_ready_claim_without_human_approval")
    if g.get("approval_status")=="pending" and g.get("requested_decision")=="PROMOTE": warns.append("promotion_requested_with_pending_approval")
    sc=scores(c); m=round(mse(sc),10)
    decision="BLOCK" if fails else ("PROMOTE_WITH_CONDITIONS" if m>0.0000001 else g.get("requested_decision","PROMOTE"))
    return {"status":"VALIDATED","module_id":c.get("module_id"),"decision":decision,"failures":fails,"warnings":warns,"purpose_scores":sc,"mse_to_target":m,"target_mse":0.0000001,"truth_boundary":"Local purpose-gate validation only; not production enforcement until integrated with repository CI and review gates."}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("contract",type=Path); ap.add_argument("--output",type=Path)
    a=ap.parse_args(); r=validate(json.loads(a.contract.read_text(encoding="utf-8"))); txt=json.dumps(r,indent=2)
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(txt+"\n",encoding="utf-8")
    print(txt)
if __name__=="__main__": main()
