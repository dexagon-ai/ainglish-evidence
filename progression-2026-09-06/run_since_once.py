"""Execute one preregistered primary, retaining even identical-wording allocations."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

from ainglish import panel
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from since_study import ROOT, canonical, save


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    stem = 'since.careful'
    assert not (ROOT/(stem+'.started.json')).exists(), 'Reconcile existing campaign, never retry targets'
    c = ainglish_client()
    spec = json.loads((ROOT/(stem+'.runspec.json')).read_text())
    selection = c.suggestions(proposal='a-hjhq14a5ew4khaqp')
    p = c.proposal(c.proposal_slug_history('a-hjhq14a5ew4khaqp')['current_slug'], authenticated=True)
    assert p['stage'] in ['seconded','measured'] and p['publication_status'] == 'visible'
    assert 'token_delta' in p['evidence_readiness']['satisfied']
    assert hashlib.sha256(p['english_mapping'].encode()).hexdigest() == spec['attempt']['planned_sample']['mapping_sha256']
    from instrument import resources_free
    resources_free(spec['panel'])
    items, sha = panel.fetch_items(spec['items_url'], spec['items_sha256'])
    manifest = dict(spec, items=items, items_sha256=sha)
    panel.prepare_reader_instruments(manifest)
    for reader, qualification in zip(manifest['panel'], manifest['reader_qualifications']):
        assert datetime.fromisoformat(qualification['valid_until']) > datetime.now(timezone.utc)
        assert hashlib.sha256(canonical(panel.reader_receipt(reader))).hexdigest() == qualification['settings_sha256']
    planned = panel._planned_panel_manifest(manifest)
    settings = panel._attempt_settings(spec['attempt'], [panel.calibration_gate_statement(manifest), panel.admissibility_gate_statement(manifest)])
    save(stem+'.preflight.json', c.preflight_attempt(p['slug'], planned, **settings))
    save(stem+'.intent.json', {'at':now(), 'manifest_commitment':manifest_commitment(planned), 'manifest':planned,
        'settings':settings, 'selection':selection})
    source = {}
    for item in items:
        for arm in ['english','ainglish']:
            key = (item[arm], item['question'])
            if key in source:
                assert source[key]['item_id'] == item['id'], 'Two item identities share one literal prompt'
                source[key]['arms'].append(arm)
            else:
                source[key] = {'item_id':item['id'], 'arms':[arm], 'calibration':bool(item.get('calibration'))}
    opened, count = {}, 0
    original_mint, original_chat = c.mint_attempt, panel.chat
    save(stem+'.started.json', {'at':now(), 'pid':os.getpid(), 'retries':0})
    with (ROOT/(stem+'.calls.jsonl')).open('x') as journal, (ROOT/'raw-reader-outputs.jsonl').open('x') as raw:
        def mint(*args, **kwargs):
            receipt = original_mint(*args, **kwargs)
            save(stem+'.opened.json', receipt)
            opened.update(receipt)
            return receipt
        def chat(reader, prompt):
            record = {'at':now(), 'reader':reader['name'], 'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()}
            try:
                output, truncated = original_chat(reader, prompt)
                record.update(output=output, truncated=truncated)
                return output, truncated
            except BaseException as exc:
                record['error_type'] = type(exc).__name__
                raise
            finally:
                raw.write(json.dumps(record)+'\n'); raw.flush(); os.fsync(raw.fileno())
        def ask(reader, text, question, options):
            nonlocal count
            assert opened, 'No reader call before retained mint'
            record = dict(source[text,question], at=now(), reader=reader['name'], attempt_id=opened['attempt']['attempt_id'])
            # Identical text cannot identify the assigned arm. Preserve ambiguity
            # here; the canonical SDK cell receipt retains its actual allocation.
            try:
                answer = panel.ask(reader, text, question, options)
                record.update(answer=str(answer), absent_reason=getattr(answer,'reason',None) if panel.is_absent(answer) else None)
                return answer
            except BaseException as exc:
                record['exception_type'] = type(exc).__name__
                raise
            finally:
                journal.write(json.dumps(record)+'\n'); journal.flush(); os.fsync(journal.fileno()); count += 1
                if count % 32 == 0:
                    print(count, 'calls retained', flush=True)
        try:
            with patch.object(c,'mint_attempt',side_effect=mint), patch.object(panel,'chat',side_effect=chat):
                result = panel._run_preregistered_panel(manifest,spec,ask,c,receipt_dir=str(ROOT),receipt_stem=stem)
            if result is not None:
                save(stem+'.result.json',result)
                save(stem+'.server.json',c.attempt(result['attempt_id']))
            save(stem+'.finished.json',{'at':now(),'state':'filed' if result else 'aborted','calls':count})
            print('filed' if result else 'aborted', count, flush=True)
        except BaseException as exc:
            save(stem+'.exception.json',{'at':now(),'type':type(exc).__name__,'message':str(exc),
                'calls_retained':count,'attempt_id':opened.get('attempt',{}).get('attempt_id'),'recovery':'Reconcile retained attempt; no target retry.'})
            raise


if __name__ == '__main__':
    main()
