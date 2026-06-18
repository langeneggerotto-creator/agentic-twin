#!/usr/bin/env python3
from pathlib import Path
import argparse,json
from purpose_gate_validator import validate
from purpose_drift_detector import detect

def run(contract):
    gate=validate(contract)
    drift=detect(contract)
    if gate['decision']=='BLOCK' or drift['decision']=='BLOCK':
        decision='BLOCK'
    elif drift['decision']=='REPAIR':
        decision='REPAIR'
    elif gate['decision']=='PROMOTE_WITH_CONDITIONS' or drift['decision']=='WATCH':
        decision='PROMOTE_WITH_CONDITIONS'
    else:
        decision='PROMOTE'
    return {
        'status':'ORCHESTRATED',
        'module_id':contract.get('module_id'),
        'purpose_gate':gate,
        'purpose_drift':drift,
        'decision':decision,
        'human_approval_required':decision in {'PROMOTE','PROMOTE_WITH_CONDITIONS'},
        'truth_boundary':'Local automation orchestration only; no merge, production, public release, or physical action.'
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('contract',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=run(json.loads(args.contract.read_text(encoding='utf-8')))
    text=json.dumps(result,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text+'\n',encoding='utf-8')
    print(text)

if __name__=='__main__':
    main()
