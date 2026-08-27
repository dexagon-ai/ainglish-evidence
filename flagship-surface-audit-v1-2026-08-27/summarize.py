#!/usr/bin/env python3
"""Verify and summarize the exploratory surface audit."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    packet_sealed = dict(packet); packet_hash = packet_sealed.pop("content_sha256")
    if hashlib.sha256(canonical(packet_sealed)).hexdigest() != packet_hash:
        raise SystemExit("item packet drift")
    result = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
    result_sealed = dict(result); result_hash = result_sealed.pop("content_sha256")
    if hashlib.sha256(canonical(result_sealed)).hexdigest() != result_hash:
        raise SystemExit("result drift")
    ledger = [json.loads(line) for line in (ROOT / "responses.jsonl").read_text(encoding="utf-8").splitlines()]
    if ledger != result["rows"]:
        raise SystemExit("append-only ledger/result mismatch")
    if len(ledger) != len(packet["items"]) * len(packet["models"]):
        raise SystemExit("incomplete cell matrix")

    cells = defaultdict(lambda: {"correct": 0, "total": 0, "errors": 0})
    constructs = defaultdict(lambda: defaultdict(lambda: {"correct": 0, "total": 0}))
    for row in ledger:
        cell = cells[(row["model"], row["exposure"])]
        cell["total"] += 1; cell["correct"] += int(row["correct"]); cell["errors"] += int(bool(row["error"]))
        bucket = constructs[row["slug"]][row["exposure"]]
        bucket["total"] += 1; bucket["correct"] += int(row["correct"])

    summary = {
        "kind": "dexagon.ainglish.flagship-surface-audit-summary.v1",
        "items_sha256": packet_hash,
        "results_sha256": result_hash,
        "cells": [
            {"model": model, "exposure": exposure, **counts, "accuracy": counts["correct"] / counts["total"]}
            for (model, exposure), counts in sorted(cells.items())
        ],
        "constructs": [
            {"slug": slug, **{exposure: {**counts, "accuracy": counts["correct"] / counts["total"]} for exposure, counts in sorted(exposures.items())}}
            for slug, exposures in sorted(constructs.items())
        ],
        "claim_boundary": packet["claim_boundary"],
    }
    summary["content_sha256"] = hashlib.sha256(canonical(summary)).hexdigest()
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"verified": True, "rows": len(ledger), "cells": summary["cells"], "sha256": summary["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
