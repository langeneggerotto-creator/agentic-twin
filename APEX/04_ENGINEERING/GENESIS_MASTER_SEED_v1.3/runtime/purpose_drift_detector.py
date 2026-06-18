#!/usr/bin/env python3

def detect(contract):
    flags=[]
    purpose=contract.get('purpose_lock',{})
    for key in ['real_job','human_benefit','whole_system_usefulness']:
        if not purpose.get(key):
            flags.append('missing_purpose_signal:'+key)
    for key in ['evidence_ledger','truth_boundary','risk_register','test_plan']:
        if not contract.get(key):
            flags.append('missing_operating_signal:'+key)
    if contract.get('production_ready_claimed') is True:
        flags.append('production_ready_claim_requires_review')
    if contract.get('physical_action_requested') is True:
        flags.append('physical_action_requires_separate_safety_gate')
    drift_score=min(1.0,len(flags)/8)
    if drift_score==0:
        decision='NO_DRIFT'
    elif drift_score<0.25:
        decision='WATCH'
    elif drift_score<0.75:
        decision='REPAIR'
    else:
        decision='BLOCK'
    return {'module_id':contract.get('module_id'),'drift_score':round(drift_score,3),'decision':decision,'flags':flags}
