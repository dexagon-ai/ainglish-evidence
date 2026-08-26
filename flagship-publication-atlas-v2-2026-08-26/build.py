#!/usr/bin/env python3
"""Render publication cards and a status-guarded editorial atlas."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLAIM_GUARD_OVERRIDES = {
    10: "Do not present it as ratified or evidence-ready; comprehension and tag-fidelity work remain incomplete.",
    11: "Do not present it as ratified or measured; it is seconded and its adverse token original is still unconfirmed.",
    12: "Do not imply empirical support; the fresh adverse comprehension result and its instrument diagnosis remain live.",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    return value


def gap(project: dict) -> str:
    readiness = project.get("evidence_readiness") or {}
    if not readiness.get("declared"):
        return "contract unspecified"
    values = list(readiness.get("missing_evidence") or [])
    values += ["opposing:" + value for value in (readiness.get("opposing_evidence") or [])]
    return ", ".join(values) if values else "complete"


def tier(rank: int) -> str:
    if rank <= 4:
        return "A-homepage-now"
    if rank <= 9:
        return "B-ratified-gallery-with-evidence-guard"
    if rank in (10, 11, 14):
        return "C-pipeline-preview"
    return "D-do-not-feature-yet"


def next_action(rank: int, project: dict) -> str:
    return {
        1: "Run form-separated comprehension after reader qualification; current caption may describe meaning, not measured superiority.",
        2: "Confirm comprehension and keep use-versus-mention adoption caution.",
        3: "Confirm comprehension; separate missing evidence from inadequate search.",
        4: "Confirm comprehension with delegation-chain attachment cells.",
        5: "Resolve the adverse comprehension original with a fresh disjoint instrument.",
        6: "Adjudicate conflicting evidence separately by omission pole.",
        7: "Adjudicate deadline-event comprehension and compression conflicts.",
        8: "Resolve measured-inconclusive evidence before claiming a win.",
        9: "Resolve measured-inconclusive evidence before claiming a win.",
        10: "Complete tag fidelity and one disjoint form/comparator comprehension settlement.",
        11: "Confirm the adverse token price, then run whole/part and attachment comparators.",
        12: "Do not dilute the fresh adverse result; diagnose or amend.",
        13: "Repair the token contract before more comprehension spend.",
        14: "Obtain an independent semantic second; then file the frozen token packet and retain the sealed comprehension carrier.",
    }[rank]


def main() -> None:
    snapshot = checked(ROOT / "snapshot.json")
    cards = []
    for row in snapshot["official"]:
        project = row["current_project"]
        editorial = row["editorial"]
        rank = row["rank"]
        cards.append({
            "rank": rank,
            "category": row["category"],
            "publication_tier": tier(rank),
            "current_slug": row["current_slug"],
            "pin_is_current": row["pin_is_current"],
            "form": project.get("form") or row["catalog_project"].get("form"),
            "stage": project.get("stage"),
            "ratified_version": project.get("ratified_version") or row["catalog_project"].get("ratified_version"),
            "before": editorial["before"],
            "after": editorial["after"],
            "caption": editorial["safe_caption"],
            "claim_guard": CLAIM_GUARD_OVERRIDES.get(rank, editorial["do_not_say"]),
            "evidence_gap": gap(project),
            "next_action": next_action(rank, project),
        })
    for row in snapshot["pipeline_additions"]:
        project = row["project"]
        rank = row["editorial_rank"]
        cards.append({
            "rank": rank,
            "category": row["category"],
            "publication_tier": tier(rank),
            "current_slug": project["slug"],
            "pin_is_current": True,
            "form": project["form"],
            "stage": project["stage"],
            "ratified_version": project.get("ratified_version"),
            "before": row["before"],
            "after": row["after"],
            "caption": row["safe_caption"],
            "claim_guard": row["do_not_say"],
            "evidence_gap": gap(project),
            "next_action": next_action(rank, project),
        })
    packet = {
        "kind": "dexagon.ainglish.flagship-publication-cards.v2",
        "snapshot_sha256": snapshot["content_sha256"],
        "cards": cards,
        "claim_rule": "Semantic captions may explain the registered distinction. Superiority, comprehension, adoption, and popularity claims require their own live evidence.",
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    (ROOT / "publication-cards.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Flagship publication atlas v2", "",
        f"Snapshot: `{snapshot['captured_at']}`. Official catalog: {len(snapshot['official'])} cards; one additional pipeline candidate. Catalog digest: `{snapshot['catalog_sha256']}`.", "",
        "This is an editorial and evidence-control artifact. It permits plain explanations of what a construct means; it does not turn ratification, intuition, token price, or scanner counts into a comprehension claim.", "",
        "## Publication matrix", "",
        "| Rank | Construct | Stage | Tier | Evidence gap | Next action |", "|---:|---|---|---|---|---|",
    ]
    for card in cards:
        form = (card["form"] or card["current_slug"]).replace("|", "/")
        lines.append(f"| {card['rank']} | `{form}` | {card['stage']} | `{card['publication_tier']}` | {card['evidence_gap']} | {card['next_action']} |")
    lines += ["", "## Website-ready cards", ""]
    for card in cards:
        lines += [
            f"### {card['rank']}. `{(card['form'] or card['current_slug']).replace('|', '/')}`", "",
            f"- Before: {card['before']}",
            f"- After: {card['after']}",
            f"- Safe caption: {card['caption']}",
            f"- Status: `{card['stage']}`; publication tier `{card['publication_tier']}`.",
            f"- Claim guard: {card['claim_guard']}", "",
        ]
    stale = [card for card in cards if not card["pin_is_current"]]
    lines += [
        "## Release recommendation", "",
        "Use ranks 1-4 on the homepage now as explanations of ratified distinctions, with no claim that a human or model panel proved them superior. Keep ranks 5-9 in a guarded ratified gallery. Show moved-direction, list completeness, and role cardinality only as pipeline previews. Do not feature ranks 12-13 until their adverse evidence or contract defects are resolved.", "",
        f"Catalog maintenance: {len(stale)} official pins still resolve through a superseded slug. Their current slugs are preserved in `publication-cards.json`.", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"cards": len(cards), "tiers": {name: sum(card["publication_tier"] == name for card in cards) for name in sorted({card["publication_tier"] for card in cards})}, "stale_pins": len(stale), "content_sha256": packet["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
