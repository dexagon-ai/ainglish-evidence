"""Fresh source/eligibility audit and immutable item recovery. No model calls or writes to governance."""
from datetime import datetime, timezone
import hashlib
import json
import urllib.request
from pathlib import Path
from ainglish import panel
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'settlement-audit'
SOURCES = [('approx', 'dfbe63f7'), ('preference-careful', 'b661b028'),
           ('preference-bare', 'edb44cee'), ('instruction-scope', '85a36ba6'),
           ('free', '12f28a15'), ('since', 'dbd86e1554733a6a375d560eaab64840eed7dcbcd190dc112be0d9af41d246a7')]

def save(name, value):
    with (OUT/name).open('x') as f: json.dump(value,f,indent=2,ensure_ascii=False)

def main():
    OUT.mkdir(exist_ok=True)
    c=ainglish_client(); summary=[]
    with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=10) as response:
        models=json.load(response)['models']
    if not (OUT/'local-roster.json').exists():
        save('local-roster.json',{'at':datetime.now(timezone.utc).isoformat(),
             'models':[{'name':r['name'],'digest':r['digest']} for r in models], 'downloads':0})
    for name,prefix in SOURCES:
        path=OUT/(name+'.source.json')
        if path.exists(): source=json.loads(path.read_text())
        else:
            full = next((ROOT/'sources').glob(prefix+'*.json')).stem if len(prefix) < 64 else prefix
            source=c.measurement(full)
            save(name+'.source.json',source)
        manifest=source['manifest']; digest=source['manifest_hash']
        record={'name':name,'manifest_hash':digest,'metric':source['metric'],'value':source['value'],
            'evidence_state':source.get('evidence_state'),'confirmed':source.get('confirmed'),
            'is_replication':source.get('is_replication'),'retraction':source.get('retraction'),
            'item_counts':manifest.get('item_counts'),'item_source':manifest.get('items_url'),
            'readers':manifest.get('readers'),'settlement_strata':manifest.get('settlement_strata'),
            'stratum_results':source.get('stratum_results')}
        url=manifest.get('items_url')
        if url and url.startswith('https://'):
            items,sha=panel.fetch_items(url,manifest['items_sha256'])
            save(name+'.items.json',items)
            record.update(recovered_items=len(items),canonical_items_sha256=sha)
        elif name == 'instruction-scope' and url == 'items.json':
            recovered='https://raw.githubusercontent.com/reticuli-labs/panel-artifacts/4f617353cf2f771432cd04d143e97e4db7e958db/thisonce-appl-2026-08-31/items.json'
            items,sha=panel.fetch_items(recovered,manifest['items_sha256'])
            save(name+'.items.json',items)
            record.update(recovered_items=len(items),canonical_items_sha256=sha,recovered_url=recovered,
                recovery_basis='Author public thread names the directory and digest; Git history resolves the immutable freeze commit; exact canonical digest verified.')
        elif url:
            record['artifact_recovery']='relative URL; no immutable recovery established'
        elif 'test_set' in manifest:
            record['recovered_items']=len(manifest['test_set'])
        summary.append(record)
        print(name,record['evidence_state'],record['confirmed'],record.get('recovered_items'),flush=True)
    save('summary.json',{'at':datetime.now(timezone.utc).isoformat(),'model_calls':0,'sources':summary})

if __name__=='__main__': main()
