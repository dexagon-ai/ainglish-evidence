"""Recompute visible semantics and served scored-cell statistics; no inference.

This is a post-hoc audit, not a new measurement or independent raw-response grading.
Dexagon is the original measurer, not an independent adoption voter on this proposal.
"""
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
from statistics import mean
from ainglish.panel import arm_for

ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT.parent
FORMS=('choose-any','draw-uniform')

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def check_source(item, span):
    form=item['settlement_stratum']; world=item['semantic_world']; ref=world['set_ref']
    a_prefix, a_request=item['ainglish'].rsplit('\nRequest: ',1)
    e_prefix, e_request=item['english'].rsplit('\nRequest: ',1)
    assert a_prefix==e_prefix
    assert a_request==f'{form}({ref}).'
    assert e_request==re.sub(r'\bS\b',lambda m:ref,span)
    members=set(world['members'])
    assert len(members)==world['n']==item['member_count']
    contract=item['probe_contract']
    allowed=[]
    for policy in contract['policies']:
        assert policy['text'] in item['question']
        probabilities={k:Fraction(v) for k,v in policy['distribution'].items()}
        text=policy['text']
        if policy['kind']=='unequal-weight':
            match=re.fullmatch(r'Assigns probability (\d+/\d+) to (\S+) and (\d+/\d+) to each other listed identity, then returns one draw from that distribution\.',text)
            assert match and match[2] in members
            parsed={k:Fraction(match[1] if k==match[2] else match[3]) for k in members}
        elif policy['kind']=='equal-probability':
            match=re.fullmatch(r'Assigns probability (\d+/\d+) to each distinct listed identity before drawing and returning exactly one\.',text)
            assert match
            parsed={k:Fraction(match[1]) for k in members}
        else:
            match=re.fullmatch(r'Returns (\S+)(?: on every execution,|, which has the unique (?:lowest|highest) [^.]+,) with probability one\.',text)
            assert match
            parsed={match[1]:Fraction(1)}
        assert probabilities==parsed
        assert sum(probabilities.values())==1 and all(v>=0 for v in probabilities.values())
        in_set=set(probabilities)<=members
        uniform=(set(probabilities)==members and all(v==Fraction(1,len(members)) for v in probabilities.values()))
        if in_set and (form=='choose-any' or uniform): allowed.append(policy['label'])
        if policy['kind']=='criterion-based':
            scores=dict(zip(world['members'],world['scores']))
            best=min(scores.values()) if 'lowest' in policy['text'] else max(scores.values())
            assert set(probabilities)=={k for k,v in scores.items() if v==best}
    guarantees=[]
    for g in contract['guarantees']:
        assert g['text'] in item['question']
        if g['key']=='one-eligible' or form=='draw-uniform' and g['key']=='equal-odds':
            guarantees.append(g['label'])
    target={'policies':sorted(allowed),'guarantees':sorted(guarantees)}
    assert {k:sorted(v) for k,v in contract['gold'].items()}==target
    good=[]
    for option in item['options']:
        # Parse the actual visible labels, not just the author's option metadata.
        match=re.fullmatch(r'Implementations: (.*?); claims: (.*?)\.',option)
        assert match
        parsed={'policies':sorted(match[1].split(', ')) if match[1]!='none' else [],
                'guarantees':sorted(match[2].split(', ')) if match[2]!='none' else []}
        assert {k:sorted(v) for k,v in contract['option_records'][option].items()}==parsed
        if parsed==target: good.append(option)
    assert good==[item['answer']]
    return a_prefix, e_request

def check_replication(item, span):
    form=item['settlement_stratum']; ref=item['set_reference']; codes=item['policy_codes']
    a_prefix,a_request=item['ainglish'].rsplit('\n\nRequest: ',1)
    e_prefix,e_request=item['english'].rsplit('\n\nRequest expressed by the complete registered careful-English specification:\n',1)
    assert a_prefix==e_prefix
    assert a_request==f'Return {form}({ref}).'
    assert e_request==re.sub(r'\bS\b',lambda m:ref,span)
    members=re.search(r'exactly these distinct eligible identities: (.*?)\.',a_prefix)[1].split(', ')
    assert len(set(members))==len(members)==item['member_count']
    lines=[s for s in a_prefix.splitlines() if s.startswith('- ')]
    assert len(lines)==5 and len(set(codes.values()))==5
    by_code={line.split(' ',2)[1]:line.split(' ',2)[2] for line in lines}
    assert set(by_code)==set(codes.values())
    assert 'always returns the first identity' in by_code[codes['first']]
    assert 'listed identity with the lowest recorded load' in by_code[codes['criterion']]
    weighted=re.fullmatch(r'samples only listed identities, assigning weight (\d+) to (\S+) and weight (\d+) to every other listed identity\.',by_code[codes['weighted']])
    assert weighted and weighted[2] in members
    assert int(weighted[1])>0 and int(weighted[3])>0 and int(weighted[1])!=int(weighted[3])
    assert f'each of the {len(members)} listed identities the same one-in-{len(members)} chance and returns one identity' in by_code[codes['uniform']]
    assert f'which is not in {ref}' in by_code[codes['outsider']]
    allowed={codes[k] for k in ('first','criterion','weighted','uniform')} if form=='choose-any' else {codes['uniform']}
    if form=='choose-any':
        suffix='The request forces one listed identity to be returned; it does not force symmetric chances, concealment of the next result, or any relation between separate runs.'
    else:
        suffix='The request forces one listed identity and the same chance for every listed identity on this draw; it does not force concealment of the next result or any relation between separate runs.'
    good=[]
    for option in item['options']:
        m=re.fullmatch(r'Permitted procedures: (.*?)\. (.*)',option)
        if m and set(m[1].split(', '))==allowed and m[2]==suffix: good.append(option)
    assert good==[item['answer']]
    assert len(item['options'])==8 and len(set(item['options']))==8
    return a_prefix,e_request

def scored_stats(measurement, items):
    lookup={i['id']:i for i in items if not i.get('calibration')}
    att=measurement['interval_provenance_attestation']
    assert len(att['items'])==len(lookup)
    assert {x['id']:x['stratum'] for x in att['items']}=={k:i['settlement_stratum'] for k,i in lookup.items()}
    cells=att['cells']; readers=att['readers']; seed=measurement['manifest']['seed']
    counts=defaultdict(lambda:[0,0]); world_arms=defaultdict(list); seen=set()
    for c in cells:
        key=(c['item_id'],c['reader'])
        assert key not in seen and c['item_id'] in lookup and c['reader'] in readers
        seen.add(key)
        assert arm_for(seed,c['reader'],c['item_id'])==c['arm']
        assert isinstance(c['correct'],bool)
        f=lookup[c['item_id']]['settlement_stratum']
        counts[f,c['reader'],c['arm']][0]+=int(c['correct'])
        counts[f,c['reader'],c['arm']][1]+=1
        world_arms[c['item_id']].append(c['arm'])
    assert len(seen)==len(lookup)*len(readers)
    forms={}
    for form in FORMS:
        detail={}; pooled={}
        for reader in readers:
            detail[reader]={arm:{'correct':counts[form,reader,arm][0],'n':counts[form,reader,arm][1],
                                'accuracy':counts[form,reader,arm][0]/counts[form,reader,arm][1]}
                            for arm in ('english','ainglish')}
        for arm in ('english','ainglish'):
            correct=sum(counts[form,r,arm][0] for r in readers)
            n=sum(counts[form,r,arm][1] for r in readers)
            pooled[arm]={'correct':correct,'n':n,'accuracy':correct/n}
        delta=100*(pooled['ainglish']['accuracy']-pooled['english']['accuracy'])
        equal_reader=mean(100*(detail[r]['ainglish']['accuracy']-detail[r]['english']['accuracy']) for r in readers)
        row=next(x for x in measurement['stratum_results'] if x['id']==form)
        assert abs(delta-row['value'])<.011
        forms[form]={'pooled':pooled,'delta_pp_unrounded':delta,'equal_reader_delta_pp':equal_reader,'by_reader':detail}
    aggregate=mean(f['delta_pp_unrounded'] for f in forms.values())
    assert abs(aggregate-measurement['value'])<.011
    return {'forms':forms,'aggregate_unrounded_pp':aggregate,
            'equal_reader_aggregate_pp':mean(f['equal_reader_delta_pp'] for f in forms.values()),
            'target_cells':len(cells),'assignment_verified':True,
            'world_arm_pattern':dict(Counter('/'.join(sorted(v)) for v in world_arms.values())),
            'grading_boundary':'Replayed published correctness flags; raw answer text was not obtained/regraded by this audit.'}

def main():
    render=json.loads((EVIDENCE/'choose-any-final-package-2026-09-15/rendering-contract.json').read_text())
    proposal=json.loads((ROOT/'a-ppyzdf5qk6z67aty.json').read_text())
    assert hashlib.sha256(proposal['english_mapping'].encode()).hexdigest()==render['english_mapping_sha256']
    for span in render['spans'].values(): assert span in proposal['english_mapping']
    report={}; banks={}
    for label,check in (('original',check_source),('replication',check_replication)):
        items=json.loads((ROOT/f'choose-{label}-items.json').read_text())
        m=json.loads((ROOT/f'choose-{label}-measurement.json').read_text())
        assert digest(items)==m['manifest']['items_sha256']
        real=[i for i in items if not i.get('calibration')]; banks[label]=real
        errors=[]; frame_counts=Counter(); option_positions=defaultdict(Counter)
        for i in real:
            try: check(i,render['spans'][i['settlement_stratum']])
            except (AssertionError,KeyError,IndexError,ValueError,TypeError) as e:
                errors.append({'id':i['id'],'type':type(e).__name__})
            option_positions[i['settlement_stratum']][i['options'].index(i['answer'])]+=1
            frame_counts[i.get('frame_family','undeclared')]+=1
        report[label]={
            'hash':m['manifest_hash'],'items_sha256':digest(items),'real_items':len(real),
            'calibration_items':len(items)-len(real),'visible_gold_and_comparator_checks':len(real)-len(errors),
            'check_failures':errors,'question_text_count':len({i['question'] for i in real}),
            'declared_frames':dict(frame_counts),'gold_option_positions_zero_based':{k:dict(v) for k,v in option_positions.items()},
            'form_domain_counts':dict(Counter(i['settlement_stratum']+'/'+i['domain'] for i in real)),
            'form_member_counts':dict(Counter(i['settlement_stratum']+'/'+str(i['member_count']) for i in real)),
            'scores':scored_stats(m,items),
        }
    op={(i['english'],i['ainglish']) for i in banks['original']}
    rp={(i['english'],i['ainglish']) for i in banks['replication']}
    report['cross_bank']={'exact_complete_pair_overlap':len(op&rp),
        'world_id_overlap':len({i['world_id'] for i in banks['original']}&{i['world_id'] for i in banks['replication']}),
        'same_declared_reader_configurations':json.loads((ROOT/'choose-original-measurement.json').read_text())['manifest']['readers']==json.loads((ROOT/'choose-replication-measurement.json').read_text())['manifest']['readers'],
        'no_causal_attribution':'No crossed fixed-bank experiment was run. Instrument differences and allocation are observed; they do not identify the cause of the accuracy shift.'}
    report['status']='post_hoc_diagnostic_audit_not_new_measurement'
    report['model_calls']=0
    (ROOT/'choose-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:{f:report[k][f] for f in ('real_items','visible_gold_and_comparator_checks','question_text_count','declared_frames','gold_option_positions_zero_based')} for k in ('original','replication')},indent=2))
    print(json.dumps({k:{'failure_count':len(report[k]['check_failures']),'first_failures':report[k]['check_failures'][:2]} for k in ('original','replication')}))
    print(json.dumps(report['cross_bank'],indent=2))

if __name__=='__main__': main()
