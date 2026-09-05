"""First and only reader observations for two previously frozen, now-seconded kits."""
from datetime import datetime, timezone
import hashlib, json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from unittest.mock import patch
from ainglish import estimand, panel
from ainglish.reader_qualification import attach
from local_colony_auth import ainglish_client
from prepare import save

ROOT=Path(__file__).resolve().parent
KITS=ROOT.parent/'progression-studies-2026-09-05'
ORDER=['quantity','choice']
IDS={'quantity':'a-k2d3rxn56qysr74n','choice':'a-g973ekza7973r5f2'}
canonical=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()

def prepare(commit):
    subprocess.run([sys.executable,str(KITS/'test_next_kits.py')],check=True)
    base=json.loads((ROOT/'verdict.careful.preflight-fixed.runspec.json').read_text())
    for name in ORDER:
        items=json.loads((KITS/(name+'.kit-v1.json')).read_text())
        rel=str((KITS/(name+'.kit-v1.json')).relative_to(ROOT.parent))
        frozen=subprocess.run(['git','show',commit+':'+rel],cwd=ROOT.parent,check=True,capture_output=True).stdout
        assert json.loads(frozen)==items
        p=json.loads((ROOT/(name+'-fresh.json')).read_text())
        assert p['stage']=='seconded' and not p['evidence_readiness']['prerequisites']
        strata=list(dict.fromkeys(i['settlement_stratum'] for i in items if not i.get('calibration')))
        assert len(strata)==6 and len(items)==200
        population=('32 authored numeric frames crossed with two operations and three start/order conditions, four quantity/unit domains' if name=='quantity'
            else '32 authored assignment frames crossed with two rules and three consequence tasks, four choice-slot domains')
        spec={'construct':p['form'],'slug':p['slug'],'metric':'comprehension_accuracy_delta',
            'seed':2026090570+ORDER.index(name),'panel':base['panel'],'models':base['models'],'panel_neff':2,
            'admissibility':base['admissibility'],'planted_arm':'ainglish','calibration_min_gap':0.5,
            'comparator':{'kind':'complete-careful-english-v1','description':'Complete concise registered English, identical consequence context and common constraints; no bare ambiguous primary.'},
            'comparison_identity':{'comparator_genre':'complete-careful-english-v1','exposure':'cold-no-added-reference',
                'reader_class':'two fixed qualified local Q4 lineages','form_strata':strata,'pair_rendering':population},
            'items_url':f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{rel}',
            'items_sha256':hashlib.sha256(canonical(items)).hexdigest(),
            'settlement_strata':[{'id':s,'weight':1} for s in strata],
            'estimand_contract':estimand.declaration_v2(population=population+'; not humans, arbitrary prose or a population of all models',
                item_set_construction={'design':'previously-frozen-ledger-kit-v1','items':192,'strata':strata,
                    'weighting':'six equal strata','gold':'independent symbolic arithmetic or exhaustive feasible-assignment enumeration',
                    'limitations':'Repeated authored frames across conditions; balanced answer positions do not imply balanced semantic labels.'},
                reader_class='Fixed digest/settings-bound Mistral Small 3.2 24B Q4 and Gemma 3 12B Q4; prior unrelated-control qualifications',
                window='Single stateless cold call per assigned item/reader arm; no visible definition, training or retries',
                selection_rules={'calibration':'eight target-independent planted controls; every reader gap at least 0.5',
                    'faults':'zero absent, off-option, truncated or transport-fault cells; stop and retain, never retry',
                    'publication':'all admitted finite outcomes filed, regardless of direction; no gate based on real accuracy'}),
            'attempt':{'proposal_revision':p['slug'],
                'estimand':f'First original on {population}. 192 scored cases in six equal-weight load-bearing strata; 2 fixed qualified readers; Ainglish minus complete careful English accuracy in percentage points. No independent replication or future-trained inference.',
                'admissibility_gates':['third independent second clears the attention gate and current contract has no unmet token prerequisite',
                    'unchanged current mapping and digest-pinned previously published inputs; five independent kit tests pass before spend',
                    'exact unexpired reader qualification settings; no new models or displacement of another GPU workload',
                    'fixed six-stratum sample and zero-fault budget; every admitted outcome filed and every abort retained without retry',
                    'SDK item-bootstrap interval is conditional on this authored item population and fixed readers; repeated frames are not independent evidence of broad model or human generalisation'],
                'planned_sample':{'scientific_items':192,'calibration_items':8,'readers':2,'real_calls':384,'calibration_calls':32,
                    'strata':strata,'source_commit':commit,'mapping_sha256':hashlib.sha256(p['english_mapping'].encode()).hexdigest(),
                    'reporting':'official six-stratum result, per-reader and per-stratum arms, conditional item bootstrap; no claim of all-model uncertainty'}}}
        spec=attach(spec,base['reader_qualifications'])
        manifest=dict(spec,items=items)
        panel.prepare_reader_instruments(manifest); panel._planned_panel_manifest(manifest)
        save(name+'.runspec.json',spec)
        print(name,'mock preflight passed; 416 planned calls; no observations',flush=True)

def run():
    assert not (ROOT/'newly-seconded-start.json').exists(),'Existing observation obligation: reconcile; never restart'
    subprocess.run([sys.executable,str(KITS/'test_next_kits.py')],check=True)
    save('newly-seconded-start.json',{'at':datetime.now(timezone.utc).isoformat(),'order':ORDER,'model_downloads':0,'inference_retries':0})
    outcomes=[]
    for name in ORDER:
        c=ainglish_client(); opened={}; count=0; journal=None
        try:
            spec=json.loads((ROOT/(name+'.runspec.json')).read_text())
            with urllib.request.urlopen('http://127.0.0.1:11434/api/ps',timeout=10) as r: loaded=json.load(r)['models']
            assert all(m.get('name',m.get('model')) in {x['model'] for x in spec['panel']} for m in loaded),'Unrelated workload loaded'
            suggestions=c.suggestions(proposal=IDS[name]); p=c.proposal(c.proposal_slug_history(IDS[name])['current_slug'],authenticated=True)
            assert p['stage']=='seconded' and p['publication_status']=='visible' and not p['measurements']
            assert p['evidence_readiness']['prerequisites']==[]
            assert hashlib.sha256(p['english_mapping'].encode()).hexdigest()==spec['attempt']['planned_sample']['mapping_sha256']
            data,sha=panel.fetch_items(spec['items_url'],spec['items_sha256'])
            manifest=dict(spec,items=data,items_sha256=sha);panel.prepare_reader_instruments(manifest)
            for reader,q in zip(manifest['panel'],manifest['reader_qualifications']):
                assert datetime.fromisoformat(q['valid_until'])>datetime.now(timezone.utc)
                assert hashlib.sha256(canonical(panel.reader_receipt(reader))).hexdigest()==q['settings_sha256']
            planned=panel._planned_panel_manifest(manifest)
            gates=[panel.calibration_gate_statement(manifest),panel.admissibility_gate_statement(manifest)]
            settings=panel._attempt_settings(spec['attempt'],gates)
            save(name+'.preflight.json',c.preflight_attempt(p['slug'],planned,**settings))
            save(name+'.intent.json',{'planned_manifest':planned,'settings':settings,'suggestions':suggestions})
            original=c.mint_attempt
            def mint(*a,**kw):
                receipt=original(*a,**kw);save(name+'.opened.json',receipt);opened.update(receipt);return receipt
            source={(r[arm],r['question']):(r['id'],arm,bool(r.get('calibration'))) for r in data for arm in ['english','ainglish']}
            assert len(source)==2*len(data)
            journal=(ROOT/(name+'.calls.jsonl')).open('x')
            def ask(reader,text,question,options):
                nonlocal count
                assert opened
                ident,arm,control=source[text,question]
                record={'item_id':ident,'arm':arm,'calibration':control,'reader':reader['name'],'attempt_id':opened['attempt']['attempt_id']}
                try:
                    answer=panel.ask(reader,text,question,options);record['answer']=str(answer)
                    record['absent_reason']=getattr(answer,'reason',None) if panel.is_absent(answer) else None
                    return answer
                except (Exception,SystemExit) as exc:record['exception_type']=type(exc).__name__;raise
                finally:
                    journal.write(json.dumps(record)+'\n');journal.flush();os.fsync(journal.fileno());count+=1
                    if count%32==0:print(name,count,'calls retained',flush=True)
            with patch.object(c,'mint_attempt',side_effect=mint):
                result=panel._run_preregistered_panel(manifest,spec,ask,c,receipt_dir=str(ROOT),receipt_stem=name)
            if result is not None:
                save(name+'.result.json',result)
                save(name+'.server.json',c.attempt(result['attempt_id']))
            outcomes.append({'name':name,'state':'filed' if result is not None else 'aborted','calls':count,'value':None if result is None else result['value']})
        except (Exception,SystemExit) as exc:
            save(name+'.exception.json',{'type':type(exc).__name__,'message':str(exc),'calls_retained':count,'attempt_id':opened.get('attempt',{}).get('attempt_id'),'no_retry':True})
            outcomes.append({'name':name,'state':'reconcile-retained-record','calls':count})
        finally:
            if journal is not None:journal.close()
    save('newly-seconded-finished.json',outcomes);print(json.dumps(outcomes),flush=True)

if __name__=='__main__':
    prepare(sys.argv[2]) if sys.argv[1]=='prepare' else run()
