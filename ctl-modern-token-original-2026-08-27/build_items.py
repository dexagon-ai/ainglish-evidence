#!/usr/bin/env python3
"""Freeze a modern, form-balanced token carrier for ctl(control) / ctl(none)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "ctl-control-declare-whether-a-null-result-could-have-been-ot-3"

NAMED = [
    ("invoice validator", "found no invalid totals", "altered-checksum"),
    ("backup verifier", "reported no missing blocks", "deleted-block"),
    ("malware scanner", "detected no infected files", "standard-test-virus"),
    ("accessibility audit", "found no unlabeled controls", "unlabeled-button"),
    ("schema checker", "reported no incompatible fields", "removed-required-field"),
    ("latency monitor", "observed no threshold breaches", "injected-delay"),
    ("permission audit", "found no excessive grants", "known-overprivileged-role"),
    ("image pipeline", "reported no corrupt outputs", "truncated-image"),
    ("translation check", "found no missing placeholders", "deleted-placeholder"),
    ("log redactor", "reported no exposed account numbers", "seeded-account-number"),
    ("archive test", "found no unreadable members", "damaged-member"),
    ("rate-limit test", "observed no rejected requests", "forced-quota-breach"),
    ("date parser", "reported no invalid timestamps", "impossible-date"),
    ("link checker", "found no broken destinations", "known-dead-link"),
    ("duplicate detector", "reported no repeated records", "copied-record"),
    ("signature verifier", "found no invalid signatures", "tampered-signature"),
]

NONE = [
    ("dependency audit", "found no vulnerable packages"),
    ("cache consistency check", "reported no stale entries"),
    ("queue monitor", "observed no dropped jobs"),
    ("document converter", "reported no malformed pages"),
    ("sensor check", "found no out-of-range readings"),
    ("billing reconciliation", "reported no mismatched charges"),
    ("routing test", "observed no misdirected messages"),
    ("certificate audit", "found no expired certificates"),
    ("migration verifier", "reported no missing rows"),
    ("compression test", "found no damaged payloads"),
    ("notification check", "observed no undelivered alerts"),
    ("inventory audit", "reported no negative balances"),
    ("encoding validator", "found no invalid byte sequences"),
    ("replication monitor", "reported no divergent replicas"),
    ("timezone test", "found no shifted appointments"),
    ("checksum audit", "reported no altered artifacts"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    rows = []
    for index, (subject, result, control) in enumerate(NAMED, 1):
        statement = f"The {subject} {result}"
        rows.append({
            "item_id": f"named-{index:02d}",
            "form": "ctl(named)",
            "ainglish": f"{statement} ctl({control}).",
            "english": f"{statement}, and the {control} known-positive control was demonstrated live in the same run, so this result was capable of being different.",
        })
    for index, (subject, result) in enumerate(NONE, 1):
        statement = f"The {subject} {result}"
        rows.append({
            "item_id": f"none-{index:02d}",
            "form": "ctl(none)",
            "ainglish": f"{statement} ctl(none).",
            "english": f"{statement}, and I ran no known-positive control in the same run, so I cannot show that this result was capable of being different.",
        })
    if len(rows) != 32 or len({row["item_id"] for row in rows}) != 32:
        raise SystemExit("REFUSING: carrier must contain 32 unique rows")
    if any(row["ainglish"] == row["english"] for row in rows):
        raise SystemExit("REFUSING: collapsed comparison")
    packet = {
        "kind": "dexagon.ainglish.ctl-modern-token-items.v1",
        "proposal_slug": SLUG,
        "forms": ["ctl(named)", "ctl(none)"],
        "mapping": {
            "ctl(named)": "The named known-positive control was demonstrated live in the same run, so the reported result was capable of being different.",
            "ctl(none)": "No known-positive control ran, so the writer cannot show that the reported result was capable of being different.",
        },
        "comparison": "Complete Ainglish statement versus a complete careful-English statement carrying the same control disclosure; silence is excluded",
        "acceptance": "The least-favourable maximum mean token_delta across cl100k_base and o200k_base is <= -10 tokens.",
        "evidentiary_limit": "This deterministic carrier measures price only. It does not measure comprehension, truth, auditability, or adoption, and it is a new original rather than an independent replication.",
        "test_set": rows,
    }
    packet["items_sha256"] = hashlib.sha256(canonical(rows)).hexdigest()
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "token-items.json"
    if target.exists():
        raise SystemExit("REFUSING: token-items.json already exists")
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(rows), "items_sha256": packet["items_sha256"], "content_sha256": packet["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
