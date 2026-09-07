"""Reload published artifacts and independently recount; never train a tokenizer."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parent
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read(path): return json.loads(path.read_text())
def main():
    spec = importlib.util.spec_from_file_location('frozen_design', ROOT / 'study.py')
    study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
    study.verify()
    plan, result, split = [read(ROOT / n) for n in ['PLAN.json', 'RESULTS.json', 'split.json']]
    train, test = study.corpus_records()
    for label, records in [('train', train), ('test', test)]:
        assert split[label] == [{'id': i, 'bytes': len(t.encode()), 'sha256': sha(t.encode())} for i,t in records]
    assert not {i for i,_ in train} & {i for i,_ in test}
    evaluation = read(ROOT / 'evaluation.json')
    heldouts = {'english': [t for _,t in test], 'code': evaluation['code'],
        'punctuation_unicode': evaluation['punctuation_unicode'],
        'paired_ainglish': [r['ainglish'] for r in evaluation['ainglish_pairs']],
        'paired_english': [r['english'] for r in evaluation['ainglish_pairs']]}
    teaching_root = ROOT.parent / 'contextual-teaching-2026-09-07'
    teaching = [json.loads(line) for line in (teaching_root / 'curriculum.jsonl').read_text().splitlines()]
    assert len(teaching) == len({r['id'] for r in teaching}) == 576
    assert len({r['frame'] for r in teaching}) == 48 and len({r['context'] for r in teaching}) == 12
    forbidden = {r[k] for r in teaching for k in ['ainglish', 'english']}
    assert not forbidden & {r[k] for r in evaluation['ainglish_pairs'] for k in ['ainglish', 'english']}
    manifest = read(teaching_root / 'MANIFEST.json')
    with zipfile.ZipFile(teaching_root / 'teaching-supplement-576.zip') as z:
        assert set(z.namelist()) == set(manifest['files']) | {'MANIFEST.json'}
        assert z.read('MANIFEST.json') == (teaching_root / 'MANIFEST.json').read_bytes()
        for name, pin in manifest['files'].items():
            raw = (teaching_root / name).read_bytes()
            assert sha(raw) == pin['sha256'] and len(raw) == pin['bytes'] and z.read(name) == raw
    expected = {(v, p, lang, mix) for v in plan['vocabulary_sizes'] for p in plan['presegmentation']
        for lang, mix in [('baseline', 0)] + [(lang, mix) for mix in [.001, .01, .05] for lang in ['ainglish', 'english']]}
    actual = {(r['vocab_limit'], r['policy'], r['exposure_language'], r['nominal_fraction']) for r in result['cells']}
    assert actual == expected and len(result['cells']) == 28
    total_strings = 0
    for row in result['cells']:
        path = ROOT / 'execution' / (row['id'] + '.json')
        assert sha(path.read_bytes()) == row['tokenizer_sha256']
        assert read(ROOT / 'execution' / (row['id'] + '.result.json')) == row
        tokenizer = Tokenizer.from_file(str(path))
        assert tokenizer.get_vocab_size() == row['actual_vocab']
        for label, texts in heldouts.items():
            encoded = [tokenizer.encode(t).ids for t in texts]
            counts = [len(ids) for ids in encoded]
            assert counts == row['evaluation'][label]['per_string']
            assert sum(counts) == row['evaluation'][label]['tokens']
            assert all(tokenizer.decode(ids) == text for text, ids in zip(texts, encoded))
            total_strings += len(texts)
        print('Verified', row['id'], flush=True)
    audit = {'kind': 'ainglish.published-tokenizer-artifact-audit.v1', 'cells': 28,
        'reencoded_heldout_strings': total_strings, 'exact_per_string_counts_match': True,
        'all_byte_roundtrips_match': True, 'whole_document_splits_reverified': True,
        'teaching_zip_bytes_and_hashes_match': True, 'teaching_pairs': 576,
        'teaching_frames': 48, 'teaching_contexts': 12, 'training_or_inference_calls': 0,
        'limits': 'Same-author reproducibility check, not independent confirmation or new efficacy evidence.'}
    with (ROOT / 'ARTIFACT-AUDIT.json').open('x') as out:
        json.dump(audit, out, indent=2); out.write('\n')
    print(json.dumps(audit, indent=2))

if __name__ == '__main__':
    main()
