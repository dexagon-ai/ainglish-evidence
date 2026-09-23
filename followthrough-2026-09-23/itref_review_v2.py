"""Review-only instruments. No qualification, mint, tokenization or reader call.

The v1 export remains immutable. This v2 repairs complete bare-input equality
(including choice order), and adds separate learnability / transform designs.
It does NOT resolve the register's missing preservation carrier by code.
"""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).parent
OLD=ROOT.parent/'decisive-progression-2026-09-22/itref_instrument.py'
spec=importlib.util.spec_from_file_location('old_itref',OLD)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def primary_v2():
    items=[];keys=[];old.primary(items,keys)
    byid={i['id']:i for i in items};frames={}
    for k in keys:frames.setdefault(k['design']['frame_cluster'],[]).append(k)
    for number,pair in enumerate(frames.values()):
        # Choose ONE option ordering for both hidden-intent worlds. Only the
        # marked/noun reference is allowed to reveal their different intent.
        canonical=list(byid[pair[0]['id']]['choices'].values())
        canonical=sorted(canonical)
        canonical=canonical[number%4:]+canonical[:number%4]
        choices=dict(zip('ABCD',canonical))
        for k in pair:
            item=byid[k['id']];answer=item['choices'][k['answer']]
            item['choices']=choices.copy()
            k['answer']=next(label for label,value in choices.items() if value==answer)
            k['answer_by_arm']=dict.fromkeys(item['arms'],k['answer'])
            k['original_public_item_id']=item['id']
            item['id']=digest({f:item[f] for f in ['arms','question','choices']})[:24]
            k['id']=item['id']
    return items,keys

def complete_bare_input(item):
    # Neither opaque item id nor design metadata is sent to a reader.
    return {'message':item['arms']['bare'],'question':item['question'],'choices':item['choices']}

DOMAINS=[('services','service','agent','failed its health check','isolate'),
         ('tools','scanner','sample','was moved to Bay D','collect'),
         ('robots','robot','crate','was marked for inspection','inspect'),
         ('processes','process','file','was placed under audit','audit'),
         ('messages','relay','packet','was flagged for review','review'),
         ('sensors','sensor','beacon','failed its diagnostic check','inspect')]

def diagnostics(entry):
    items=[];keys=[]
    for family,repeats in [('learning',8),('summary',4),('translation',4)]:
        for d,(domain,n1,n2,condition,action) in enumerate(DOMAINS):
            for j in range(repeats):
                frame=f'{family}-{domain}-{j}'
                a=f'{n1}-{digest(frame+"a")[:6]}';b=f'{n2}-{digest(frame+"b")[:6]}'
                common=f'Two distinct non-person units are named {a} and {b}. Response rule: {action} exactly the unit that {condition}. '
                choices0=[f'{action} {a}',f'{action} {b}',f'{action} both units','No unique action is licensed']
                # Pair shares a complete question/choice space, including order.
                rotation=(d+j)%4;values=choices0[rotation:]+choices0[:rotation]
                choices=dict(zip('ABCD',values))
                question='Which single action does the record license next?'
                for position,target in enumerate((a,b)):
                    marked=common+f'The unit {a} was listed alongside {b}. Later, it({target}) {condition}.'
                    careful=common+f'The unit {a} was listed alongside {b}. Later, the unit {target} {condition}.'
                    if family=='learning':
                        arms={'marked_cold':marked,'marked_entry_loaded':entry+'\n\n'+marked,
                              'careful_cold':careful,'careful_entry_loaded':entry+'\n\n'+careful}
                        stage_plan=None
                    else:
                        arms={'marked':marked,'careful':careful}
                        if family=='summary':
                            stage_plan=[{'operation':'summarize', 'instruction':
                                'Summarize the supplied operational record in at most 40 words. Preserve the entity identifiers, which unit has the reported condition, and the response rule. Do not add facts.'},
                                {'operation':'receiver','input':'ONLY the retained summary, the fixed question and choices; never the original source or key'}]
                        else:
                            stage_plan=[{'operation':'translate_en_es','instruction':
                                'Translate this operational record into Spanish. Preserve entity identifiers exactly and preserve its assertions and action rule. Do not add facts.'},
                                {'operation':'translate_es_en','instruction':
                                'Translate this Spanish operational record into English. Preserve entity identifiers exactly and preserve its assertions and action rule. Do not add facts.'},
                                {'operation':'receiver','input':'ONLY the retained back-translation, fixed question and choices; never either earlier source or key'}]
                    item={'arms':arms,'question':question,'choices':choices.copy()}
                    if stage_plan is not None:item['stages']=stage_plan
                    item['id']=digest(item)[:24];items.append(item)
                    keys.append({'id':item['id'],'family':family,'frame_cluster':frame,
                        'domain':domain,'antecedent_position':position,
                        'answer':next(label for label,value in choices.items() if value==f'{action} {target}'),
                        'intended_target':target,'reported_condition':condition,'licensed_action':f'{action} {target}',
                        'source_entities':[a,b],
                        'boundary':'Score received meaning and intended transmission separately. Preserving identifier bytes alone does not certify semantics.'})
    return items,keys

def validate(primary, primary_keys, diagnostic, diagnostic_keys,entry):
    frames={};byid={i['id']:i for i in primary}
    for k in primary_keys:frames.setdefault(k['design']['frame_cluster'],[]).append(k)
    for pair in frames.values():
        assert len(pair)==2
        first,second=[byid[k['id']] for k in pair]
        assert complete_bare_input(first)==complete_bare_input(second)
        assert pair[0]['answer']!=pair[1]['answer']
    byid={i['id']:i for i in diagnostic}
    for k in diagnostic_keys:
        row=byid[k['id']]
        assert row['choices'][k['answer']]==k['licensed_action']
        assert len(set(row['choices'].values()))==4
        if k['family']=='learning':
            for arm in ('marked','careful'):
                assert row['arms'][arm+'_entry_loaded']==entry+'\n\n'+row['arms'][arm+'_cold']
    assert len({i['id'] for i in primary+diagnostic})==384
    assert Counter(k['family'] for k in diagnostic_keys)=={'learning':96,'summary':48,'translation':48}
    return {'status':'review_only_carrier_mismatch_holds_launch',
        'primary_worlds':192,'primary_frame_clusters':96,'complete_bare_pairs_equal':96,
        'primary_answer_positions':dict(Counter(k['answer'] for k in primary_keys)),
        'diagnostic_worlds':192,'diagnostic_families':dict(Counter(k['family'] for k in diagnostic_keys)),
        'diagnostic_frame_clusters':96,
        'reader_calls':0,'hypothetical_diagnostic_calls_if_all_conditions_run':864,
        'entry_sha256':hashlib.sha256(entry.encode()).hexdigest(),
        'limitations':['The 96 primary frames are authored combinations, not a representative sample.',
            'The bare arm estimates assigned-intent recovery, not truth stated by ambiguous English.',
            'An above-50-percent expected paired bare score violates the intended information boundary; audit inputs/keys/state/assignment/scoring, not retrospectively remove cases.',
            'Summary and translation require semantic review; an ID-preservation check is insufficient.',
            'This is a separately reviewed diagnostic design, not a future-training result or a route around careful-English requirements.',
            'Final roster, calibration, transport, official harness conversion and inferential plan remain launch gates.']}

def main():
    snapshot=json.loads((ROOT/'snapshot.json').read_text())
    entry=snapshot['itref_entry']['english_mapping']
    p,pk=primary_v2();d,dk=diagnostics(entry);report=validate(p,pk,d,dk,entry)
    outputs={'itref-primary-v2-inputs.json':p,'itref-primary-v2-keys.json':pk,
             'itref-diagnostic-inputs.json':d,'itref-diagnostic-keys.json':dk,
             'itref-v2-review.json':report,'itref-entry.json':snapshot['itref_entry']}
    for name,value in outputs.items():(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
