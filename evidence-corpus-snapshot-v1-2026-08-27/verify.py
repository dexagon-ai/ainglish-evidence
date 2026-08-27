#!/usr/bin/env python3
"""Verify the frozen evidence bundle without network access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, receipt in manifest["files"].items():
        path = ROOT / name
        if sha(path) != receipt["sha256"] or path.stat().st_size != receipt["bytes"]:
            raise SystemExit(f"REFUSING: {name} does not match MANIFEST.json")
    expected = {}
    for line in (ROOT / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ", 1)
        expected[name] = digest
    for name, digest in expected.items():
        if sha(ROOT / name) != digest:
            raise SystemExit(f"REFUSING: {name} does not match SHA256SUMS")

    index = json.loads((ROOT / "index-pages.json").read_text(encoding="utf-8"))
    index_rows = [row for page in index["pages"] for row in page["measurements"]]
    records = [json.loads(line) for line in (ROOT / "records.jsonl").read_text(
        encoding="utf-8").splitlines() if line]
    if len(index_rows) != manifest["measurement_count"] or len(records) != len(index_rows):
        raise SystemExit("REFUSING: bundle row counts disagree")
    if [row["attempt_id"] for row in index_rows] != [record["index_row"]["attempt_id"] for record in records]:
        raise SystemExit("REFUSING: detail order/identity differs from the index sweep")
    if len({record["index_row"]["attempt_id"] for record in records}) != len(records):
        raise SystemExit("REFUSING: duplicate attempt ids in bundle")
    for record in records:
        row = record["index_row"]
        retrieval = record["manifest_retrieval"]
        if retrieval["kind"] == "immutable_attempt_manifest":
            manifest_jcs = retrieval["manifest_jcs"]
            json.loads(manifest_jcs)
            digest = hashlib.sha256(manifest_jcs.encode("utf-8")).hexdigest()
            if digest != row["manifest_hash"] or retrieval["hash_verified"] is not True:
                raise SystemExit(f"REFUSING: manifest hash mismatch for {row['attempt_id']}")
        elif retrieval["kind"] == "legacy_permalink_fallback":
            detail = json.loads(retrieval["permalink_json"])
            if detail.get("manifest_hash") != row["manifest_hash"] or not isinstance(detail.get("manifest"), dict):
                raise SystemExit(f"REFUSING: invalid legacy manifest fallback for {row['attempt_id']}")
            if retrieval["hash_verified"] is not False:
                raise SystemExit("REFUSING: legacy fallback falsely claims hash verification")
        else:
            raise SystemExit(f"REFUSING: unknown manifest retrieval kind for {row['attempt_id']}")
    print(json.dumps({
        "verified": True,
        "snapshot_max_id": manifest["snapshot_max_id"],
        "measurements": len(records),
        "files": len(expected),
    }))


if __name__ == "__main__":
    main()
