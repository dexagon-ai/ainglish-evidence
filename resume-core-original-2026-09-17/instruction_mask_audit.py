"""Reproduce the visible-policy shortcut without the experimental instruction.

This is a deterministic design counterexample, not a model measurement.
The predictor receives text/question only: no gold, backend ID or strata.
"""
import json
from pathlib import Path
import re

def predict_without_instruction(text,question):
    context=text.rsplit('. ',1)[0]+'.'
    policies=set(re.findall(r'SAT-RR2-(?:media|reading|review|simulation)-(resume|redo)-[0-3]',context))
    if len(policies)!=1: return None
    policy=next(iter(policies))
    match=re.search(r'consists exactly of the four \w+ ([^,]+), ([^,]+), ([^,]+), and ([^,]+), in that order\.',context)
    if not match: return None
    units=list(match.groups())
    match=re.search(r'previously completed: (.*?)\. Saved record',context)
    if not match: return None
    completed=[] if match.group(1)=='none' else match.group(1).split(', ')
    match=re.search(r'if and only if (\w+) is (left unperformed|performed) during the forthcoming pass',question)
    if not match or match.group(1) not in units: return None
    probe,condition=match.groups()
    performed=policy=='redo' or probe not in completed
    lights=performed if condition=='performed' else not performed
    return 'Yes' if lights else 'No'

def audit(items):
    core=[x for x in items if not x.get('calibration')]
    arm_reports={}
    for arm in ['english','ainglish']:
        predictions=[predict_without_instruction(x[arm],x['question']) for x in core]
        arm_reports[arm]={'items':len(core),'predictions_without_instruction':sum(p is not None for p in predictions),
                          'correct_without_instruction':sum(p==x['answer'] for p,x in zip(predictions,core))}
    return arm_reports

if __name__=='__main__':
    root=Path(__file__).parent
    replica=json.loads((root/'saturnia-items.json').read_text())['items']
    original=json.loads((root/'runspec.json').read_text())['items']
    report={'kind':'ainglish.visible-policy-design-counterexample.v1',
            'replica':audit(replica),'original_negative_control':audit(original),
            'replica_cold_truthful_absence_options':sum(any('not specified' in o.lower() for o in x['options']) for x in replica if x.get('calibration')),
            'source_cold_truthful_absence_options':sum(any('not specified' in o.lower() for o in x['options']) for x in original if x.get('calibration')),
            'reader_calls':0,'not_a_measurement':True,
            'limits':'A concrete policy-labelled-ID shortcut only; failure of this predictor does not prove absence of every other shortcut.'}
    (root/'instruction-mask-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
