"""Control-concept fixtures and fail-closed scoring. No inference or SDK filing.

The ninety prompts below are thirty semantic control templates, each rendered
in three option orders. These are review witnesses, not ninety independent
worlds, a final language bank, or planted-effect SDK calibration items.
"""
from collections import Counter
import json
from pathlib import Path

LABELS=['Yes','No','Not established by the record']
FORMS=['they-one','they-many']
SPECS={
 'gender':{
  'question':'Is every referent a woman?',
  'referents':{'they-one':'The referent is one person.','they-many':'The referents are two people.'},
  'facts':[
   'The verified profiles explicitly state that every referent is a woman.',
   'The verified profiles explicitly state that at least one referent is not a woman.',
   'The record provides no gender information about any referent.'
  ]},
 'known_identity':{
  'question':'Does the recorder know the identity of every referent?',
  'referents':{'they-one':'The report concerns one referent.','they-many':'The report concerns two referents.'},
  'facts':[
   'The recorder has verified the identity of every referent against the authoritative identity register.',
   'The recorder explicitly states that the identity of at least one referent remains unknown to the recorder.',
   'The report says nothing about whether the recorder knows the identities of the referents.'
  ]},
 'unanimity':{
  'question':'Did every member of the referenced committee or committees support the proposal?',
  'referents':{'they-one':'The referent is one committee with several members.','they-many':'The referents are two committees, each with several members.'},
  'facts':[
   'The complete ballot record states that every member of the referenced committee or committees voted in favour; no member opposed or abstained.',
   'The complete ballot record states that at least one member of the referenced committee or committees opposed the proposal.',
   'The report states only that the proposal passed. It gives no individual votes and no rule requiring unanimous support.'
  ]},
 'all_members_participation':{
  'question':'Did every member of the referenced team or teams personally perform some part of the task?',
  'referents':{'they-one':'The referent is one team with several members.','they-many':'The referents are two teams, each with several members.'},
  'facts':[
   'The complete participation record states that every member of the referenced team or teams personally performed at least one task step.',
   'The complete participation record states that at least one member of the referenced team or teams performed no part of the task.',
   'The report says that the task was completed. It gives no information about which members participated.'
  ]},
 'collective_action':{
  'question':'Was the reported activity performed as one coordinated group event?',
  'referents':{'they-one':'The referent is one ensemble with several members.','they-many':'The referents are two ensembles, each with several members.'},
  'facts':[
   'The event record explicitly states that the participants performed the reported activity together as one coordinated group event.',
   'The event record explicitly states that participants performed the reported activity separately and independently, not as one coordinated group event.',
   'The report says that the activity happened. It gives no information about coordination, timing, or whether the participants acted together.'
  ]},
}

def build():
    items=[]
    for form in FORMS:
        for dimension,spec in SPECS.items():
            for state,fact in enumerate(spec['facts']):
                world=f'{form}/{dimension}/state-{state}'
                for rotation in range(3):
                    options=LABELS[rotation:]+LABELS[:rotation]
                    items.append({'id':f'{world}/order-{rotation}','world_id':world,
                                  'form_slot':form,'dimension':dimension,
                                  'role':'explicit_fact' if state<2 else 'underdetermined',
                                  'text':'Fictional control record. '+spec['referents'][form]+' '+fact,
                                  'question':spec['question'],'options':options,
                                  'gold':LABELS[state],
                                  'exposure':'standalone shared-context control concept; no target marker in prompt'})
    return {'kind':'ainglish.nonclaim-control-review-fixtures.v1',
            'status':'PROPOSED_FOR_REVIEW_NOT_A_TARGET_BANK_OR_MEASUREMENT',
            'candidate_sha256':'fdf67591234ec63df19d29cfbbfe44d17e3685a189cb42c7782e7f41b36cc462',
            'semantic_templates':30,'prompt_variants':90,
            'reader_calls':0,'items':items}

def score(fixtures,observations):
    """Review-fixture scoring only; one observation ID cannot serve two prompts."""
    planned={r['id']:r for r in fixtures['items']}
    if len(planned)!=len(fixtures['items']): raise ValueError('Duplicate planned prompt ID')
    ids=set(); seen={}
    for row in observations:
        if not isinstance(row,dict) or set(row)!={'observation_id','item_id','dimension','form_slot','answer'}:
            raise ValueError('Observation has missing or unknown fields')
        oid=row['observation_id']; iid=row['item_id']
        if not isinstance(oid,str) or not oid or oid in ids:
            raise ValueError('Observation ID missing or reused')
        if iid not in planned or iid in seen: raise ValueError('Unknown or duplicate prompt')
        item=planned[iid]
        if row['dimension']!=item['dimension'] or row['form_slot']!=item['form_slot']:
            raise ValueError('An observation cannot be reassigned to another endpoint')
        if row['answer'] is not None and row['answer'] not in item['options']:
            raise ValueError('Use a declared answer or explicit absent-cell null')
        ids.add(oid); seen[iid]=row
    endpoints=[]
    for form in FORMS:
        for dimension in SPECS:
            summary={'form_slot':form,'dimension':dimension}
            for role in ['explicit_fact','underdetermined']:
                rows=[x for x in planned.values() if x['form_slot']==form and x['dimension']==dimension and x['role']==role]
                answered=[x for x in rows if x['id'] in seen and seen[x['id']]['answer'] is not None]
                correct=sum(seen[x['id']]['answer']==x['gold'] for x in answered)
                summary[role]={'planned_prompts':len(rows),'semantic_templates':len({x['world_id'] for x in rows}),
                               'answered':len(answered),'absent':len(rows)-len(answered),
                               'correct':correct,'incorrect':len(answered)-correct,
                               'observed_accuracy':correct/len(answered) if answered else None,
                               'observed_control_failure_rate':1-correct/len(answered) if answered else None}
            summary['complete']=all(summary[r]['absent']==0 for r in ['explicit_fact','underdetermined'])
            endpoints.append(summary)
    return {'kind':'ainglish.control-fixture-score.v1','fileable_measurement':False,
            'complete':all(x['complete'] for x in endpoints),'endpoints':endpoints,
            'interpretation':'Counts of prototype prompt variants, not independent-world rates or confidence bounds. No target, instrument or bundle is certified.'}

def fixture_answers(fixtures,choice=None):
    rows=[]
    for item in fixtures['items']:
        answer=item['gold'] if choice is None else choice(item)
        rows.append({'observation_id':'synthetic/'+item['id'],'item_id':item['id'],
                     'dimension':item['dimension'],'form_slot':item['form_slot'],'answer':answer})
    return rows

if __name__=='__main__':
    root=Path(__file__).parent
    fixtures=build()
    results={}
    for label in LABELS:
        results['constant-semantic/'+label]=score(fixtures,fixture_answers(fixtures,lambda item,label=label:label))
    for position in range(3):
        results[f'constant-position/{position}']=score(fixtures,fixture_answers(fixtures,lambda item,position=position:item['options'][position]))
    for name,value in [('control-prototypes.json',fixtures),('shortcut-checks.json',results)]:
        (root/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print('Prepared 30 control templates / 90 option variants; six synthetic shortcut checks; zero reader calls.')
