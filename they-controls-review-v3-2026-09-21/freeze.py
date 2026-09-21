"""Generate the review artifacts and digest inventory, without network or inference."""
import hashlib
import json
from pathlib import Path
from controls import build, witnesses

root = Path(__file__).resolve().parent
fixtures = build()
for name, value in [('control-prototypes.json', fixtures), ('shortcut-checks.json', witnesses(fixtures))]:
    (root / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
files = ['controls.py', 'test_controls.py', 'README.md', 'freeze.py',
         'control-prototypes.json', 'shortcut-checks.json']
manifest = {'kind': 'ainglish.control-coverage-review-freeze.v3',
            'reviewed_predecessor_commit': '0ab7d5c6586dc8a85f1007c6cfcce2d8f8f14f75',
            'candidate_sha256': fixtures['candidate_sha256'],
            'review_finding': 'e86a4d4e-139c-4a15-b1d5-fc0dc7a5e3db',
            'file_sha256': {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files},
            'semantic_worlds': 60, 'semantic_question_probes': 72, 'prompt_variants': 216,
            'reader_calls': 0, 'not_a_target_bank': True, 'no_execution_approval': True,
            'full_study_author_scope': 'shelved'}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
