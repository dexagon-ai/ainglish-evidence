"""Narrow visible-text assignment oracle and public evidence archive; no inference.

Unrecognised frames remain unassessed. This author's audit does not rewrite an
official score, certify general English equivalence, or constitute replication.
"""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
import re
import subprocess
from urllib.request import HTTPRedirectHandler, build_opener

from ainglish.client import manifest_commitment

ROOT=Path(__file__).parent
REPO=ROOT.parent
OWN='https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/'
REMOTE={'https://x0.at/yiwf.json','https://x0.at/rjux.json'}
RAW={
 '3cf5e320-8ef0-4f79-bdc7-4c4e31969a08':'next-wave-2026-09-05/choice.attempt-3cf5e320-8ef0-4f79-bdc7-4c4e31969a08.cells.json',
 '96ac4706-3cbd-4064-ac85-5f2eadb19d46':'overnight-2026-09-05/choice.cold.attempt-96ac4706-3cbd-4064-ac85-5f2eadb19d46.cells.json',
 'ae2fc895-82a4-4d63-9262-61718ded5e6d':'overnight-2026-09-05/choice.reference.attempt-ae2fc895-82a4-4d63-9262-61718ded5e6d.cells.json',
}
RAW_REV='f66ef9f1dca95c25445373934e9cd1b0f33dd9ef'

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def save(path,value):
    path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError('Artifact redirect requires explicit review')

def archive(url):
    """Only reviewed public endpoints or exact immutable blobs in our own repo."""
    if url.startswith(OWN):
        ref,path=url[len(OWN):].split('/',1)
        if not re.fullmatch('[a-f0-9]{40}',ref) or '..' in path.split('/'):
            raise ValueError('Need an immutable reviewed source reference')
        raw=subprocess.check_output(['git','show',ref+':'+path],cwd=REPO)
    elif url in REMOTE:
        with build_opener(NoRedirect()).open(url,timeout=25) as response:
            raw=response.read(2_000_001)
    else:
        raise ValueError('Unreviewed source URL')
    if len(raw)>2_000_000:raise ValueError('Artifact exceeds 2 MB limit')
    value=json.loads(raw)
    sha=hashlib.sha256(raw).hexdigest()
    dest=ROOT/'artifacts'/(sha+'.json');dest.parent.mkdir(exist_ok=True)
    if not dest.exists():dest.write_bytes(raw)
    return value,{'source_url':url,'raw_sha256':sha,'archive':str(dest.relative_to(ROOT))}

def world(text):
    """Parse only the two published finite assignment grammars, never ledger gold."""
    primary=re.findall(r'([A-Za-z0-9-]+) permits only ([A-Z,]+)\.',text)
    if primary:
        names=[x[0] for x in primary]
        eligible=[x[1].split(',') for x in primary]
        caps=dict((a,int(n)) for a,n in re.findall(r'\b([A-Z])=(\d+)\b',text))
        if len(names)!=3 or set(caps)!={'A','B','C'}:raise ValueError('Unsupported primary world')
        return names,eligible,caps
    secondary=re.findall(r'([A-Za-z0-9-]+) allows ([^.]+)\.',text)
    if secondary and 'reviewer capacity is unlimited' in text:
        names=[x[0] for x in secondary]
        eligible=[[] if x[1]=='no reviewer' else x[1].split(', ') for x in secondary]
        if len(names)!=3 or len(set(names))!=3:raise ValueError('Unsupported secondary world')
        return names,eligible,None
    raise ValueError('Unrecognised assignment world')

def check(row):
    try:
        text=row['ainglish'].split('\n\n')[-1]
        names,eligible,caps=world(text)
        if world(row['english'].split('\n\n')[-1])!=(names,eligible,caps):
            raise ValueError('Visible arm facts differ')
        markers=re.findall(r'(same-for-all|may-vary-across)\([^)]+\)',text)
        if len(markers)!=1:raise ValueError('Unrecognised marked rule')
        rule=markers[0]
        plans=[p for p in product(*eligible) if
               (rule!='same-for-all' or len(set(p))==1) and
               (caps is None or all(p.count(v)<=caps[v] for v in p))]
        question=row['question'];valid=[];semantic=None
        if question=='Can any complete plan obey all the stated requirements?':
            semantic='yes' if plans else 'no'
            valid=[semantic]+(['no feasible assignment exists'] if not plans else [])
        elif question.startswith('A proposed plan uses IDs '):
            match=re.fullmatch(r'A proposed plan uses IDs ([A-Z,]+) in the listed member order\. Does that plan obey every stated requirement\?',question)
            if not match:raise ValueError('Unrecognised candidate question')
            semantic='yes' if tuple(match[1].split(',')) in plans else 'no'
            # Only the narrow direct answer is certified for admissibility here;
            # whether another longer true statement is also responsive is unassessed.
            valid=[semantic]
        elif question=='Among plans obeying every requirement, must the first and last listed members use the same choice ID?':
            if not plans:
                return {'status':'unassessed','reason':'Empty feasible set: natural-language must/vacuity needs review'}
            semantic='yes' if all(p[0]==p[-1] for p in plans) else 'no';valid=[semantic]
        else:
            if question.startswith('Does at least one assignment satisfy every stated requirement?'):
                semantic='yes' if plans else 'no'
            elif question.startswith('Is at least one permitted assignment possible that uses more than one reviewer identity?'):
                semantic='yes' if any(len(set(p))>1 for p in plans) else 'no'
            elif question.startswith('Does the candidate satisfy every stated requirement?'):
                pairs=dict(re.findall(r'([A-Za-z0-9-]+) → ([A-Za-z0-9-]+)',text))
                if set(pairs)!=set(names):raise ValueError('Unrecognised named candidate')
                semantic='yes' if tuple(pairs[n] for n in names) in plans else 'no'
            else:raise ValueError('Unrecognised question')
            valid=[k for k,v in re.findall(r'\b([A-Z]) = (yes|no)\.',question) if v==semantic]
        offered=[x for x in valid if x in row['options']]
        return {'status':'checked','valid_answers':offered,'key_valid':row['answer'] in offered,
                'non_unique_correct':len(offered)>1,'feasible_plans':len(plans),
                'comparator_semantic_equivalence':'not_certified'}
    except (KeyError,TypeError,ValueError) as exc:
        return {'status':'unassessed','reason':str(exc)}

def inspect(source):
    m=source['manifest'];items,receipt=archive(m['items_url'])
    items=items.get('items',items) if isinstance(items,dict) else items
    if digest(items)!=m['items_sha256']:raise ValueError('Item digest mismatch')
    if manifest_commitment(m)!=source['manifest_hash']:raise ValueError('Manifest mismatch')
    real=[r for r in items if not r.get('calibration')]
    checks=[{'item_id':r['id'],'stratum':r.get('settlement_stratum'),**check(r)} for r in real]
    bad={r['item_id']:r for r in checks if r.get('non_unique_correct') or r.get('key_valid') is False}
    attempt=source['report_target']['id'];raw_receipt=None;affected=[]
    if attempt in RAW:
        raw,raw_receipt=archive(OWN+RAW_REV+'/'+RAW[attempt])
        for cell in raw['rows']:
            if cell['item_id'] in bad:
                valid=bad[cell['item_id']]['valid_answers']
                affected.append({**cell,'semantically_correct':cell['answer'] in valid})
    return {'manifest_hash':source['manifest_hash'],'attempt_id':attempt,'items_receipt':receipt,
            'items_sha256':digest(items),'pin_verified':True,'real_items':len(real),
            'checks':checks,'unassessed':sum(x['status']=='unassessed' for x in checks),
            'non_unique_gold_items':[x['item_id'] for x in checks if x.get('non_unique_correct')],
            'invalid_gold_items':[x['item_id'] for x in checks if x.get('key_valid') is False],
            'raw_receipt':raw_receipt,'affected_raw_cells':affected,
            'wrongly_scored_false':sum(x['semantically_correct'] and x['correct'] is False for x in affected),
            'wrongly_scored_false_by_arm':dict(Counter(x['arm'] for x in affected if x['semantically_correct'] and x['correct'] is False)),
            'official_value_unchanged':source['value'],'boundary':__doc__}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('capture',type=Path);args=ap.parse_args()
    reports=[];archived=[]
    for path in sorted(args.capture.glob('*.json')):
        if not re.fullmatch(r'[a-f0-9]{64}\.json',path.name):continue
        m=json.loads(path.read_text())
        if m['proposal']['public_id'] not in ['a-g973ekza7973r5f2','a-3zjcv2sz5g53nxxd']:continue
        save(ROOT/'measurements'/path.name,m)
        if m['proposal']['public_id']=='a-g973ekza7973r5f2':
            report=inspect(m);reports.append(report)
            print(path.stem[:12],report['real_items'],len(report['non_unique_gold_items']),report['wrongly_scored_false'],report['unassessed'],flush=True)
        else:
            items,receipt=archive(m['manifest']['items_url'])
            rows=items.get('items',items) if isinstance(items,dict) else items
            if digest(rows)!=m['manifest']['items_sha256']:raise ValueError('Rent item pin mismatch')
            archived.append({'manifest_hash':m['manifest_hash'],'items_sha256':digest(rows),**receipt})
    save(ROOT/'choice-audit.json',{'kind':'ainglish.choice-semantic-audit.v1','reports':reports,'boundary':__doc__})
    save(ROOT/'artifact-index.json',{'choice_sources':[r['items_receipt'] for r in reports], 'other_public_sources':archived,
         'boundary':'Exact public artifacts retained; original manifests and URLs are not rewritten. Mirrors are not new evidence.'})

if __name__=='__main__':main()
