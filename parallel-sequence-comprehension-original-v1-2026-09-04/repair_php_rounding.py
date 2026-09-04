#!/usr/bin/env python3
"""Repair only Python-vs-PHP tie rounding in a retained stratified panel request.

The immutable scored-cell journal remains byte-identical. PHP's round() uses half-away-from-zero,
whereas Python's built-in round() uses ties-to-even. The register replays with PHP, so derive the
two arm accuracies from exact integer counts using ROUND_HALF_UP and rebuild the declared point.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "runspec.attempt-7137bb19-9869-486e-bb5c-b1b4f5d42b93.measurement.json"
OUTPUT = ROOT / "runspec.attempt-7137bb19-9869-486e-bb5c-b1b4f5d42b93.measurement.php-rounding.json"
Q4 = Decimal("0.0001")


def q4(value: Decimal) -> Decimal:
    return value.quantize(Q4, rounding=ROUND_HALF_UP)


def main() -> None:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    provenance = payload["interval_provenance"]
    stratum_by_item = {row["id"]: row["stratum"] for row in provenance["items"]}
    counts = defaultdict(lambda: defaultdict(lambda: {"correct": 0, "live": 0}))
    for cell in provenance["cells"]:
        if not isinstance(cell["correct"], bool):
            continue
        bucket = counts[stratum_by_item[cell["item_id"]]][cell["arm"]]
        bucket["live"] += 1
        bucket["correct"] += int(cell["correct"])

    rows = []
    for contract in payload["manifest"]["settlement_strata"]:
        ident = contract["id"]
        arms = {}
        for arm in ("english", "ainglish"):
            bucket = counts[ident][arm]
            if bucket["live"] == 0:
                raise SystemExit(f"no live {arm} cell in {ident}")
            arms[arm] = q4(Decimal(bucket["correct"]) / Decimal(bucket["live"]))
        value = q4(Decimal(100) * (arms["ainglish"] - arms["english"]))
        old = next(row for row in payload["stratum_results"] if row["id"] == ident)
        rows.append({
            "id": ident,
            "value": float(value),
            "arms": {
                "english": float(arms["english"]),
                "ainglish": float(arms["ainglish"]),
                "chance": old["arms"]["chance"],
            },
        })

    weight_sum = sum(Decimal(str(row["weight"])) for row in payload["manifest"]["settlement_strata"])
    by_id = {row["id"]: row for row in rows}
    top_value = Decimal(0)
    top_arms = {"english": Decimal(0), "ainglish": Decimal(0)}
    for contract in payload["manifest"]["settlement_strata"]:
        share = Decimal(str(contract["weight"])) / weight_sum
        row = by_id[contract["id"]]
        top_value += share * Decimal(str(row["value"]))
        for arm in top_arms:
            top_arms[arm] += share * Decimal(str(row["arms"][arm]))

    payload["stratum_results"] = rows
    payload["value"] = float(q4(top_value))
    payload["arms"]["english"] = float(q4(top_arms["english"]))
    payload["arms"]["ainglish"] = float(q4(top_arms["ainglish"]))
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT.chmod(0o600)
    print(json.dumps({
        "source_value": json.loads(SOURCE.read_text(encoding="utf-8"))["value"],
        "corrected_value": payload["value"],
        "stratum_results": rows,
        "interval_provenance_sha256": provenance["content_sha256"],
        "cell_count": len(provenance["cells"]),
    }, indent=2))


if __name__ == "__main__":
    main()
