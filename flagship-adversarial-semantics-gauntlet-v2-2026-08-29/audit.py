#!/usr/bin/env python3
"""Fail closed on structural and semantic-family drift in the frozen gauntlet."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LABELS = {"entailed", "contradicted", "underdetermined"}
FAMILIES = {
    "direct_entailment": "entailed",
    "boundary_overread": "underdetermined",
    "quoted_opposite_distractor": "entailed",
    "dual_record_scope": "entailed",
}


def main() -> None:
    source = json.loads((ROOT / "constructs.json").read_text(encoding="utf-8"))
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    rows = packet["items"]
    prompts = [json.loads(line) for line in (ROOT / "prompts.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    failures = []
    if len(source["constructs"]) != 18 or len(rows) != 180 or len(prompts) != 18:
        failures.append("population counts drifted")
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        failures.append("duplicate item IDs")
    by_rank: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_rank[row["rank"]].append(row)
        if row["expected"] not in LABELS:
            failures.append(f"{row['id']}: invalid expected label")
        if row["family"] in FAMILIES and row["expected"] != FAMILIES[row["family"]]:
            failures.append(f"{row['id']}: fixed-family expected label drift")
        if not all(isinstance(row.get(key), str) and row[key].strip() for key in ("reference", "text", "candidate_conclusion")):
            failures.append(f"{row['id']}: empty semantic field")
        if row["candidate_conclusion"].strip() == row["text"].strip():
            failures.append(f"{row['id']}: candidate simply repeats actual message")
    expected_family_counts = {name: 2 for name in (*FAMILIES, "cross_relation")}
    for rank in range(1, 19):
        subset = by_rank[rank]
        if len(subset) != 10 or Counter(row["family"] for row in subset) != expected_family_counts:
            failures.append(f"rank {rank}: family balance drift")
        if Counter(row["pole"] for row in subset) != {"left": 5, "right": 5}:
            failures.append(f"rank {rank}: pole balance drift")
        prompt = prompts[rank - 1] if rank <= len(prompts) else None
        if prompt is None or prompt["rank"] != rank:
            failures.append(f"rank {rank}: missing ordered prompt")
        elif set(prompt["item_ids"]) != {row["id"] for row in subset}:
            failures.append(f"rank {rank}: prompt/item population mismatch")
        elif hashlib.sha256(prompt["prompt"].encode()).hexdigest() != prompt["prompt_sha256"]:
            failures.append(f"rank {rank}: prompt digest mismatch")
    if plan["planned_cells"] != 540 or plan["planned_calls"] != 54 or plan["downloads"] != 0:
        failures.append("run-plan count or download boundary drift")
    if failures:
        raise SystemExit("REFUSING:\n- " + "\n- ".join(failures))
    print(json.dumps({
        "ok": True,
        "constructs": len(by_rank),
        "items": len(rows),
        "family_counts": Counter(row["family"] for row in rows),
        "expected_label_counts": Counter(row["expected"] for row in rows),
        "cross_relation_labels": Counter(row["expected"] for row in rows if row["family"] == "cross_relation"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
