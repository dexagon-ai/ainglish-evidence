#!/usr/bin/env python3
"""Recompute gauntlet accuracy from raw retained responses."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    output = ROOT / "analysis.json"
    if output.exists():
        raise SystemExit("REFUSING: analysis.json already exists")
    items_doc = json.loads((ROOT / "items.json").read_text())
    items = {row["id"]: row for row in items_doc["items"]}
    calls = [json.loads(line) for line in (ROOT / "responses.jsonl").read_text().splitlines() if line]
    rows = []
    invalid_batches = []
    for call in calls:
        content = (((call.get("response") or {}).get("message") or {}).get("content") or "")
        thinking = (((call.get("response") or {}).get("message") or {}).get("thinking") or "")
        expected_ids = call["item_ids"]
        try:
            parsed = json.loads(content)
            answers = parsed["answers"]
            got_ids = [answer["id"] for answer in answers]
            valid = (
                len(answers) == len(expected_ids)
                and len(set(got_ids)) == len(got_ids)
                and set(got_ids) == set(expected_ids)
                and all(set(answer) == {"id", "choice"} and answer["choice"] in ("A", "B", "C") for answer in answers)
            )
        except Exception:
            answers = []
            valid = False
        if not valid or call.get("error"):
            invalid_batches.append({"reader_id": call["reader_id"], "family": call["family"], "error": call.get("error"), "content": content})
            for item_id in expected_ids:
                item = items[item_id]
                rows.append({**{key: item[key] for key in ("id", "form", "family", "state", "answer")}, "reader_id": call["reader_id"], "parsed": None, "correct": False, "batch_valid": False, "thinking_bytes": len(thinking.encode())})
            continue
        by_id = {answer["id"]: answer["choice"] for answer in answers}
        for item_id in expected_ids:
            item = items[item_id]
            choice = by_id[item_id]
            parsed = item["options"][ord(choice) - 65]
            rows.append({**{key: item[key] for key in ("id", "form", "family", "state", "answer")}, "reader_id": call["reader_id"], "parsed": parsed, "correct": parsed == item["answer"], "batch_valid": True, "thinking_bytes": len(thinking.encode())})
    readers = sorted({row["reader_id"] for row in rows})
    per_reader = {
        reader: {
            "correct": sum(row["correct"] for row in rows if row["reader_id"] == reader),
            "cells": sum(row["reader_id"] == reader for row in rows),
        }
        for reader in readers
    }
    for value in per_reader.values():
        value["accuracy"] = value["correct"] / value["cells"]
    breakdown = defaultdict(lambda: {"correct": 0, "cells": 0})
    for row in rows:
        for axis, value in (("form", row["form"]), ("family", row["family"]), ("state", row["state"])):
            key = f"{axis}:{value}"
            breakdown[key]["correct"] += int(row["correct"])
            breakdown[key]["cells"] += 1
    for value in breakdown.values():
        value["accuracy"] = value["correct"] / value["cells"]
    errors = [row for row in rows if not row["correct"]]
    confusion = Counter((row["answer"], row["parsed"] or "invalid") for row in errors)
    result = {
        "kind": "ainglish.group-scope-uncertainty-boundary-result.v1",
        "items_sha256": items_doc["content_sha256"],
        "responses_sha256": hashlib.sha256((ROOT / "responses.jsonl").read_bytes()).hexdigest(),
        "calls": len(calls),
        "cells": len(rows),
        "correct": sum(row["correct"] for row in rows),
        "accuracy": sum(row["correct"] for row in rows) / len(rows),
        "invalid_batches": invalid_batches,
        "per_reader": per_reader,
        "breakdown": dict(sorted(breakdown.items())),
        "confusion": [{"expected": expected, "parsed": parsed, "count": count} for (expected, parsed), count in sorted(confusion.items())],
        "errors": errors,
        "boundary": "supplied-reference development diagnostic only; never governance evidence or human validation",
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("calls", "cells", "correct", "accuracy", "content_sha256")}, indent=2))


if __name__ == "__main__":
    main()
