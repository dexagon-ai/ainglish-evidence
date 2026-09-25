"""Bounded recovery of pinned source bytes and deterministic paragraph slices."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent
SOURCES=[('python/cpython','bcee1c322115c581da27600f2ae55e5439c027eb'),
         ('scipy/scipy','b1296b9b4393e251511fe8fdd3e58c22a1124899')]
CPATHS=['Doc/whatsnew/3.12.rst','Doc/whatsnew/3.13.rst','Doc/using/cmdline.rst',
        'Doc/library/configparser.rst','LICENSE','Doc/license.rst','Doc/copyright.rst']
TERMS=re.compile(r'\b(last|latest|final|default|assigned|significant|important)\b',re.I)


def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def write(name,v):(ROOT/name).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')


def fetch(url,bound):
    with urlopen(Request(url,headers={'User-Agent':'Dexagon-bounded-corpus'}),timeout=40) as r:b=r.read(bound+1)
    if len(b)>bound:raise ValueError('Acquisition bound exceeded')
    return b


def extract(path,text,repo):
    rows=[];start=0;lines=text.splitlines()
    for end in range(len(lines)+1):
        if end<len(lines) and lines[end].strip():continue
        block=lines[start:end];text='\n'.join(block)
        if block and re.match(r'^[A-Za-z]',block[0]) and 15<=len(text.split())<=160:
            # Refuse headings/tables; keep inline markup and source wrapping.
            if not any(re.fullmatch(r'[=~\-^+| :]+',line) for line in block):
                rows.append({'repository':repo,'path':path,'first_line':start+1,'last_line':end,'text':text})
        start=end+1
    return rows


def acquire():
    if (ROOT/'manifest.json').exists():raise ValueError('Archive exists; use verify')
    records=[];total=0
    for repo,commit in SOURCES:
        tree=json.loads(fetch(f'https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1',8*1024*1024))
        assert not tree.get('truncated')
        paths=CPATHS if repo=='python/cpython' else ['doc/source/tutorial/stats/hypothesis_tests.rst','LICENSE.txt']
        assert paths and len(paths)<=80
        index={r['path']:r for r in tree['tree']}
        for path in sorted(paths):
            row=index[path];assert row['type']=='blob'
            url=f'https://raw.githubusercontent.com/{repo}/{commit}/{path}'
            blob=fetch(url,2*1024*1024);total+=len(blob)
            assert total<=8*1024*1024
            assert hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()==row['sha']
            target=ROOT/'upstream'/repo/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(blob)
            records.append({'repository':repo,'commit':commit,'path':path,'source_url':url,
                            'bytes':len(blob),'sha256':sha(blob),'git_blob':row['sha']})
    write('manifest.json',{'rule_sha256':sha((ROOT/'RULE.md').read_bytes()),'sources':records,
                          'total_bytes':total,'rights':'Retained PSF and BSD upstream notices; not CC0'})
    build(False)


def build(verify=True):
    m=json.loads((ROOT/'manifest.json').read_bytes());assert sha((ROOT/'RULE.md').read_bytes())==m['rule_sha256']
    rows=[]
    for r in m['sources']:
        blob=(ROOT/'upstream'/r['repository']/r['path']).read_bytes()
        assert sha(blob)==r['sha256'] and len(blob)==r['bytes']
        assert hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()==r['git_blob']
        if r['path'].endswith('.rst') and r['path'] not in ('Doc/license.rst','Doc/copyright.rst'):
            rows.extend(extract(r['path'],blob.decode('utf-8'),r['repository']))
    rows.sort(key=lambda r:(r['repository'],r['path'],r['first_line']))
    selected=[r for r in rows if TERMS.search(r['text'])]
    report={'sources':len(m['sources']),'bytes':m['total_bytes'],'paragraphs':len(rows),'selected':len(selected),
            'paragraphs_sha256':sha(canonical(rows)),'selected_sha256':sha(canonical(selected)),
            'term_counts':{term:sum(bool(re.search(r'\b'+term+r'\b',r['text'],re.I)) for r in rows)
                           for term in ('last','latest','final','default','assigned','significant','important')},
            'reader_calls':0,'tokenizer_calls':0,'not_a_representative_sample':True,'not_a_claim_carrier':True}
    for name,data in [('paragraphs.json',rows),('candidate-slice.json',selected),('recovery.json',report)]:
        if verify:assert json.loads((ROOT/name).read_bytes())==data
        else:write(name,data)
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['acquire','verify']);args=p.parse_args()
    acquire() if args.command=='acquire' else build()
