"""Regenerate CPU fixtures and their public file manifest, without inference."""
import hashlib
import json
from pathlib import Path
import runpy

root=Path(__file__).resolve().parent
runpy.run_path(str(root/'controls.py'),run_name='__main__')
files=['controls.py','test_controls.py','README.md','control-prototypes.json',
       'shortcut-checks.json','old-question-blind-reproduction.json']
manifest={'kind':'ainglish.control-coverage-review-freeze.v2',
    'reviewed_predecessor_commit':'4e68a36c8c4009f26c4f01d624c39143c9d33c53',
    'candidate_sha256':'fdf67591234ec63df19d29cfbbfe44d17e3685a189cb42c7782e7f41b36cc462',
    'review_findings':['8dbb4d4a-a547-4d7d-8262-8908ac91817d','f087e84a-ee78-4db4-b2ef-da4b72cde4cb'],
    'file_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files},
    'semantic_worlds':55,'semantic_question_probes':67,'prompt_variants':201,
    'reader_calls':0,'not_a_target_bank':True,'no_execution_approval':True}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
