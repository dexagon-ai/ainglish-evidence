#!/usr/bin/env python3
"""A small deterministic train-only export; never zip the research directory."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from audit import ROOT, validate

ALLOWED = ('curriculum.jsonl','train-ainglish.jsonl','train-english.jsonl','guides.json',
           'TEACHING.md','conversations.jsonl','source-constructs.json','LICENSE-CC0-1.0.txt')
NOTICE = '''Synthetic, non-normative Ainglish teaching supplement, 6 September 2026.
CC0-1.0 language examples, derived from six ratified mappings in ainglish-core-v3.
Not an official release or a modification of that immutable bundle.
144 paired contextual cases, six teaching cards, twelve two-turn dialogue renderings.
Agent-authored with structural and semantic checks; no independent or human review claimed.
No evaluation answers, measurement payloads, private conversations or contributor identities.
The curriculum includes annotated training answers; these are not held-out evaluation data.
Instruction variants and English/Ainglish versions are not independent samples.
Source provenance and exact file digests are in source-constructs.json and MANIFEST.json.
Research and limitations: https://github.com/dexagon-ai/ainglish-evidence/tree/main/ratified-learning-pilot-2026-09-06
'''


def export(target):
    validate()
    if target.exists(): raise ValueError('Refusing to overwrite export')
    files={name:(ROOT/name).read_bytes() for name in ALLOWED}
    files['README.txt']=NOTICE.encode()
    manifest={'kind':'ainglish.non-normative-teaching-supplement.v1','license':'CC0-1.0',
              'official_release':False,'synthetic':True,'split':'train','source':'ainglish-core-v3',
              'files':{n:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for n,b in sorted(files.items())}}
    files['MANIFEST.json']=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,body in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,9,6,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644 << 16
            archive.writestr(info,body)
    return {'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'members':list(files)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args()
    print(json.dumps(export(args.output),indent=2))
