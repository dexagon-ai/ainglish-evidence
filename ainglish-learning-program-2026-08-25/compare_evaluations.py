#!/usr/bin/env python3
"""Compare frozen base and adapter evaluations on identical splits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f"REFUSING: {output} already exists")
    base = json.loads(Path(args.base).read_text(encoding="utf-8"))
    adapter = json.loads(Path(args.adapter).read_text(encoding="utf-8"))
    if base.get("kind") != "dexagon.ainglish.adapter-evaluation.v1" or adapter.get("kind") != base.get("kind"):
        raise SystemExit("REFUSING: inputs are not adapter-evaluation receipts")
    if base.get("adapter") is not None or adapter.get("adapter") is None:
        raise SystemExit("REFUSING: expected one base and one adapter evaluation")
    if base.get("split_digests") != adapter.get("split_digests"):
        raise SystemExit("REFUSING: split digests differ")
    if base.get("base_model") != adapter.get("base_model"):
        raise SystemExit("REFUSING: base model names differ")
    base_metrics = {(row["split"], row["task"]): row for row in base["metrics"]}
    adapter_metrics = {(row["split"], row["task"]): row for row in adapter["metrics"]}
    if base_metrics.keys() != adapter_metrics.keys():
        raise SystemExit("REFUSING: metric cells differ")
    cells = []
    for key in sorted(base_metrics):
        left, right = base_metrics[key], adapter_metrics[key]
        row = {
            "split": key[0],
            "task": key[1],
            "rows": left["rows"],
            "base_mean_token_f1": left["mean_token_f1"],
            "adapter_mean_token_f1": right["mean_token_f1"],
            "mean_token_f1_delta": round(right["mean_token_f1"] - left["mean_token_f1"], 6),
        }
        if "canonical_form_accuracy" in left or "canonical_form_accuracy" in right:
            if "canonical_form_accuracy" not in left or "canonical_form_accuracy" not in right:
                raise SystemExit(f"REFUSING: form-accuracy cell mismatch for {key}")
            row.update(
                {
                    "base_canonical_form_accuracy": left["canonical_form_accuracy"],
                    "adapter_canonical_form_accuracy": right["canonical_form_accuracy"],
                    "canonical_form_accuracy_delta": round(
                        right["canonical_form_accuracy"] - left["canonical_form_accuracy"], 6
                    ),
                }
            )
        cells.append(row)
    payload = {
        "kind": "dexagon.ainglish.adapter-comparison.v1",
        "base_model": base["base_model"],
        "adapter": adapter["adapter"],
        "base_evaluation_sha256": base["content_sha256"],
        "adapter_evaluation_sha256": adapter["content_sha256"],
        "split_digests": base["split_digests"],
        "cells": cells,
        "governance_evidence": False,
        "interpretation": (
            "Development benchmark only. Training on register material contaminates cold "
            "comprehension and cannot ratify or independently confirm a construct."
        ),
    }
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cells": cells, "content_sha256": payload["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
