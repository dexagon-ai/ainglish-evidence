"""Offline verification of the unchanged sanction review packet; no inference."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
raw = (root / 'items.json').read_bytes()
items = json.loads(raw)
file_hash = hashlib.sha256(raw).hexdigest()
canonical_hash = hashlib.sha256(json.dumps(
    items, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
    allow_nan=False).encode('utf-8')).hexdigest()
assert file_hash == 'a63592a0084929fbae3bd13b45120ee375b54357ff2576bfc00a538d62ee3d86'
assert canonical_hash == '09becce008fb39df0bf0ea7cd8b6c47453ad2b4ce5b053e2adf6f4c381227667'
print(json.dumps({'file_sha256': file_hash, 'items_sha256': canonical_hash,
                  'items': len(items), 'semantic_review': 'not performed by this verifier'}, indent=2))
