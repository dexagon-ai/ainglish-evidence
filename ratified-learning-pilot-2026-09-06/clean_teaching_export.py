#!/usr/bin/env python3
"""Post-run teaching cleanup; immutable experiment inputs are never rewritten."""
import hashlib
import json
import zipfile
from audit import ROOT, rows, validate
from export_training import ALLOWED, NOTICE


def cleaned_files():
    validate()
    kept=[];seen=set();removed=[]
    for row in rows('curriculum.jsonl'):
        signature=json.dumps({k:row[k] for k in ('ainglish','english','question','options','answer')},sort_keys=True)
        if signature in seen: removed.append(row['id'])
        else: seen.add(signature);kept.append(row)
    assert len(kept)==126 and len(removed)==18
    ids={r['id'] for r in kept}
    files={name:(ROOT/name).read_bytes() for name in ALLOWED}
    def encode(values):return ''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in values).encode()
    files['curriculum.jsonl']=encode(kept)
    for language in ('ainglish','english'):
        selected=[r for r in rows(f'train-{language}.jsonl') if r['id'] in ids]
        assert len(selected)==126
        files[f'train-{language}.jsonl']=encode(selected)
    files['README.txt']=(NOTICE.replace('144 paired contextual cases','126 distinct paired contextual cases')+
        '\nPost-run teaching-only deduplication: 18 exact repeated case rows removed.\n'
        'The adapters were trained on the original 144 rows, not this cleaned export.\n'
        'Original training, evaluation and result artifacts remain immutable for reproduction.\n').encode()
    manifest={'kind':'ainglish.non-normative-teaching-supplement.v1','revision':'deduplicated-1',
        'license':'CC0-1.0','official_release':False,'synthetic':True,'split':'train','source':'ainglish-core-v3',
        'distinct_paired_cases':126,'removed_exact_duplicate_rows':removed,
        'experiment_training_unchanged':True,
        'files':{n:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for n,b in sorted(files.items())}}
    files['MANIFEST.json']=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
    assert set(files)==set(ALLOWED)|{'README.txt','MANIFEST.json'}
    return files


if __name__=='__main__':
    files=cleaned_files()
    target=ROOT/'teaching-supplement-deduplicated.zip'
    with zipfile.ZipFile(target,'x') as archive:
        for name,body in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,9,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,body)
    print(json.dumps({'file':target.name,'distinct_cases':126,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
