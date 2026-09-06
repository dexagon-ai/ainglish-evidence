"""Teaching-only export and literal marker audit; never changes frozen experiments."""
from collections import Counter, defaultdict
import hashlib
import json
import re
import subprocess
import zipfile
from audit import ROOT, audit, rows, verify

MARKER = re.compile(r'\b[a-z][a-z0-9_]*(?:-[a-z0-9_]+)+\b|\b[a-z][a-z0-9_]*(?=\(|:)')
SOURCE_COMMIT = '73df9ce'
ALLOWED = {'curriculum.jsonl', 'train-ainglish.jsonl', 'train-english.jsonl', 'source-constructs.json'}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def main():
    audit(); verify(public=True)
    train = rows('curriculum.jsonl')
    seen = set()
    for row in train:
        key = json.dumps({k: row[k] for k in ('ainglish', 'english', 'question', 'options', 'answer')}, sort_keys=True)
        assert key not in seen, 'Exact duplicate teaching case; do not claim 336 distinct pairs'
        seen.add(key)
    source = json.loads((ROOT/'source-constructs.json').read_text())
    # This published sweep is frozen rather than presenting a stale live status as current.
    snapshot = ROOT.parent/'progression-lab-2026-09-06/snapshot/proposals.json'
    proposals = json.loads(snapshot.read_text())
    index = defaultdict(list)
    for p in proposals:
        for marker in set(MARKER.findall(p['form'])):
            index[marker].append({k: p[k] for k in ('public_id', 'slug', 'stage', 'form')})
    taught = set()
    findings = []
    for family, entry in source['entries'].items():
        own_markers = set(MARKER.findall(entry['form']))
        taught.update(own_markers)
        for marker in sorted(set(MARKER.findall(entry['english_mapping']))):
            if marker in own_markers:
                continue  # The current definition is not a dependency on its own older version.
            matches = [p for p in index.get(marker, []) if p['slug'] != entry['slug']]
            if matches:
                findings.append({'source_family': family, 'marker': marker,
                    'has_ratified_target_in_snapshot': any(p['stage'] == 'ratified' for p in matches),
                    'targets': matches})
    task_text = '\n'.join(message['content'] for language in ('ainglish', 'english')
                          for row in rows('train-' + language + '.jsonl') for message in row['messages'])
    # Other registered-marker strings are reported, not assumed to be language use.
    extras = []
    for marker in sorted(set(MARKER.findall(task_text)) - taught):
        if marker in index:
            extras.append({'marker': marker, 'targets': index[marker]})
    report = {'kind': 'ainglish.teaching-surface-audit.v1', 'snapshot_at': '2026-09-06',
        'proposal_snapshot_sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        'snapshot_records': len(proposals), 'training_cases': len(train),
        'authored_frames': len({r['frame'] for r in train}), 'families': dict(Counter(r['family'] for r in train)),
        'taught_markers': sorted(taught), 'definition_mentions': findings,
        'other_registered_marker_spellings_in_training_messages': extras,
        'boundary': 'Literal spelling audit, not a semantic parser or conformance certificate. Referenced tags inside source definitions are not thereby ratified. Complete definitions are preserved as reference metadata and are not appended to these training messages. Ordinary English remains legal.'}
    assert not extras, extras
    files = {}
    for name in ALLOWED:
        raw = subprocess.check_output(['git', 'show', f'{SOURCE_COMMIT}:{ROOT.name}/{name}'], cwd=ROOT.parent)
        assert raw == (ROOT/name).read_bytes(), name
        files[name] = raw
    files['MARKER-AUDIT.json'] = encode(report)
    files['README.txt'] = b'''Synthetic teaching supplement, not an official language release.
CC0-1.0. Train-only: 336 distinct paired cases across six ratified families,
42 authored task frames and eight lexical domains. These are not 336 independent
semantic structures or human-reviewed examples. Matched English exposure remains
available. The experimental adapters trained on these exact, unchanged rows.

Allowed inputs are explicitly enumerated. No holdout, composition task, controls,
answer-bearing evaluation file, model output, adapter or research result is inside
this archive. Keep evaluations separate; exact disjointness does not rule out
concept/template overlap. The new holdout shares known semantic principles.

The source definitions are preserved in source-constructs.json as provenance and
reference, not automatically appended to training examples. req:/will: and other
tags cited by those definitions do not become ratified teaching vocabulary.
Consult MARKER-AUDIT.json for the dated spelling audit and its limitations.

Publication makes reuse possible; it is not evidence of downstream adoption,
training, tokenizer changes or successful transfer. Do not report the earlier
pilot or this export as an official new public-domain language release.
'''
    manifest = {'kind': 'ainglish.non-normative-teaching-supplement.v1', 'license': 'CC0-1.0',
        'official_release': False, 'synthetic': True, 'split': 'train', 'source': 'ainglish-core-v3',
        'source_training_commit': subprocess.check_output(['git', 'rev-parse', SOURCE_COMMIT], cwd=ROOT.parent, text=True).strip(),
        'paired_cases': len(train), 'authored_frames': len({r['frame'] for r in train}),
        'experiment_training_unchanged': True,
        'files': {name: {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)} for name, raw in sorted(files.items())}}
    files['MANIFEST.json'] = encode(manifest)
    target = ROOT/'teaching-supplement-336.zip'
    with zipfile.ZipFile(target, 'x') as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 9, 6, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    with (ROOT/'TEACHING-MARKER-AUDIT.json').open('xb') as stream: stream.write(encode(report))
    print(json.dumps({'path': target.name, 'paired_cases': len(train), 'bytes': target.stat().st_size,
        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'additional_registered_spellings_in_training': extras,
        'unratified_definition_mentions': [r for r in findings if not r['has_ratified_target_in_snapshot']]}))


if __name__ == '__main__': main()
