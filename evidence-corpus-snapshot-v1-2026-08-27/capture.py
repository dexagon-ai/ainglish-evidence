#!/usr/bin/env python3
"""Freeze one cursor-bound public evidence sweep plus every row's immutable attempt manifest."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
BASE = "https://ainglish.org"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_manifest(row: dict) -> dict:
    receipt = (row.get("attempt") or {}).get("manifest")
    if not isinstance(receipt, dict):
        request = urllib.request.Request(
            BASE + row["url"], headers={"User-Agent": "dexagon-evidence-snapshot-v1/1"})
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read()
        text = body.decode("utf-8")
        detail = json.loads(text)
        if detail.get("manifest_hash") != row["manifest_hash"] or not isinstance(detail.get("manifest"), dict):
            raise SystemExit(f"REFUSING: legacy permalink lost manifest for {row['attempt_id']}")
        return {
            "kind": "legacy_permalink_fallback",
            "manifest_jcs": None,
            "permalink_json": text,
            "hash_verified": False,
            "note": "this backfilled legacy attempt has no immutable manifest receipt; the public permalink record is preserved but its parsed manifest cannot be reserialized as the original hash bytes",
        }
    request = urllib.request.Request(
        BASE + receipt["url"], headers={"User-Agent": "dexagon-evidence-snapshot-v1/1"})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read()
    if hashlib.sha256(body).hexdigest() != receipt["sha256"] or len(body) != receipt["bytes"]:
        raise SystemExit(f"REFUSING: attempt manifest bytes differ for {row['attempt_id']}")
    text = body.decode("utf-8")
    json.loads(text)
    return {
        "kind": "immutable_attempt_manifest",
        "manifest_jcs": text,
        "permalink_json": None,
        "hash_verified": True,
        "note": None,
    }


def main() -> None:
    outputs = [ROOT / name for name in (
        "index-pages.json", "records.jsonl", "MANIFEST.json", "SHA256SUMS",
    )]
    if any(path.exists() for path in outputs):
        raise SystemExit("REFUSING: snapshot outputs already exist")
    client = AinglishClient(base_url=BASE, user_agent="dexagon-evidence-snapshot-v1/1")
    if not hasattr(client, "measurement_pages"):
        raise SystemExit("REFUSING: this snapshot requires SDK measurement_pages() cursor validation")

    pages = list(client.measurement_pages(page_size=100))
    rows = [row for page in pages for row in page["measurements"]]
    if not pages or not rows:
        raise SystemExit("REFUSING: live evidence sweep returned no rows")
    snapshot_id = pages[0]["sweep"]["snapshot_max_id"]
    if any(page["sweep"]["snapshot_max_id"] != snapshot_id for page in pages):
        raise SystemExit("REFUSING: evidence cursor chain changed snapshot")
    attempts = [row["attempt_id"] for row in rows]
    if len(attempts) != len(set(attempts)):
        raise SystemExit("REFUSING: evidence sweep repeated an attempt id")

    records = []
    for number, row in enumerate(rows, 1):
        manifest = exact_manifest(row)
        manifest_jcs = manifest["manifest_jcs"]
        if manifest_jcs is not None and hashlib.sha256(manifest_jcs.encode("utf-8")).hexdigest() != row["manifest_hash"]:
            raise SystemExit(f"REFUSING: attempt manifest {number} does not match manifest_hash")
        records.append({"index_row": row, "manifest_retrieval": manifest})
        if number % 50 == 0:
            print(f"resolved {number}/{len(rows)} attempt manifests", flush=True)

    hashes = {}
    for row in rows:
        hashes.setdefault(row["manifest_hash"], []).append(row)
    collisions = []
    for manifest_hash, matches in hashes.items():
        if len(matches) < 2:
            continue
        detail = client.measurement(manifest_hash)
        collisions.append({
            "manifest_hash": manifest_hash,
            "attempt_ids": [row["attempt_id"] for row in matches],
            "permalink_resolves_attempt_id": detail.get("attempt_id"),
            "note": "manifest-hash addressing cannot distinguish these historical same-manifest rows; index_row + attempt manifest preserves both",
        })

    captured_at = datetime.now(timezone.utc).isoformat()
    page_document = {
        "kind": "dexagon.ainglish.evidence-index-sweep.v1",
        "captured_at": captured_at,
        "source": f"{BASE}/api/v1/measurements?limit=100",
        "snapshot_max_id": snapshot_id,
        "page_count": len(pages),
        "row_count": len(rows),
        "pages": pages,
    }
    (ROOT / "index-pages.json").write_text(
        json.dumps(page_document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "records.jsonl").write_text(
        "".join(canonical(record).decode() + "\n" for record in records), encoding="utf-8")

    metric_counts = {}
    state_counts = {}
    for row in rows:
        metric_counts[row["metric"]] = metric_counts.get(row["metric"], 0) + 1
        state = row.get("evidence_state", "unknown")
        state_counts[state] = state_counts.get(state, 0) + 1
    retrieval_counts = {}
    for record in records:
        kind = record["manifest_retrieval"]["kind"]
        retrieval_counts[kind] = retrieval_counts.get(kind, 0) + 1
    data_files = {
        name: {"sha256": sha(ROOT / name), "bytes": (ROOT / name).stat().st_size}
        for name in ("index-pages.json", "records.jsonl")
    }
    manifest = {
        "kind": "dexagon.ainglish.evidence-corpus-snapshot.v1",
        "captured_at": captured_at,
        "source_base": BASE,
        "source_endpoint": "/api/v1/measurements",
        "source_sdk_surface": "AinglishClient.measurement_pages; exact bytes from each attempt manifest URL",
        "snapshot_max_id": snapshot_id,
        "page_size": 100,
        "page_count": len(pages),
        "measurement_count": len(rows),
        "first_manifest_hash": rows[0]["manifest_hash"],
        "last_manifest_hash": rows[-1]["manifest_hash"],
        "metric_counts": dict(sorted(metric_counts.items())),
        "evidence_state_counts": dict(sorted(state_counts.items())),
        "manifest_retrieval_counts": dict(sorted(retrieval_counts.items())),
        "manifest_hash_collisions": collisions,
        "files": data_files,
        "scope": {
            "membership": "max-id snapshot and cursor chain from the public evidence index",
            "detail_records": "each complete index row paired with its immutable attempt manifest",
            "mutable_metadata_caveat": "the cursor freezes membership, not later evidence moderation or voiding; this bundle preserves the bytes observed at captured_at",
            "permalink_collision_caveat": "historical same-manifest reproductions can share a manifest hash, so one hash permalink cannot identify both rows; the attempt id is the row identity in this bundle",
        },
        "model_calls": 0,
        "model_downloads": 0,
        "governance_writes": 0,
    }
    manifest["content_sha256"] = hashlib.sha256(canonical(manifest)).hexdigest()
    (ROOT / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    checks = [(sha(ROOT / name), name) for name in (
        "MANIFEST.json", "index-pages.json", "records.jsonl",
    )]
    (ROOT / "SHA256SUMS").write_text(
        "".join(f"{digest}  {name}\n" for digest, name in checks), encoding="ascii")
    print(json.dumps({
        "snapshot_max_id": snapshot_id,
        "pages": len(pages),
        "measurements": len(rows),
        "manifest_sha256": sha(ROOT / "MANIFEST.json"),
    }, indent=2))


if __name__ == "__main__":
    main()
