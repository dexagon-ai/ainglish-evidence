#!/usr/bin/env python3
"""Build lifecycle-honest publication cards from the frozen v3 snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    return value


def next_gate(project: dict) -> dict:
    if project["stage"] == "proposed":
        return {"gate": "independent_attention", "action": "An independent agent must decide whether the distinction is worth measuring."}
    readiness = project.get("evidence_readiness") or {}
    pending = [work for work in readiness.get("work_items") or [] if work.get("state", "complete") != "complete"]
    pending.sort(key=lambda work: (
        work.get("role") != "prerequisite",
        work.get("state") != "replicate_original",
    ))
    if pending:
        work = pending[0]
        action = work.get("action") or {}
        return {
            "gate": work.get("state"),
            "metric": work.get("metric"),
            "action": action.get("what") or "Complete the declared evidence item.",
        }
    if project["stage"] == "ratified":
        return {"gate": "standing_language", "action": "Observe adoption and continue regression testing."}
    if readiness.get("evidence_ready"):
        return {"gate": "ballot", "action": "Eligible independent agents may decide whether to ratify it."}
    return {"gate": "evidence_unspecified", "action": "Read the live record before claiming another gate."}


def allowed_claim(project: dict) -> str:
    if project["stage"] == "ratified":
        return "Standing Ainglish: explain the registered semantic distinction and version; attach evidence guards to empirical claims."
    return f"Candidate only: state that the row is {project['stage']} and explain the proposed distinction without implying adoption."


def main() -> None:
    snapshot = checked(ROOT / "snapshot.json")
    cards = []
    for rank, row in enumerate(snapshot["entries"], start=1):
        project = row["project"]
        editorial = row["editorial"]
        cards.append({
            "rank": rank,
            "source": row["source"],
            "slug": project["slug"],
            "title": project["title"],
            "form": project["form"],
            "stage": project["stage"],
            "ratified_version": project.get("ratified_version"),
            "pin_is_current": row["pin_is_current"],
            "category": editorial.get("category"),
            "problem": editorial.get("problem"),
            "before": editorial.get("before"),
            "after": editorial.get("after"),
            "consequence": editorial.get("consequence"),
            "safe_caption": editorial.get("safe_caption"),
            "claim_guard": editorial.get("claim_guard") or editorial.get("do_not_say"),
            "allowed_claim": allowed_claim(project),
            "next_gate": next_gate(project),
        })

    packet = {
        "kind": "dexagon.ainglish.flagship-publication-cards.v3",
        "snapshot_sha256": snapshot["content_sha256"],
        "cards": cards,
        "claim_rule": "Semantic explanations, lifecycle status, evidence status, and adoption are separate claims. Never infer one from another.",
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    (ROOT / "publication-cards.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Flagship publication atlas v3", "",
        f"Frozen at `{snapshot['captured_at']}` with {len(cards)} cards: "
        f"{snapshot['live_catalogue_entry_count']} from the deployed catalogue and "
        f"{snapshot['overlay_entry_count']} explicitly labelled pre-deploy additions.", "",
        "This atlas is editorial control material, not a measurement. A draft overlay is never described as deployed, and a candidate is never described as standing Ainglish.", "",
        "## Exact next gates", "",
        "| # | Construct | Stage | Source | Next gate |", "|---:|---|---|---|---|",
    ]
    for card in cards:
        lines.append(
            f"| {card['rank']} | `{card['form'] or card['slug']}` | {card['stage']} | "
            f"`{card['source']}` | {card['next_gate']['action']} |"
        )
    lines += [
        "", "## Publication contract", "",
        "- Lead with the ordinary ambiguity and the operational consequence.",
        "- Show the live lifecycle stage beside every non-ratified example.",
        "- Use the registered meaning as the semantic source; use evidence receipts only for empirical claims.",
        "- Treat the overlay as an editorial proposal until PR 294 is deployed and a later snapshot sees it in the live catalogue.",
        "- Re-capture instead of editing this snapshot when lifecycle state changes.", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"cards": len(cards), "content_sha256": packet["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
