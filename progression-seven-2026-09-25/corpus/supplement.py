"""Separate pinned SciPy reporting-context acquisition; no model/tokenizer calls."""
import argparse
import hashlib
import json
import re
from recover import ROOT, fetch, sha, canonical, write, TERMS

COMMIT='b1296b9b4393e251511fe8fdd3e58c22a1124899'
BASE='doc/source/tutorial/stats/'


def extract(path,text):
    records=[];block=[];start=None;fence=None
    lines=text.splitlines()
    for i,line in enumerate(lines+[''],1):
        match=re.match(r'^\s*(`{3,}|~{3,})',line)
        if match:
            token=match[1]
            if fence is None:fence=(token[0],len(token))
            elif token[0]==fence[0] and len(token)>=fence[1]:fence=None
            line=''
        elif fence is not None:line=''
        if not line.strip():
            if block and re.match(r'^[A-Za-z]',block[0]) and 15<=len(' '.join(block).split())<=160:
                records.append({'path':path,'first_line':start,'last_line':i-1,'text':'\n'.join(block)})
            block=[];start=None
        else:
            if start is None:start=i
            block.append(line)
    return records


def acquire():
    if (ROOT/'supplement-manifest.json').exists():raise ValueError('Supplement already captured')
    index=(ROOT/'upstream/scipy/scipy'/BASE/'hypothesis_tests.rst').read_text()
    names=re.findall(r'^    (hypothesis_[a-z0-9_]+\.md)$',index,re.M)
    assert 1<=len(names)<=24 and len(names)==len(set(names))
    tree=json.loads(fetch(f'https://api.github.com/repos/scipy/scipy/git/trees/{COMMIT}?recursive=1',8*1024*1024))
    assert not tree.get('truncated');by={r['path']:r for r in tree['tree']}
    records=[];total=0
    for name in names:
        path=BASE+name;entry=by[path];assert entry['type']=='blob'
        url=f'https://raw.githubusercontent.com/scipy/scipy/{COMMIT}/{path}'
        b=fetch(url,2*1024*1024);total+=len(b);assert total<=4*1024*1024
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==entry['sha']
        target=ROOT/'upstream/scipy/scipy'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
        records.append({'path':path,'url':url,'bytes':len(b),'sha256':sha(b),'git_blob':entry['sha']})
    write('supplement-manifest.json',{'commit':COMMIT,'rule_sha256':sha((ROOT/'SUPPLEMENT-RULE.md').read_bytes()),
        'index_sha256':sha(index.encode()),'sources':records,'total_bytes':total,'rights':'BSD-3-Clause, not CC0'})
    build(False)


def build(verify=True):
    m=json.loads((ROOT/'supplement-manifest.json').read_bytes());assert m['rule_sha256']==sha((ROOT/'SUPPLEMENT-RULE.md').read_bytes())
    rows=[]
    for r in m['sources']:
        b=(ROOT/'upstream/scipy/scipy'/r['path']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_blob']
        rows+=extract(r['path'],b.decode())
    rows.sort(key=lambda r:(r['path'],r['first_line']));selected=[r for r in rows if TERMS.search(r['text'])]
    result={'sources':len(m['sources']),'bytes':m['total_bytes'],'paragraphs':len(rows),'selected':len(selected),
        'paragraphs_sha256':sha(canonical(rows)),'selected_sha256':sha(canonical(selected)),
        'reader_calls':0,'tokenizer_calls':0,'not_a_claim_carrier':True}
    for name,value in [('supplement-paragraphs.json',rows),('supplement-slice.json',selected),('supplement-recovery.json',result)]:
        if verify:assert json.loads((ROOT/name).read_bytes())==value
        else:write(name,value)
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['acquire','verify']);a=p.parse_args()
    acquire() if a.command=='acquire' else build()
