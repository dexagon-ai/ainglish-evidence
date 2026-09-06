"""Refresh only an unpublished, unspent draft's code pins after preparation review."""
import json
from pathlib import Path
import subprocess
from audit_research import audit,digest
ROOT=Path(__file__).resolve().parent
assert not (ROOT/'research-results').exists()
assert not (ROOT/'adapter-receipts.json').exists()
assert not subprocess.check_output(['git','ls-files',f'{ROOT.name}/FROZEN.json'],cwd=ROOT.parent).strip(), 'Published/tracked freeze must not be rewritten'
assert audit()['ok']
path=ROOT/'FROZEN.json'
pins=json.loads(path.read_text())
with path.open('w') as handle:json.dump({name:digest(ROOT/name) for name in pins},handle,indent=2);handle.write('\n')
