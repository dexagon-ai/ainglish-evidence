"""Offline low-mixture byte-level BPE experiment. Freeze before training."""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT=Path(__file__).resolve().parent
CORPUS=Path('/home/dexagon/codex/worktrees/web-language-counts-20260907/public/corpus/slice-cfb0f4433028.json')
TRAIN_BYTES=4_000_000
EVAL_BYTES=1_000_000
MIXTURES=[0.001,0.01,0.05]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(path):return sha(path.read_bytes())
def save(path,value):
 with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def truncate(text,n):return text.encode()[:n].decode('utf-8',errors='ignore')
def corpus_records():
 envelope=json.loads(CORPUS.read_text())
 marker=re.compile(r'\b(?:we-including-you|we-excluding-you|fact-not-known|choice-not-made|start-by|complete-by|or-both|not-both|as-one|each-alone|supersedes\(|supplements\()')
 records=[]
 for r in envelope['records']:
  text='\n'.join(r[k] for k in ['title','body'] if isinstance(r.get(k),str))
  if len(text)<100 or 'ainglish' in text.lower() or marker.search(text):continue
  ident=r['kind']+'/'+r['id']
  records.append((sha(ident.encode()),ident,text))
 records.sort()
 train=[];test=[];nt=ne=0
 for h,ident,text in records:
  if int(h[:2],16)%4==0 and ne<EVAL_BYTES:
   part=truncate(text,EVAL_BYTES-ne);test.append((ident,part));ne+=len(part.encode())
  elif int(h[:2],16)%4!=0 and nt<TRAIN_BYTES:
   part=truncate(text,TRAIN_BYTES-nt);train.append((ident,part));nt+=len(part.encode())
 assert nt>=TRAIN_BYTES-3 and ne>=EVAL_BYTES-3,(nt,ne)
 assert not {r[0] for r in train}&{r[0] for r in test}
 return train,test

def material():
 train,test=corpus_records()
 base=''.join(x[1] for x in train)
 teaching=[json.loads(line) for line in (ROOT.parent/'contextual-teaching-2026-09-07/curriculum.jsonl').read_text().splitlines()]
 return base,test,teaching

def exposure(teach,mixture):
 # Same paired records and occurrence count in both arms. Neutral background fills
 # the shorter arm. Neither arm gets an extra trained Ainglish definition.
 cap=int(TRAIN_BYTES*mixture);texts={'ainglish':'','english':''};ids=[];i=0
 while True:
  r=teach[i%len(teach)];parts={lang:r[lang]+'\n' for lang in texts}
  if max(len((texts[lang]+parts[lang]).encode()) for lang in texts)>cap:break
  for lang in texts:texts[lang]+=parts[lang]
  ids.append(r['id']);i+=1
 assert ids
 return texts,ids

def cases():
 # Collateral heldouts are authored here; no fetched code corpus is redistributed.
 code=[]
 for n in range(16):
  code.append(f'def packet_{n}(records):\n    result = {{"ready": [], "pending": []}}\n    for key, value in records.items():\n        if value is None:\n            result["pending"].append(key)\n        elif value >= {n+3}:\n            result["ready"].append((key, value))\n    return result\n')
 punctuation=['A—B; C–D. E-F / G_H.', '“Quoted words”, apostrophes’ and (nested [brackets]).',
  'Résumé naïve façade; café, jalapeño, São Paulo.', '£12.50; €7,25; $0.00; ⅔ ≠ 0.67.',
  '日本語 / العربية / हिंदी / Ελληνικά', 'A\tB\n\nC  D\r\nE',
  '🙂 ⚙️ 🧪 → ← ≥ ≤ ∑ Δ ⊥', 'path/to/file.json?x=1&y=2#section',
  '2026-11-17T18:03:22+00:00', 'a\u0301 versus á; \u200b zero-width space.',
  '{"line":"one\\ntwo","empty":[],"ok":true}', '[] () {} <> := == != -> =>',
  'MiXeDCase lowerUPPER snake_case kebab-case.', '10,000.000_01 + 0xFF + 1e-09',
  '\n    indentation\n\tand tabs\n', 'Repeated... punctuation!!! Really???']
 # New lexical heldout only, not a new grammar-transfer test. Same eight paired
 # frame types per family; no teaching record copied or target-dependent selection.
 import importlib.util
 spec=importlib.util.spec_from_file_location('teaching',ROOT.parent/'contextual-teaching-2026-09-07/build.py')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 evaluation=[]
 for family in ['participants','unknown','deadline','alternatives','multiplicity','update']:
  for v in range(8):
   a,e,q,g,note=mod.render(family,('numismatics','coin register','mint diagram'),v)
   evaluation.append({'id':family+'/'+str(v),'ainglish':a,'english':e,'family':family})
 return {'code':code,'punctuation_unicode':punctuation,'ainglish_pairs':evaluation}

def build():
 base,test,teach=material();evaluation=cases()
 forbidden={r[k] for r in teach for k in ['ainglish','english']}
 assert not forbidden&{r[k] for r in evaluation['ainglish_pairs'] for k in ['ainglish','english']}
 profiles=[]
 for mixture in MIXTURES:
  texts,ids=exposure(teach,mixture)
  profiles.append({'nominal_max_fraction':mixture,'occurrences':len(ids),'unique_records':len(set(ids)),
   'ordered_id_sha256':sha(json.dumps(ids).encode()),'arms':{lang:{'exposure_bytes':len(t.encode()),
   'achieved_fraction':len(t.encode())/TRAIN_BYTES,'exposure_sha256':sha(t.encode())} for lang,t in texts.items()}})
 train,test=corpus_records()
 save(ROOT/'split.json',{'train':[{'id':i,'bytes':len(t.encode()),'sha256':sha(t.encode())} for i,t in train],
  'test':[{'id':i,'bytes':len(t.encode()),'sha256':sha(t.encode())} for i,t in test]})
 save(ROOT/'evaluation.json',evaluation)
 save(ROOT/'PLAN.json',{'kind':'ainglish.low-exposure-tokenizer-study.v1','random_seed':20260907,
  'training_bytes_per_cell':TRAIN_BYTES,'english_eval_bytes':EVAL_BYTES,'mixtures':profiles,
  'vocabulary_sizes':[8000,16000],'presegmentation':['bytelevel-regex','whitespace-preserving'],
  'cells':28,'conditions':['background-only','paired-A-exposure','paired-English-exposure'],
  'tokenizers_version':importlib.metadata.version('tokenizers'),'corpus_sha256':digest(CORPUS),
  'teaching_sha256':digest(ROOT.parent/'contextual-teaching-2026-09-07/curriculum.jsonl'),
  'boundaries':['Same record IDs and occurrence counts in paired arms; achieved byte fractions differ and are reported.',
   '4MB total byte budget; the shorter teaching arm receives more of the fixed background prefix. This is byte-budget matched, not identical background exposure.',
   'Whole records split by deterministic ID hash before UTF8-safe budget clipping; documents do not cross splits.',
   'Literal filtering only: the background is not certified free of semantic Ainglish influence.',
   'All 256 byte tokens supplied; every heldout string must decode byte-exactly. No unknown-token collapse or whitespace loss receives credit.',
   'New lexical Ainglish cases share the authored teaching frames; this is not independent grammar transfer.',
   'Local newly trained BPEs are not production tokenizers, model weight training, adoption or a forecast. No downloads or raw background redistribution.'],
  'analysis':'Every cell reports totals on the same heldout English documents, synthetic code, punctuation/Unicode and paired language cases. Report costs against each matched background-only tokenizer, plus paired-A versus paired-English exposure. No best-cell selection.'})
 save(ROOT/'FROZEN.json',{name:digest(ROOT/name) for name in ['study.py','README.md','PLAN.json','split.json','evaluation.json']})
 print('Frozen design:28 tokenizers; no training performed.')

def verify():
 frozen=json.loads((ROOT/'FROZEN.json').read_text())
 for name,h in frozen.items():assert digest(ROOT/name)==h,name
 commit=subprocess.check_output(['git','log','-1','--format=%H','--',str(ROOT/'FROZEN.json')],cwd=ROOT.parent,text=True).strip()
 assert commit
 subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT.parent,check=True)
 for name in [*frozen,'FROZEN.json']:
  assert subprocess.check_output(['git','show',f'{commit}:{ROOT.name}/{name}'],cwd=ROOT.parent)==(ROOT/name).read_bytes(),name
 return commit

def run():
 commit=verify();plan=json.loads((ROOT/'PLAN.json').read_text())
 assert importlib.metadata.version('tokenizers')==plan['tokenizers_version']
 assert digest(CORPUS)==plan['corpus_sha256']
 assert digest(ROOT.parent/'contextual-teaching-2026-09-07/curriculum.jsonl')==plan['teaching_sha256']
 assert not (ROOT/'execution').exists(),'Do not repeat or silently resume a spent experiment'
 (ROOT/'execution').mkdir();save(ROOT/'execution/intent.json',{'freeze':commit,'at':time.time()})
 os.environ['RAYON_NUM_THREADS']='2';os.environ['TOKENIZERS_PARALLELISM']='false'
 from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers, Regex
 base,test,teach=material();heldout=json.loads((ROOT/'evaluation.json').read_text())
 evals={'english':[t for _,t in test], 'code':heldout['code'],'punctuation_unicode':heldout['punctuation_unicode'],
        'paired_ainglish':[r['ainglish'] for r in heldout['ainglish_pairs']],
        'paired_english':[r['english'] for r in heldout['ainglish_pairs']]}
 results=[]
 for vocab in plan['vocabulary_sizes']:
  for policy in plan['presegmentation']:
   conditions=[('baseline',0.0,None)] + [(lang,mix,exposure(teach,mix)[0][lang]) for mix in MIXTURES for lang in ['ainglish','english']]
   for lang,mix,supplement in conditions:
    ident=f'{vocab}-{policy}-{lang}-{mix:g}';started=time.time()
    text=base if supplement is None else supplement+truncate(base,TRAIN_BYTES-len(supplement.encode()))
    tokenizer=Tokenizer(models.BPE())
    if policy=='bytelevel-regex':tokenizer.pre_tokenizer=pre_tokenizers.ByteLevel(add_prefix_space=False,use_regex=True)
    else:tokenizer.pre_tokenizer=pre_tokenizers.Sequence([pre_tokenizers.Split(Regex(r'\s+|\S+'),behavior='isolated'),pre_tokenizers.ByteLevel(add_prefix_space=False,use_regex=False)])
    tokenizer.decoder=decoders.ByteLevel()
    trainer=trainers.BpeTrainer(vocab_size=vocab,min_frequency=2,show_progress=False,initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),special_tokens=[])
    # Bound individual input strings by lines, without dropping their line endings.
    tokenizer.train_from_iterator(text.splitlines(keepends=True),trainer=trainer)
    tokenizer_path=ROOT/'execution'/f'{ident}.json';tokenizer.save(str(tokenizer_path))
    row={'id':ident,'vocab_limit':vocab,'actual_vocab':tokenizer.get_vocab_size(),'policy':policy,'exposure_language':lang,
         'nominal_fraction':mix,'training_bytes':len(text.encode()),'training_sha256':sha(text.encode()),
         'tokenizer_sha256':digest(tokenizer_path),'evaluation':{}}
    for label,strings in evals.items():
     counts=[];bad=[]
     for i,value in enumerate(strings):
      ids=tokenizer.encode(value).ids
      if tokenizer.decode(ids)!=value:bad.append(i)
      counts.append(len(ids))
     row['evaluation'][label]={'strings':len(strings),'bytes':sum(len(s.encode()) for s in strings),'tokens':sum(counts),
       'per_string':counts,'roundtrip_failures':bad}
    row['passed_lossless_gate']=not any(v['roundtrip_failures'] for v in row['evaluation'].values())
    row['elapsed_seconds']=time.time()-started
    save(ROOT/'execution'/f'{ident}.result.json',row);results.append(row)
    print(ident,'lossless',row['passed_lossless_gate'],'seconds',round(row['elapsed_seconds'],2),flush=True)
 save(ROOT/'RESULTS.json',{'freeze':commit,'cells':results,'all_lossless':all(r['passed_lossless_gate'] for r in results)})
 baseline={(r['vocab_limit'],r['policy']):r for r in results if r['exposure_language']=='baseline'}
 lines=['# Low-exposure tokenizer results','', 'All 28 predeclared cells retained. These are small locally trained byte-level BPEs, not production tokenizers or model-weight training.','',
  '|Vocab|Presegmentation|Exposure|Nominal cap|A pair tokens|E pair tokens|Background English delta|Code delta|Unicode/punctuation delta|Lossless|',
  '|---:|---|---|---:|---:|---:|---:|---:|---:|---|']
 for r in results:
  b=baseline[r['vocab_limit'],r['policy']];ev=r['evaluation']
  delta=lambda key:100*(ev[key]['tokens']/b['evaluation'][key]['tokens']-1)
  lines.append(f"|{r['vocab_limit']}|{r['policy']}|{r['exposure_language']}|{r['nominal_fraction']:.3%}|{ev['paired_ainglish']['tokens']}|{ev['paired_english']['tokens']}|{delta('english'):+.3f}%|{delta('code'):+.3f}%|{delta('punctuation_unicode'):+.3f}%|{r['passed_lossless_gate']}|")
 lines+=['','Positive collateral deltas mean more tokens, not improvement. Achieved A/English teaching byte shares differ: see PLAN.json. Paired evaluations share teaching frames but not lexical records. Full per-string counts and tokenizer hashes are retained. A failed lossless gate invalidates efficiency interpretation for that cell; it is not dropped.']
 with (ROOT/'RESULTS.md').open('x') as f:f.write('\n'.join(lines)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);a=p.parse_args()
 build() if a.action=='build' else run()
