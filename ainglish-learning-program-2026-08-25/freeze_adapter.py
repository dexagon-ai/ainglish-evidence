#!/usr/bin/env python3
"""Hash a local adapter directory without copying its large weights into Git."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--base-revision", required=True)
    parser.add_argument("--output", default=str(ROOT / "adapter-artifact-receipt.json"))
    args = parser.parse_args()
    directory = Path(args.adapter).resolve()
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit(f"REFUSING: {output} already exists")
    if not (directory / "training-receipt.json").is_file():
        raise SystemExit("REFUSING: completed training receipt is absent")
    records = []
    aggregate = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise SystemExit(f"REFUSING: adapter artifact contains symlink {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(directory).as_posix()
        file_digest = sha256(path)
        size = path.stat().st_size
        records.append({"path": relative, "bytes": size, "sha256": file_digest})
        aggregate.update(relative.encode() + b"\0" + str(size).encode() + b"\0" + file_digest.encode() + b"\n")
    training = json.loads((directory / "training-receipt.json").read_text(encoding="utf-8"))
    payload = {
        "kind": "dexagon.ainglish.qlora-adapter-artifact.v1",
        "local_path": str(directory),
        "base_model": training["base_model"],
        "base_revision": args.base_revision,
        "mode": training["mode"],
        "source": training["source"],
        "source_sha256": training["source_sha256"],
        "adapter_files": len(records),
        "adapter_bytes": sum(row["bytes"] for row in records),
        "directory_sha256": aggregate.hexdigest(),
        "files": records,
        "training_receipt": training,
        "weights_committed_to_git": False,
        "governance_evidence": False,
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("adapter_files", "adapter_bytes", "directory_sha256")}, indent=2))


if __name__ == "__main__":
    main()
