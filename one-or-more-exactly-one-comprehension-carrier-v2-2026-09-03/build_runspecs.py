#!/usr/bin/env python3
"""Bind the frozen carrier and qualified readers into four separate runspecs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
QUALIFICATION = REPO / "remote-reader-qualification-wave-v2-2026-09-03"
SLUG = "one-or-more-role-exactly-one-role-does-a-reviewer-require-at"
SDK_VERSION = "0.2.51"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def result(name):
    document = json.loads((QUALIFICATION / f"{name}.result.json").read_text(encoding="utf-8"))
    if document["status"] != "passed" or not document["receipt"]["result"]["passed"]:
        raise SystemExit(f"REFUSING: qualification {name} did not pass")
    return document["receipt"]


def reader(screen_name):
    screen = json.loads((QUALIFICATION / f"{screen_name}.screen.json").read_text(encoding="utf-8"))
    return screen["reader"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items-commit", required=True)
    parser.add_argument("--sdk-commit", required=True)
    args = parser.parse_args()
    for label, value in (("items", args.items_commit), ("SDK", args.sdk_commit)):
        if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
            raise SystemExit(f"{label} commit must be a full lowercase Git SHA")

    frozen = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    receipts = [result("local-mistral-small32-24b"), result("local-gemma3-12b")]
    panel = [reader("local-mistral-small32-24b"), reader("local-gemma3-12b")]
    roster = [receipt["roster_id"] for receipt in receipts]
    index = {
        "kind": "ainglish.role-cardinality-comprehension-runspec-index.v2",
        "items_commit": args.items_commit,
        "sdk_commit": args.sdk_commit,
        "sdk_version": SDK_VERSION,
        "campaigns": {},
    }
    for ordinal, (name, meta) in enumerate(frozen["campaigns"].items()):
        form, comparison = name.rsplit("-vs-", 1)
        careful = comparison == "careful"
        comparator = (
            f"the shortest complete careful-English expansion of {form}(role), explicitly "
            "counting distinct qualifying principals"
            if careful else
            "the same bare indefinite-singular role instruction, whose at-least-one versus "
            "exactly-one force is not stipulated"
        )
        estimand = (
            f"Original form-separated comprehension_accuracy_delta for {form}(role) versus "
            f"{comparison} English over 120 frozen role/action/cardinality items. The scalar is "
            "reported with absolute arms; the public cell sidecar retains every role, voice, "
            "observed-count, two-principal, seam, alias, and non-claim stratum. This campaign "
            "must not be pooled with the other form or comparator class."
        )
        spec = {
            "construct": f"{form}(role) role-cardinality comprehension original versus {comparison}",
            "slug": SLUG,
            "metric": "comprehension_accuracy_delta",
            "seed": 2026090307 + ordinal,
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": 1,
            "panel": panel,
            "models": roster,
            "reader_qualifications": receipts,
            "comparator": {"kind": "complete-careful-english-v1" if careful else "baseline-english-v1", "description": comparator + "."},
            "items_url": (
                "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                f"{args.items_commit}/one-or-more-exactly-one-comprehension-carrier-v2-2026-09-03/{meta['file']}"
            ),
            "items_sha256": meta["items_sha256"],
            "concurrency": {
                "max_in_flight": 2,
                "per_reader_max_in_flight": {reader["name"]: 1 for reader in panel},
            },
            "attempt": {
                "proposal_revision": SLUG,
                "estimand": estimand,
                "admissibility_gates": [
                    f"the 120+8 answer-bearing carrier is frozen at public commit {args.items_commit} with canonical item digest {meta['items_sha256']}",
                    f"the exact receipt-preserving panel harness is public at ai-nglish/ainglish commit {args.sdk_commit}",
                    "Mistral Small 3.2 24B and Gemma 3 12B passed the same 16-control target-independent screen before any target reader call",
                    "the two attached reader receipts are unexpired and match every declared roster identity",
                    "all 120 scientific rows remain byte-for-byte identical to the 2026-08-26 v1 freeze; only invalid byte-identical calibration arms changed",
                    "all eight target-independent calibration controls must be live in both arms for each reader and recover a planted-arm gap of at least 0.5",
                    "zero response-bound truncations and a passing cell-yield guard are required",
                    "absolute arms, interval, resolution, per-reader values, agreement, all normalized cells, and adverse, null or supportive outcomes are retained without retry",
                    "the declared panel_neff is conservatively one; distinct model-family names are not treated as proof of independent errors",
                ],
                "planned_sample": {
                    "form": form,
                    "comparison": comparison,
                    "scientific_items": 120,
                    "calibration_items": 8,
                    "readers": 2,
                    "reader_lineages": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                    "panel_members": 2,
                    "panel_neff": 1,
                    "real_cells": 240,
                    "calibration_cells": 32,
                    "sdk_version": SDK_VERSION,
                },
            },
        }
        path = ROOT / f"runspec-{name}.json"
        encoded = json.dumps(spec, indent=2, ensure_ascii=False).encode() + b"\n"
        path.write_bytes(encoded)
        index["campaigns"][name] = {
            "runspec": path.name,
            "runspec_sha256": hashlib.sha256(encoded).hexdigest(),
            "receipt_stem": f"role-cardinality-{name}",
        }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "runspec-index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
