#!/usr/bin/env python3
"""Freeze both local adapter identities into a small public evaluation receipt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from integrity import ROOT, canonical, pretty, sha256_file, validate_artifact, verify_preregistered


def main() -> None:
    target = ROOT / "adapter-receipts.json"
    if target.exists():
        raise SystemExit("REFUSING: adapter-receipts.json already exists")
    public_commit = verify_preregistered()
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    adapters = []
    for group in ("a", "b"):
        directory = Path(plan["adapter_paths"][group])
        manifest_path = directory / "artifact-manifest.json"
        receipt_path = directory / "training-receipt.json"
        if not manifest_path.is_file() or not receipt_path.is_file():
            raise RuntimeError(f"group {group} training output is incomplete")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        validate_artifact(directory, manifest)
        if manifest["group"] != group or receipt["group"] != group or receipt["source_sha256"] != plan["outputs"][f"train-{group}.jsonl"]["sha256"]:
            raise RuntimeError(f"group {group} receipt binding drift")
        adapters.append({
            "group": group, "directory": str(directory),
            "manifest_sha256": sha256_file(manifest_path), "manifest": manifest,
            "training_receipt_sha256": sha256_file(receipt_path), "training_receipt": receipt,
        })
    packet = {
        "schema": "ainglish.crossover-adapter-receipts.v1",
        "public_preregistration_commit": public_commit,
        "adapters": adapters,
        "weights_committed_to_git": False,
        "note": "Exact local adapter files are bound by path, per-file digests, sizes, and aggregate digests; only this receipt is published.",
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target.write_bytes(pretty(packet))
    print(json.dumps({"ok": True, "content_sha256": packet["content_sha256"], "adapters": [{"group": row["group"], "bytes": row["manifest"]["total_bytes"], "digest": row["manifest"]["aggregate_sha256"]} for row in adapters]}, indent=2))


if __name__ == "__main__":
    main()
