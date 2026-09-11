"""Audit retained public cells without another reader call or changing evidence."""
import argparse
from collections import Counter, defaultdict
import hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
PREFIX='evening-progression-2026-09-07/readers/should/'
SOURCE='abdb20658d870dc38340e12cc02a0725f77c2ed40651114899b655a55b0bf1d1'
REPLICA='b72bc1a26957199c3f28151c64775276530973a11cc81ee0ac6384fe7f1c773f'
ITEM_PIN='a4e6fc8871fccae2bcc55e3dae0b7b1179c9930a4139c4a2ea6bdc8512ccf70c'
POSITIVE='A departure from an invoked standard is established by this statement.'


def git_json(path):
    return json.loads(subprocess.check_output(['git','-C',str(REPO),'show','1c4a58a:'+PREFIX+path],text=True))


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def audit(items,cells):
    real=[i for i in items if not i.get('calibration')]
    by_id={i['id']:i for i in real}
    groups=defaultdict(list);errors=[];seen=set()
    for c in cells:
        key=(c['item_id'],c['reader'])
        if key in seen:errors.append('duplicate item-reader cell: '+str(key))
        seen.add(key)
        i=by_id[c['item_id']]
        if c['expected']!=i['answer']:errors.append('cell expected differs from frozen item: '+i['id'])
        if c['correct'] != (c['answer']==i['answer']):errors.append('incorrect scoring flag: '+i['id'])
        if (i['answer']==POSITIVE)!=i['oracle']['invokes_applicable_requirement']:
            errors.append('gold differs from declared world oracle: '+i['id'])
        if c['answer'] not in i['options']:errors.append('answer outside allowed choices: '+i['id'])
        row=dict(c,gold_position=i['options'].index(i['answer']),answer_position=i['options'].index(c['answer']),aspect=i['aspect'])
        for group in [(i['settlement_stratum'],c['arm'],'all'),
                      (i['settlement_stratum'],c['arm'],c['reader'])]:groups[group].append(row)
    tables=[]
    for (stratum,arm,reader),rows in sorted(groups.items()):
        tables.append({'stratum':stratum,'arm':arm,'reader':reader,'n':len(rows),
            'correct':sum(r['correct'] for r in rows),'accuracy':sum(r['correct'] for r in rows)/len(rows),
            'negative_option_selections':sum(r['answer']!=POSITIVE for r in rows),
            'gold_positions':dict(Counter(r['gold_position'] for r in rows)),
            'chosen_positions':dict(Counter(r['answer_position'] for r in rows)),
            'by_gold_position':{str(pos):{'n':len(part),'correct':sum(r['correct'] for r in part)}
                for pos in [0,1] if (part:=[r for r in rows if r['gold_position']==pos])},
            'by_aspect':{aspect:{'n':len(part),'correct':sum(r['correct'] for r in part)}
                for aspect in ['plain','perfect'] if (part:=[r for r in rows if r['aspect']==aspect])}})
    return {'real_items':len(real),'cells':len(cells),'scoring_errors':errors,'groups':tables,
        'independent_semantic_check':{'rule': 'Applicable procedure calls for P; failure of P is departure from that procedure.',
            'forecast': 'An expectation explicitly specifies no obligation; failure does not by itself establish departure from an applicable standard.',
            'boundary':'A semantic review, not reader data. The premise does not exclude undisclosed other standards.'}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    items=git_json('items.json')
    if digest(items)!=ITEM_PIN:raise ValueError('Frozen item digest changed')
    cells=git_json('execution/should-careful.attempt-84d921a0-da6a-4802-a968-78c3309272fd.cells.json')
    result={'kind':'retained-should-integrity-audit.v1','measurement':False,'reader_calls':0,
        'source':SOURCE,'replication_context':REPLICA,'items_sha256':digest(items),
        'cells_sha256':digest(cells),'source_commit':'1c4a58a',**audit(items,cells['rows']),
        'interpretation':['No scoring or gold-oracle inconsistency is established by these checks.',
            'Below-chance English suggests an insensitive instrument for this task, not proof of a malformed question.',
            'Changing readers and items together does not isolate reader, preamble, option wording, position or budget.',
            'Source used qualified Falcon3/OLMo2 q4 readers with max_tokens 64; remote replica used a DeepSeek pair and 65536. Do not call them the same instrument.',
            'No row is retracted, invalidated, relabelled or independently confirmed by this audit.']}
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:result[k] for k in ['real_items','cells','scoring_errors','reader_calls']}))


if __name__=='__main__':main()
