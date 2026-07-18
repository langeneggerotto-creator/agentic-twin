#!/usr/bin/env python3
from pathlib import Path
import argparse, json

BASE={'PROMOTE':10,'PROMOTE_WITH_CONDITIONS':8,'REPAIR':6,'HOLD':5,'BLOCK':0,'ROLLBACK':1,'RESEED':2}
CEILING={'PROMOTE':'PROMOTE','PROMOTE_WITH_CONDITIONS':'PROMOTE_WITH_CONDITIONS','REPAIR':'REPAIR','HOLD':'HOLD','BLOCK':'BLOCK','ROLLBACK':'ROLLBACK','RESEED':'RESEED'}

def adapt(purpose_gate_result):
    decision=purpose_gate_result.get('decision','HOLD')
    failures=purpose_gate_result.get('failures',[])
    warnings=purpose_gate_result.get('warnings',[])
    approval_required=bool(purpose_gate_result.get('approval_required',False))
    score=BASE.get(decision,5)-min(len(failures)*2,5)-min(len(warnings),2)
    if approval_required and purpose_gate_result.get('approval_status')!='approved': score-=1
    score=max(0,min(10,score))
    ceiling='BLOCK' if failures or decision=='BLOCK' else CEILING.get(decision,'HOLD')
    return {'status':'ADAPTED','taste_dimension':'Purpose Gate Alignment','purpose_gate_decision':decision,'taste_purpose_gate_score':score,'taste_verdict_ceiling':ceiling,'promotion_allowed':ceiling=='PROMOTE','truth_boundary':'Local adapter proof only; does not promote, merge, deploy, or override approval gates.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('purpose_gate_result',type=Path); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); r=adapt(json.loads(a.purpose_gate_result.read_text(encoding='utf-8'))); txt=json.dumps(r,indent=2)
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(txt+'\n',encoding='utf-8')
    print(txt)
if __name__=='__main__': main()
