"""Historical, read-only source reconstruction audit; no new experimental claim."""
import json, math
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
import tiktoken
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client

ROOT=Path(__file__).resolve().parent
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False)

def main():
    c=ainglish_client();triage=c.dispute_triage();save(ROOT/'legacy-triage.json',triage)
    rows=[]
    for target in triage['targets']:
        h=target['manifest_hash'];m=c.measurement(h);manifest=m['manifest']
        save(ROOT/'legacy-sources'/(h+'.json'),m)
        assert manifest_commitment(manifest)==h
        row={k:target.get(k) for k in ['public_id','slug','proposal_title','metric','manifest_hash','agreement_count','disagreement_count','resolution_class']}
        row.update(attempt_id=m.get('attempt_id'),confirmed=m.get('confirmed'),evidence_state=m['evidence_state'],
                   source_author=m['submitter'],value=m['value'],manifest_reconstructable=True,
                   modern_mint=not (m.get('attempt') or {}).get('backfilled',True))
        if m['metric']=='token_delta':
            pairs=manifest.get('test_set',[])
            if isinstance(pairs,dict):pairs=pairs.get('pairs',[])
            means=[]
            try:
                with patch('tiktoken.load.read_file',side_effect=RuntimeError('Cached encodings only; no download')):
                    for model in manifest['models']:
                        enc=tiktoken.get_encoding(model)
                        ds=[]
                        for p in pairs:
                            e=p.get('english',p.get('baseline')) if isinstance(p,dict) else p[0]
                            a=p['ainglish'] if isinstance(p,dict) else p[1]
                            ds.append(len(enc.encode(a))-len(enc.encode(e)))
                        means.append({'model':model,'value':sum(ds)/len(ds)})
                row.update(pairs=len(pairs),recount=means,headline_recounts_at_6dp=math.isclose(max(x['value'] for x in means),m['value'],abs_tol=.000001,rel_tol=0))
            except (ValueError,KeyError,TypeError,RuntimeError,ZeroDivisionError) as exc:
                row['recount_stop']=type(exc).__name__+': '+str(exc)
        else:
            row['reader_contract']={k:manifest.get(k) for k in ['models','items_url','items_sha256','prompt_template','comparison_identity','interval_kind']}
            row['reader_boundary']='Manifest retention does not establish access to the original hosted reader, raw answers, or a statistically independent instrument.'
        rows.append(row)
        print(row['metric'],h[:8],row.get('pairs'),row.get('headline_recounts_at_6dp'),flush=True)
    save(ROOT/'legacy-audit.json',{'at':datetime.now(timezone.utc).isoformat(),'mutation_count':0,
         'targets':rows,'summary':dict(Counter(x['metric'] for x in rows)),
         'boundary':'Legacy identity is not an exclusion verdict. Historical recount is not prospective replication or a semantic-fidelity certificate.'})

if __name__=='__main__':main()
