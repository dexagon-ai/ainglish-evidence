"""Recover a bounded, licensed technical-English corpus. No inference or scoring."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
COMMIT = 'bcee1c322115c581da27600f2ae55e5439c027eb'
TERMS = re.compile(r'\b(last|latest|final|default|assigned|significant|important)\b', re.I)


def digest(blob): return hashlib.sha256(blob).hexdigest()
def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
def write(name, value): (ROOT/name).write_bytes(json.dumps(value, indent=2, ensure_ascii=False).encode()+b'\n')


def fetch(url, limit):
    with urlopen(Request(url, headers={'User-Agent':'Dexagon-Ainglish-corpus-recovery'}), timeout=40) as r:
        blob = r.read(limit+1)
    if len(blob)>limit: raise ValueError('Acquisition bound exceeded')
    return blob


def extract(path, text):
    lines=text.splitlines(); records=[]; start=0
    for end in range(len(lines)+1):
        if end<len(lines) and lines[end].strip(): continue
        block=lines[start:end]
        if block and re.match(r'^[A-Za-z]',block[0]) and all(
            line == line.lstrip() and '`' not in line and '.. ' not in line and
            not re.fullmatch(r'[^\w\s]+',line) for line in block):
            prose=' '.join(block)
            if 15<=len(prose.split())<=120:
                records.append({'source':path,'first_line':start+1,'last_line':end,'text':prose})
        start=end+1
    return records


def acquire():
    if (ROOT/'manifest.json').exists(): raise ValueError('Archive already exists; use verify, never overwrite source history')
    tree=json.loads(fetch(f'https://api.github.com/repos/python/cpython/git/trees/{COMMIT}?recursive=1',8*1024*1024))
    if tree.get('truncated'): raise ValueError('Incomplete Git tree')
    selected=[r for r in tree['tree'] if re.fullmatch(r'Doc/tutorial/[^/]+\.rst',r['path'])]
    if not 1<=len(selected)<=40 or any(r['type']!='blob' for r in selected): raise ValueError('Unexpected inventory')
    extras=[next(r for r in tree['tree'] if r['path']==p) for p in ('LICENSE','Doc/license.rst','Doc/copyright.rst')]
    inventory=[]; total=0
    for r in sorted(selected+extras,key=lambda x:x['path']):
        path=r['path']; blob=fetch(f'https://raw.githubusercontent.com/python/cpython/{COMMIT}/{path}',1024*1024)
        total+=len(blob)
        if total>8*1024*1024: raise ValueError('Total acquisition bound exceeded')
        if hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()!=r['sha']: raise ValueError('Git blob mismatch')
        dest=ROOT/'upstream'/path; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(blob)
        inventory.append({'path':path,'bytes':len(blob),'sha256':digest(blob),'git_blob':r['sha'],
                          'source_url':f'https://raw.githubusercontent.com/python/cpython/{COMMIT}/{path}'})
    write('manifest.json', {'kind':'bounded-python-tutorial-corpus.v1','commit':COMMIT,
        'rule_sha256':digest((ROOT/'RULE.md').read_bytes()),'sources':inventory,
        'inventory_sha256':digest(canonical(inventory)), 'bytes':total,
        'rights':'PSF-2.0 with retained upstream notices; not CC0'})
    build(verify=False)


def build(verify=True):
    m=json.loads((ROOT/'manifest.json').read_bytes())
    assert m['commit']==COMMIT and m['rule_sha256']==digest((ROOT/'RULE.md').read_bytes())
    assert m['inventory_sha256']==digest(canonical(m['sources']))
    records=[]
    for r in m['sources']:
        blob=(ROOT/'upstream'/r['path']).read_bytes()
        assert digest(blob)==r['sha256'] and len(blob)==r['bytes']
        assert hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()==r['git_blob']
        if r['path'].startswith('Doc/tutorial/'):
            records.extend(extract(r['path'],blob.decode('utf-8')))
    records.sort(key=lambda r:(r['source'],r['first_line']))
    selected=[r for r in records if TERMS.search(r['text'])]
    for name,rows in [('paragraphs.json',records),('candidate-slice.json',selected)]:
        if verify: assert json.loads((ROOT/name).read_bytes())==rows
        else: write(name,rows)
    report={'kind':'technical-english-corpus-recovery.v1','sources':len(m['sources']),
        'bytes':m['bytes'],'paragraphs':len(records),'selected':len(selected),
        'paragraphs_sha256':digest(canonical(records)), 'selected_sha256':digest(canonical(selected)),
        'term_paragraph_counts':{term:sum(bool(re.search(r'\b'+term+r'\b',r['text'],re.I)) for r in records)
                                 for term in ('last','latest','final','default','assigned','significant','important')},
        'reader_calls':0,'tokenizer_calls':0,'representativeness':'narrow technical documentation only',
        'carrier_eligibility':'not assessed; no comprehension labels or Ainglish translations'}
    if verify: assert json.loads((ROOT/'recovery.json').read_bytes())==report
    else: write('recovery.json',report)
    print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['acquire','verify']);a=p.parse_args()
    acquire() if a.command=='acquire' else build()
