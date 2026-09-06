import argparse
import json
import sys
from pathlib import Path
from design import ROOT,FIELDS,reader_messages,sender_messages,decode_json,decode_message
sys.path.insert(0,str(ROOT.parent/'overnight-runtime-2026-09-06'))
from runtime import Journal,LocalReader,save_new,verify_freeze

def main(resume=False):
    freeze=verify_freeze(ROOT)
    plan=json.loads((ROOT/'PLAN.json').read_text()); cases=json.loads((ROOT/'cases.json').read_text())
    controls=json.loads((ROOT/'controls.json').read_text())
    with Journal(ROOT/'results/base.jsonl', {'freeze':freeze,**plan}, resume=resume) as journal:
        reader=LocalReader(plan['snapshot'])
        if not (ROOT/'results/base-provenance.json').exists():save_new(ROOT/'results/base-provenance.json',reader.provenance)
        screening={'reader':[],'writer':[]}
        for c in controls:
            r=reader.call(journal,'control/reader/'+c['id'],c['messages'],cap=plan['receiver_cap'])
            screening['reader'].append({'id':c['id'],'correct':r['ended'] and decode_json(r['raw'],c['brief'])==c['brief'],'ended':r['ended']})
            r=reader.call(journal,'control/writer/'+c['id'],c['writer_messages'],cap=plan['sender_cap'])
            screening['writer'].append({'id':c['id'],'correct':r['ended'] and r['raw'].strip().casefold()==c['writer_gold'].casefold(),'ended':r['ended']})
        passed=all(sum(r['correct'] for r in rows)>=plan['minimum_control_correct'] and all(r['ended'] for r in rows) for rows in screening.values())
        if not (ROOT/'results/qualification.json').exists(): save_new(ROOT/'results/qualification.json',{'passed':passed,'roles':screening,'target_calls_before_qualification':0})
        print('Qualification',passed,{k:sum(r['correct'] for r in rows) for k,rows in screening.items()},flush=True)
        if not passed:return
        count=0
        for case in cases:
            for arm in plan['arms']:
                key=case['id']+'/'+arm
                reader.call(journal,'reference/'+key,reader_messages(case,arm,case['messages'][arm]),cap=plan['receiver_cap'])
                count+=1
                if case['dimensions']==5:
                    source=reader.call(journal,'sender/'+key,sender_messages(case,arm),cap=plan['sender_cap'])
                    reader.call(journal,'handoff/'+key,reader_messages(case,arm,source['raw']),cap=plan['receiver_cap'])
                    count+=2
                if count%24==0:print('Recorded targets',count,'/',plan['target_calls'],flush=True)
        save_new(ROOT/'results/finished.json',{'status':'complete','target_calls':count,'control_calls':16,'freeze':freeze,'downloads':0})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');a=p.parse_args();main(a.resume)
