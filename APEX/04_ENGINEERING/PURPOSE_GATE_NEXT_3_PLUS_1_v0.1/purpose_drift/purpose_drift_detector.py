#!/usr/bin/env python3
from pathlib import Path
import argparse, json

def nonempty(v):
    if isinstance(v,str): return bool(v.strip())
    if isinstance(v,(list,dict)): return len(v)>0
    return v is not None

def detect(contract):
    p=contract.get('purpose_lock',{})
    signals=[]
    for field in ['real_job','human_benefit','whole_system_usefulness']:
        if not nonempty(p.get(field)):
            signals.append({'signal':'missing_'+field,'severity':'critical','decision':'BLOCK'})
    if not nonempty(contract.get('evidence_ledger')):
        signals.append({'signal':'missing_evidence_ledger','severity':'major','decision':'REPAIR_REQUIRED'})
    if not nonempty(contract.get('test_plan')):
        signals.append({'signal':'missing_test_plan','severity':'major','decision':'REPAIR_REQUIRED'})
    if contract.get('production_ready_claimed') and contract.get('promotion_gate',{}).get('approval_status')!='approved':
        signals.append({'signal':'production_ready_without_approval','severity':'critical','decision':'BLOCK'})
    decision='BLOCK' if any(s['decision']=='BLOCK' for s in signals) else ('REPAIR_REQUIRED' if signals else 'NO_DRIFT')
    return {'status':'DRIFT_CHECKED','module_id':contract.get('module_id'),'signals':signals,'decision':decision,'truth_boundary':'Local drift detector only; not live enforcement.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('module_contract',type=Path); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); r=detect(json.loads(a.module_contract.read_text(encoding='utf-8'))); txt=json.dumps(r,indent=2)
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(txt+'\n',encoding='utf-8')
    print(txt)
if __name__=='__main__': main()
