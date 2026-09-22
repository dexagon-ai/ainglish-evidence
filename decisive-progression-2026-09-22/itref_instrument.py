"""Build a REVIEW candidate, never launch a panel. No model or tokenizer imports.

Keys and design labels are separate from reader inputs. Authored frame clusters,
not repeated arms, are the units of replication/inference. These exposed review
bytes must not later be called an unseen independently sampled population.
"""
import hashlib,json,re
from collections import Counter
from pathlib import Path

DOMAINS=[
 ('services_agents','service','agent','notified','failed','repair'),
 ('tools_artifacts','scanner','sample','inspected','moved to Bay C','retrieve from Bay C'),
 ('robots_objects','robot','crate','approached','blocked the doorway','clear from the doorway'),
 ('processes_files','process','file','referenced','changed version','audit the new version of'),
 ('senders_messages','relay','packet','forwarded','was quarantined','review the quarantine of'),
 ('sensors_targets','sensor','beacon','tracked','emitted the pulse','inspect the transmitter in'),
]
AXES={'identity':'The two identifiers name one physical object.',
      'ownership':'The first unit owns the second unit.',
      'responsibility':'The first unit is responsible for the event.',
      'causality':'The first unit caused the event.',
      'continued_existence':'The first unit still exists now.',
      'truth':'The claim printed by the first unit is true.'}
INVALID=('missing','future','duplicate','unpinned','plural','person','possessive','demonstrative','delimiter_loss')

def sha(x):return hashlib.sha256(x.encode()).hexdigest()
def options(values,correct,rotation):
    values=values[rotation%len(values):]+values[:rotation%len(values)]
    return {chr(65+i):v for i,v in enumerate(values)},chr(65+values.index(correct))

def add(items,keys,meta,messages,question,answers,correct,rotation,**extra):
    item_id=sha(json.dumps([meta,messages,question],sort_keys=True))[:24]
    choices,key=options(answers,correct,rotation)
    items.append({'id':item_id,'arms':messages,'question':question,'choices':choices})
    keys.append({'id':item_id,'answer':key,'answer_by_arm':dict.fromkeys(messages,key),'design':meta,**extra})

def primary(items,keys,phase='primary'):
    for d,(domain,n1,n2,verb,predicate,action) in enumerate(DOMAINS):
        for connective in ('after','while','because','before'):
            for distance in range(4):
                frame=f'{phase}-{d}-{connective}-{distance}'
                # IDs identify entities in the message, not the hidden intended position.
                a=f'{n1}-{sha(frame+"a")[:6]}';b=f'{n2}-{sha(frame+"b")[:6]}'
                padding=' '.join(f'Log channel {j+1} is reserved for routine status records.' for j in range(distance))
                context=f'There are two distinct non-person units: the {a} and the {b}. {padding} Response rule: {action} exactly the unit reported to have {predicate if predicate != "was quarantined" else "been quarantined"}; do not act on any other unit. '
                # Keep the bare input byte-identical across the two hidden-intent worlds.
                bare=f'The {a} {verb} the {b} {connective} it {predicate}.'
                for target_position,target in enumerate((a,b)):
                    messages={'bare':context+bare,
                              'marked':context+bare.replace(' it ',f' it({target}) '),
                              'careful':context+bare.replace(' it ',f' the {target} ')}
                    correct=f'{target}; act on {target}'
                    alternatives=[f'{a}; act on {a}',f'{b}; act on {b}',f'{a}; act on {b}','Cannot determine which unit; no unique action is licensed']
                    add(items,keys,{'family':phase,'frame_cluster':frame,'domain':domain,'connective':connective,'distance_sentences':distance,'antecedent_position':target_position},messages,
                        'Which unit has the reported condition, and which single unit does the response rule identify?',alternatives,correct,
                        d+distance+2*target_position+('after','while','because','before').index(connective))

def controls(items,keys):
    for family in INVALID:
        for i in range(12):
            a=f'unit-{sha(family+str(i))[:6]}';b=f'unit-{sha(family+str(i)+"b")[:6]}'
            for valid in (False,True):
                context=f'Two distinct non-person units have unique identifiers {a} and {b}. '
                ref=a;surface=f'it({a})';expect='Valid proposed marker with one in-scope referent'
                if not valid:
                    expect='Not a valid proposed marker with one in-scope referent'
                    if family=='missing':ref='unintroduced-unit';surface=f'it({ref})'
                    elif family=='future':context='No unit has been introduced at this point. '
                    elif family=='duplicate':context=f'Two distinct units both use the identifier {a}. '
                    elif family=='unpinned':context=f'The identifier {a} occurs only in a mutable external document, whose version is not supplied. '
                    elif family=='plural':context=f'The identifier {a} denotes several units collectively. '
                    elif family=='person':context=f'The identifier {a} denotes one human person. '
                    elif family=='possessive':surface=f'its({a})'
                    elif family=='demonstrative':surface=f'this({a})'
                    elif family=='delimiter_loss':surface=f'it {a}'
                message=context+f'At this point the received reference is {surface}.'
                if family=='future' and not valid:message+=f' Only afterwards is a unique unit named {a} introduced.'
                add(items,keys,{'family':'validity','case':family,'valid_control':valid}, {'marked':message},
                    'At the indicated point, is the received reference a valid instance of the proposed singular non-person marker with exactly one recoverable referent?',
                    ['Valid proposed marker with one in-scope referent','Not a valid proposed marker with one in-scope referent'],expect,i%2)
    for axis,fact in AXES.items():
        for state in ('unstated','yes','no'):
            for i in range(12):
                a=f'unit-{sha(axis+str(i))[:6]}';b=f'unit-{sha(axis+str(i)+"b")[:6]}'
                context=f'The first unit is {a}; the second unit is {b}. The first unit printed a claim. '
                if state=='yes':context+='It is explicitly given as a fact that: '+fact+' '
                if state=='no':context+='It is explicitly given as a fact that the following statement is false: '+fact+' '
                add(items,keys,{'family':'nonclaim','axis':axis,'assertion':state},
                    {'marked':context+f'The record mentions it({a}).','careful':context+f'The record mentions the unit {a}.'},
                    'Does the supplied text establish this statement: '+fact,
                    ['Yes','No','Not established'],{'yes':'Yes','no':'No','unstated':'Not established'}[state],i%3)
    for mutation in ('valid_to_valid','valid_to_missing','parentheses_loss','punctuation_stripping'):
        for i in range(12):
            a=f'unit-{sha(mutation+str(i))[:6]}';b=f'unit-{sha(mutation+str(i)+"b")[:6]}'
            context=f'Two units are introduced with unique identifiers {a} and {b}. '
            received=b if mutation=='valid_to_valid' else 'missing-unit' if mutation=='valid_to_missing' else a
            marker=f'it({received})';noun=f'the unit {received}'
            if mutation=='parentheses_loss':marker=marker.replace('(',' ').replace(')','')
            if mutation=='punctuation_stripping':marker=re.sub(r'[^\w\s]','',marker);noun=re.sub(r'[^\w\s]','',noun)
            # Matching punctuation transformation applies to the complete noun identifier too.
            expected=received if mutation=='valid_to_valid' else 'No valid unique reference under the declared reference grammar'
            add(items,keys,{'family':'corruption','mutation':mutation},
                {'marked':context+f'The received reference is {marker}.','careful':context+f'The received reference is {noun}.'},
                'Which introduced unit does the received reference identify under its stated grammar?',
                [a,b,'No valid unique reference under the declared reference grammar'],expected,i%3,
                sender_intended=a,received_reference=received,
                scoring_boundary='Score received binding and sender-intended transmission separately. Correct binding of received B is not a parser error; B is still a transmission error against intended A. Parentheses loss preserves ordinary noun recovery while invalidating the marker; do not impose the marker grammar on the English arm.')
            if mutation=='parentheses_loss':
                keys[-1]['answer_by_arm']['careful']=next(k for k,v in items[-1]['choices'].items() if v==a)
    for i in range(12):
        a=f'unique-{i}'
        add(items,keys,{'family':'one_antecedent'},
            {'bare':f'The unit {a} is the only unit mentioned. It failed.',
             'marked':f'The unit {a} is the only unit mentioned. it({a}) failed.',
             'careful':f'The unit {a} is the only unit mentioned. The unit {a} failed.'},
            'Which unit failed?',[a,'No unique unit can be identified'],a,i%2)

def validate(items,keys):
    assert len(items)==len(keys)==len({x['id'] for x in items})
    byid={x['id']:x for x in items}
    for k in keys:
        assert k['answer'] in byid[k['id']]['choices']
        assert set(k['answer_by_arm'])==set(byid[k['id']]['arms'])
        assert all(v in byid[k['id']]['choices'] for v in k['answer_by_arm'].values())
        if k['design'].get('mutation')=='parentheses_loss':
            assert k['answer_by_arm']['marked'] != k['answer_by_arm']['careful']
    primary_keys=[k for k in keys if k['design']['family']=='primary']
    assert len(primary_keys)==192
    assert Counter(k['design']['antecedent_position'] for k in primary_keys)=={0:96,1:96}
    frames={}
    for k in primary_keys:frames.setdefault(k['design']['frame_cluster'],[]).append(k)
    assert len(frames)==96
    for pair in frames.values():
        assert len(pair)==2
        assert byid[pair[0]['id']]['arms']['bare']==byid[pair[1]['id']]['arms']['bare']
        assert byid[pair[0]['id']]['choices'][pair[0]['answer']]!=byid[pair[1]['id']]['choices'][pair[1]['answer']]
    assert Counter(k['answer'] for k in primary_keys)==dict.fromkeys('ABCD',48)
    return {'items':len(items),'families':dict(Counter(k['design']['family'] for k in keys)),
            'primary_worlds':192,'primary_frame_clusters':96,
            'primary_calls_per_reader':576,'all_calls_per_reader':sum(len(x['arms']) for x in items),
            'reader_calls_run':0,'status':'independent_review_required_not_launch_ready',
            'critical_unfinished':['Independent semantic/key review of the authored bank, including full noun repetition and matched corruption arm-specific expectations.',
                'Current positive careful-English carrier versus prose preservation must be explicitly decided; no automatic noninferiority pass.',
                'Definition-conditioned diagnostic, summarization and translation arms require separately reviewed instruments; they are not silently counted as covered here.',
                'Reader roster, qualification, official harness conversion, absolute floor and joint inferential/error-control method are not fixed by this review export.',
                'Template/world dependence must not inflate n from 96 frame clusters to 192 independent contexts. Exposed review data are not human validation.']}

def main():
    items=[];keys=[];primary(items,keys);controls(items,keys);report=validate(items,keys)
    root=Path(__file__).parent
    for name,data in [('itref-inputs.json',items),('itref-keys.json',keys),('itref-review.json',report)]:
        (root/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
