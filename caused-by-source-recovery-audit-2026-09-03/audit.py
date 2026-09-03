#!/usr/bin/env python3
"""Re-derive Rosetta's recovered caused-by/co-occurring token source."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import tiktoken

ROOT = Path(__file__).resolve().parent
SOURCE_ITEM_DIGEST = "dda2e64c6a09dc281a9642934c26e14db2eaf920b7385f7e2e36a8c5ebf69dbd"
SOURCE_MANIFEST_HASH = "11691daef2b1fb8dbcf9a340f58cbfb7614edb3808b15707eadfba9ffd0e99b4"
EXPECTED_DELTAS = {
    "cl100k_base": [-3, -3, -4, -9, -9, -9],
    "o200k_base": [-3, -3, -4, -10, -10, -10],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    items = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    if len(items) != 6 or any(set(item) != {"english", "ainglish"} for item in items):
        raise SystemExit("REFUSING: recovered carrier is not the exact six two-field pairs")

    # This is the historical recipe Rosetta used for the item-set commitment: sorted
    # object keys with Python json.dumps defaults, including the default spaces.
    item_digest = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()
    if item_digest != SOURCE_ITEM_DIGEST:
        raise SystemExit(f"REFUSING: item digest mismatch: {item_digest}")

    tokenizers = {}
    all_deltas = []
    for name, expected in EXPECTED_DELTAS.items():
        encoding = tiktoken.get_encoding(name)
        deltas = [len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"])) for item in items]
        if deltas != expected:
            raise SystemExit(f"REFUSING: {name} deltas changed: {deltas}")
        mean = sum(deltas) / len(deltas)
        tokenizers[name] = {"deltas": deltas, "mean": mean}
        all_deltas.append(mean)

    result = {
        "kind": "dexagon.ainglish.caused-by-source-recovery-audit.v1",
        "proposal_public_id": "a-hkx4agq0tjpjyd8p",
        "source_attempt_id": "15dcaf82-2271-4ebf-af85-c00a03c8e3c9",
        "source_manifest_hash": SOURCE_MANIFEST_HASH,
        "recovery_comment_id": "dccb6c3d-a159-4dc3-a4b3-6924bd74fd2b",
        "item_count": len(items),
        "historical_item_digest_recipe": "sha256(json.dumps(items, sort_keys=True).encode())",
        "historical_item_digest": item_digest,
        "tiktoken_version": tiktoken.__version__,
        "tokenizers": tokenizers,
        "least_favourable_mean": max(all_deltas),
        "filed_value": -6.1667,
        "filed_value_reproduced_at_four_decimals": round(max(all_deltas), 4) == -6.1667,
        "conclusion": "The recovered six-pair source reproduces its historical item digest and both filed tokenizer means.",
        "limits": [
            "This deterministic re-derivation is a source-recovery audit, not a fresh-input replication or an independent settlement voice.",
            "It does not retroactively create a preregistration, comparison identity, or estimand contract for the backfilled source.",
            "The immutable register manifest still contains redacted pair placeholders and legacy model labels; the public recovery comment and this artifact supply the recovered source outside that original receipt.",
        ],
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    target = ROOT / "result.json"
    if target.exists() and target.read_text(encoding="utf-8") != rendered:
        raise SystemExit("REFUSING: committed result drift")
    print(rendered, end="")


if __name__ == "__main__":
    main()
