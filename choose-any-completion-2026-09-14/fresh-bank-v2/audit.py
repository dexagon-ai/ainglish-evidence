"""Audit actual SDK payload construction and file semantics with all network sockets forbidden.

The fake HTTP service is an admitted answer-key oracle. It establishes plumbing only; it never
qualifies a reader, certifies language accuracy, files evidence, or saves its numeric result.
"""
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import random
import re
from unittest.mock import patch

from ainglish import panel
from instrument import ROOT, FORMS, digest, canonical, opportunities, write

def old_shortcut(options):
    counts=[(len(re.findall(r'\bP\d+\b',s)),len(re.findall(r'\bG\d+\b',s))) for s in options]
    want=(4,1) if max(p for p,g in counts)>=3 else (1,2)
    matches=[s for s,c in zip(options,counts) if c==want]
    return matches[0] if len(matches)==1 else None

def bound(items,view):
    groups=defaultdict(Counter)
    for item in items: groups[canonical(view(item))][item['answer']]+=1
    return {'maximum_correct':sum(max(c.values()) for c in groups.values()),'total':len(items),
            'distinct_views':len(groups),'ambiguous_views':sum(len(c)>1 for c in groups.values())}

def visible(item,arm):
    return {'context':item[arm].split('\nRequest:')[0],'question':item['question'],'options':item['options']}

def semantic_check(item):
    w=item['semantic_world']; contract=item['probe_contract']; form=item['settlement_stratum']
    members=w['members']; n=w['n']
    assert n==len(set(members))==len(members) and 2<=n<=8
    assert w['outsider'] not in members
    assert len(set(w['scores']))==n and w['scores'].index(min(w['scores']))!=0
    first=members[0]; minimum=members[w['scores'].index(min(w['scores']))]
    allowed={'constant-first','criterion-based','unequal-weight','equal-probability'} if form=='choose-any' else {'equal-probability'}
    p_labels=set(); kinds=set()
    for policy in contract['policies']:
        kind=policy['kind']; kinds.add(kind)
        dist={k:Fraction(v) for k,v in policy['distribution'].items()}
        assert sum(dist.values())==1 and all(v>0 for v in dist.values())
        if kind=='constant-first': assert dist=={first:Fraction(1)}
        elif kind=='criterion-based': assert dist=={minimum:Fraction(1)}
        elif kind=='out-of-set': assert dist=={w['outsider']:Fraction(1)}
        elif kind=='equal-probability': assert dist=={m:Fraction(1,n) for m in members}
        elif kind=='unequal-weight':
            assert set(dist)==set(members)
            values=Counter(dist.values()); assert len(values)==2
            low,high=sorted(values)
            assert values[high]==1 and high/low in [2,3,4]
            assert high+(n-1)*low==1
        else: raise AssertionError(kind)
        if kind in allowed: p_labels.add(policy['label'])
    assert len(kinds)==5
    guaranteed={'one-eligible'}|({'equal-odds'} if form=='draw-uniform' else set())
    g_labels={g['label'] for g in contract['guarantees'] if g['key'] in guaranteed}
    assert len({g['key'] for g in contract['guarantees']})==4
    assert contract['gold']=={'policies':sorted(p_labels),'guarantees':sorted(g_labels)}
    answers=[s for s,r in contract['option_records'].items() if r==contract['gold']]
    assert answers==[item['answer']]
    assert len(set(item['options']))==8 and set(item['options'])==set(contract['option_records'])
    assert item['english'].split('\nRequest:')[0]==item['ainglish'].split('\nRequest:')[0]
    assert all(f not in visible(item,'english')['context'] for f in FORMS)

def capture_payload(reader,item,arm):
    payloads=[]
    reader=deepcopy(reader)
    reader[panel._INSTRUMENT_PREPARATION_KEY]={'binding':'OFFLINE-FAKE-DO-NOT-CERTIFY','entry_point':'payload audit'}
    def fake_fetch(request,timeout=None):
        assert request.full_url=='http://127.0.0.1:11434/v1/chat/completions'
        payloads.append(json.loads(request.data))
        return {'choices':[{'message':{'content':'A'},'finish_reason':'stop'}]}
    with patch('socket.socket',side_effect=AssertionError('Network forbidden')),patch.object(panel,'_fetch',fake_fetch):
        panel.ask(reader,item[arm],item['question'],item['options'])
    assert len(payloads)==1
    return payloads[0]

def without_request(payload):
    result=deepcopy(payload)
    content=result['messages'][0]['content']
    prefix,rest=content.split('\nRequest:',1)
    _,suffix=rest.split('\n---',1)
    result['messages'][0]['content']=prefix+'\n---'+suffix
    return result

def full_pipeline(spec,items,poison=False):
    """Default SDK planner -> ask -> chat -> actual serialized HTTP request, intercepted locally."""
    manifest=deepcopy(spec); manifest['items']=deepcopy(items); manifest['_dry_run']=True
    for ep in manifest['panel']:
        ep[panel._INSTRUMENT_PREPARATION_KEY]={'binding':'OFFLINE-FAKE-DO-NOT-CERTIFY','entry_point':'payload audit'}
    if poison:
        for item in manifest['items']:
            item['semantic_world']={'form':'SENTINEL-GOLD-METADATA-MUST-NOT-LEAK'}
            item['probe_contract']={'gold':'SENTINEL-ANSWER-METADATA-MUST-NOT-LEAK'}
            item['extra_runtime_echo']='SENTINEL-PAYLOAD-ECHO-MUST-NOT-LEAK'
            if not item.get('calibration'): item['settlement_stratum']='sentinel-stratum-'+item['settlement_stratum']
        for cell in manifest['settlement_strata']: cell['id']='sentinel-stratum-'+cell['id']
        manifest['items_sha256']=digest(manifest['items'])
    # The oracle matches text and uses gold only after payload capture. It is explicitly synthetic.
    key={item[arm]:(item,arm) for item in items for arm in ['english','ainglish']}
    payloads=[]
    def fake_fetch(request,timeout=None):
        assert request.full_url=='http://127.0.0.1:11434/v1/chat/completions'
        body=json.loads(request.data); payloads.append(body)
        assert 'sentinel-' not in json.dumps(body).lower()
        content=body['messages'][0]['content']; text=content.split('\n---\n')[1]
        item,arm=key[text]
        answer=item['answer']
        if item.get('calibration') and arm=='english': answer='Neither clerk nor archive established.'
        code=panel._CHOICE_CODES[item['options'].index(answer)]
        return {'choices':[{'message':{'content':code},'finish_reason':'stop'}]}
    transcript=io.StringIO(); cells=[]; calibration=[]
    with patch('socket.socket',side_effect=AssertionError('Network forbidden')),patch.object(panel,'_fetch',fake_fetch),redirect_stdout(transcript):
        result=panel.run_panel(manifest,cell_results=cells,calibration_results=calibration)
    assert result and not panel._is_panel_refusal(result), transcript.getvalue()
    assert result['manifest']['protocol'].endswith(panel._DRY_PROTOCOL_SUFFIX)
    assert result['manifest']['reader_qualifications']==spec['reader_qualifications']
    return payloads,len(cells),len(calibration)

def structural_features(item):
    counts=tuple((len(re.findall(r'\bP\d+\b',s)),len(re.findall(r'\bG\d+\b',s))) for s in item['options'])
    return {'member_count':item['member_count'],'frame_family':item['frame_family'],
            'ordered_count_signature':counts,'menu_characters':sum(map(len,item['options']))}

def classifier_score(items,labels,feature):
    hits=0
    for domain in sorted({i['domain'] for i in items}):
        train=defaultdict(Counter)
        for i,l in zip(items,labels):
            if i['domain']!=domain: train[canonical(structural_features(i)[feature])][l]+=1
        for i,l in zip(items,labels):
            if i['domain']==domain:
                votes=train[canonical(structural_features(i)[feature])]
                predicted='draw-uniform' if votes['draw-uniform']>votes['choose-any'] else 'choose-any'
                hits+=predicted==l
    return hits

def main():
    all_items=json.loads((ROOT/'items.json').read_text()); items=[i for i in all_items if not i.get('calibration')]
    twins=json.loads((ROOT/'audit-only-counterfactuals.json').read_text())['items']
    spec=json.loads((ROOT/'reader-config-review.json').read_text())
    assert len(items)==144 and len({i['world_id'] for i in items})==144
    assert Counter(i['settlement_stratum'] for i in items)=={'choose-any':72,'draw-uniform':72}
    assert set(Counter((i['settlement_stratum'],i['domain']) for i in items).values())=={12}
    for item in twins: semantic_check(item)
    for item in items: semantic_check(item)
    pair_bounds={}; sensitivity={}
    for arm in ['english','ainglish']:
        pair_bounds[arm]=bound(twins,lambda i:visible(i,arm))
        assert pair_bounds[arm]['maximum_correct']==144 and pair_bounds[arm]['ambiguous_views']==144
        for site in ['context','set_ref','question','option']:
            altered=deepcopy(twins)
            for i in altered:
                marker=' LEAK:'+i['settlement_stratum']
                if site=='context': i[arm]=i[arm].replace('\nRequest:',marker+'\nRequest:')
                elif site=='set_ref': i[arm]=i[arm].replace(i['semantic_world']['set_ref'],i['semantic_world']['set_ref']+marker)
                elif site=='question': i['question']+=marker
                else: i['options'][0]+=marker
            result=bound(altered,lambda i:visible(i,arm))
            assert result['maximum_correct']==288
            sensitivity[arm+'/'+site]=result
    for field in ['settlement_stratum','semantic_world.form']:
        result=bound(twins,lambda i:dict(visible(i,'english'),metadata_form=i['settlement_stratum']))
        assert result['maximum_correct']==288
        sensitivity[field+'_if_exposed']=result
    payloads=[]
    for reader in spec['panel']:
        for item in items:
            for arm in ['english','ainglish']:
                body=capture_payload(reader,item,arm)
                assert set(body)=={'model','temperature','seed','max_tokens','messages'}
                assert len(body['messages'])==1 and body['messages'][0]['role']=='user'
                payloads.append({'item_id':item['id'],'reader':reader['name'],'arm':arm,'http_body':body})
    for index in range(0,len(twins),2):
        left,right=twins[index:index+2]
        for arm in ['english','ainglish']:
            assert without_request(capture_payload(spec['panel'][0],left,arm))==without_request(capture_payload(spec['panel'][0],right,arm))
    clean,nreal,ncal=full_pipeline(spec,all_items)
    poisoned,pnreal,pncal=full_pipeline(spec,all_items,poison=True)
    assert clean==poisoned and nreal==pnreal==288 and ncal==pncal==128
    assert len(clean)==416
    old=json.loads((ROOT.parent/'draft/items.json').read_text())
    old_items=old.get('items',[]) if isinstance(old,dict) else old
    witnesses=json.loads((ROOT.parent/'repair-witnesses/excluded-witnesses.json').read_text())['items']
    old_pairs={(i['english'],i['ainglish']) for i in old_items+witnesses}
    old_texts={i[a] for i in old_items+witnesses for a in ['english','ainglish']}
    assert all((i['english'],i['ainglish']) not in old_pairs for i in items)
    assert all(i[a] not in old_texts for i in items for a in ['english','ainglish'])
    shortcuts=Counter()
    for item in items:
        prediction=old_shortcut(item['options'])
        assert prediction==old_shortcut(list(reversed(item['options'])))
        shortcuts[item['settlement_stratum']]+=prediction==item['answer']
    # Diagnose the single selected assignment; never reroll it based on these scores.
    labels=[i['settlement_stratum'] for i in items]
    classifiers={f:classifier_score(items,labels,f) for f in structural_features(items[0])}
    report={'status':'OFFLINE_STRUCTURAL_AUDIT_NOT_A_LANGUAGE_MEASUREMENT',
        'sdk_version':importlib.metadata.version('ainglish'),
        'sdk_panel_file_sha256':hashlib.sha256(Path(panel.__file__).read_bytes()).hexdigest(),
        'target_reader_calls':0,'network_connections':0,'items_sha256':digest(all_items),
        'worlds':144,'forms':dict(Counter(labels)),'full_pipeline_synthetic_target_cells':nreal,
        'full_pipeline_synthetic_calibration_cells':ncal,'pipeline_metadata_poisoning_payload_identity':True,
        'metadata_fields_excluded':['answer','settlement_stratum','semantic_world','probe_contract','extra_runtime_echo','id','domain','frame_family','status'],
        'both_arm_counterfactual_view_bounds':pair_bounds,'leak_injection_sensitivity':sensitivity,
        'unpaired_exact_view_memorisation_bound':bound(items,lambda i:visible(i,'english')),
        'known_shortcut_correct_by_form':dict(shortcuts),
        'leave_one_domain_out_form_classification_correct_of_144':classifiers,
        'answer_position_counts_by_form':{f:dict(Counter(i['options'].index(i['answer']) for i in items if i['settlement_stratum']==f)) for f in FORMS},
        'member_count_by_form':{f:dict(Counter(i['member_count'] for i in items if i['settlement_stratum']==f)) for f in FORMS},
        'offered_worlds_by_form_contrast':dict(Counter(i['settlement_stratum']+'/'+k for i in items for k in opportunities(i))),
        'excluded_draft_and_witness_complete_pair_overlap':0,'excluded_draft_and_witness_arm_overlap':0,
        'readers_qualified_by_this_audit':False,'empirical_validation':False,
        'limits':['Identical twin views prove a bound only on that paired audit envelope.',
                  'Unpaired worlds have unique contexts: a memorising lookup can attain 144/144; no universal zero-information claim.',
                  'The listed held-out heuristic classifiers are finite diagnostics, not proof that no shortcut exists.',
                  'Stored metadata changes do not alter serialized HTTP bodies in this SDK/config; future versions need re-audit.',
                  'Same-investigator semantic double-check is not an independent principal review.']}
    write('exported-reader-payloads.json',{'status':'OFFLINE_EXPORT_NO_REQUEST_SENT','payloads':payloads})
    write('STRUCTURAL-AUDIT.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['leak_injection_sensitivity','offered_worlds_by_form_contrast','metadata_fields_excluded']},indent=2))

if __name__=='__main__': main()
