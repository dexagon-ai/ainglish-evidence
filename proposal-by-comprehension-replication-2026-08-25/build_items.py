#!/usr/bin/env python3
"""Build 48 fresh paired proposal-by scenarios and eight planted calibrations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "items.json"
OPTIONS = [
    "offered / no / no",
    "selected / yes / no",
    "invalid source / no / no",
    "selected / yes / yes",
    "cannot tell / cannot tell / cannot tell",
]
QUESTION = (
    "Choose the three-part profile that follows from the message. Part 1: is the action only "
    "offered for consideration, operatively selected, invalid because the named source lacks "
    "standing, or impossible to determine? Part 2: may the record state that an existing choice "
    "has been made? Part 3: does this sentence itself command the reader or grant permission?"
)
DOMAINS = (
    ("release", "stage release 12 in the west region"),
    ("security", "quarantine the legacy credential set"),
    ("operations", "drain the delayed-job queue tonight"),
    ("research", "repeat the calibration on a held-out sample"),
    ("finance", "reconcile the disputed supplier invoice"),
    ("moderation", "reopen the archived appeal for review"),
    ("procurement", "trial the second hardware quotation"),
    ("scheduling", "hold the retrospective on Thursday"),
    ("documentation", "publish the migration appendix separately"),
    ("data", "retain the raw import table for another week"),
    ("support", "send the customer a diagnostic bundle"),
    ("governance", "place the exception on the next ballot"),
)
SOURCES = (
    "delivery coordinator", "security analyst", "queue operator", "research associate",
    "accounts reviewer", "appeal clerk", "purchasing assistant", "calendar steward",
    "documentation editor", "data custodian", "support engineer", "agenda secretary",
)
STYLES = (
    ("Could we {action}?", "neutral_question"),
    ("I suggest that we {action}.", "explicit_suggestion"),
    ("What if we {action}?", "what_if"),
    ("Perhaps we should {action}.", "tentative_should"),
)
PREFACES = (
    "A different earlier course remains operative.",
    "Several participants spoke in favour, but no authorized selection followed.",
    "The named writer has a senior title, but this message records no decision event.",
    "The option has not been approved or rejected.",
)


def rotate(values: list[str], offset: int) -> list[str]:
    offset %= len(values)
    return values[offset:] + values[:offset]


def build() -> dict:
    items = []
    for index in range(8):
        action = DOMAINS[index][1]
        items.append({
            "id": f"cal-proposal-fresh-{index + 1:02d}", "calibration": True,
            "english": (
                f"A status note mentions whether to {action}, but does not say whether the action "
                "was offered, selected, invalid, or directive."
            ),
            "ainglish": (
                f"The action to {action} was offered for consideration only. No operative choice "
                "was made, and this sentence neither commands nor permits the reader."
            ),
            "question": QUESTION, "options": rotate(OPTIONS, index),
            "answer": "offered / no / no", "strata": {"control": "planted_effect"},
        })
    for index in range(48):
        domain, action = DOMAINS[index % len(DOMAINS)]
        source = SOURCES[index % len(SOURCES)]
        style, style_name = STYLES[index // len(DOMAINS)]
        preface = PREFACES[(index // 3) % len(PREFACES)]
        quoted = style.format(action=action)
        items.append({
            "id": f"proposal-fresh-{index + 1:03d}",
            "english": f"{preface} The {source} writes, “{quoted}”",
            "ainglish": f"{preface} proposal-by({source}): {action}.",
            "question": QUESTION, "options": rotate(OPTIONS, index),
            "answer": "offered / no / no",
            "strata": {"domain": domain, "style": style_name, "preface": PREFACES.index(preface)},
        })
    canonical = json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {
        "kind": "ainglish.panel.items.v1", "proposal": "proposal-by-p-decision-by-a-say-whether-an-option-is-offered",
        "form": "proposal", "baseline": "short", "real_items": 48,
        "calibration_items": 8, "sha256": hashlib.sha256(canonical).hexdigest(), "items": items,
    }


def main() -> None:
    if OUT.exists():
        raise SystemExit("REFUSING: items.json already exists")
    doc = build()
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "sha256": doc["sha256"], "items": len(doc["items"])}))


if __name__ == "__main__":
    main()
