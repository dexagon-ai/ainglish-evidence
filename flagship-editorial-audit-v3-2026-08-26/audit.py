#!/usr/bin/env python3
"""Audit the v3 atlas for human-readable story completeness and lifecycle honesty."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ATLAS = ROOT.parent / "flagship-publication-atlas-v3-2026-08-26" / "publication-cards.json"

# Builder/editor judgements only. They are deliberately not empirical evidence.
REVIEW_NOTES = {
    "true-as-worded-false-as-worded-unambiguous-answers-to-negati": (False, "The current card demonstrates one pole; show both answer poles before promotion."),
    "repeat-event-restore-state-did-again-repeat-the-action-or-on-2": (False, "The contrast is intuitive, but asymmetric arguments and force projection still prevent a five-second surface pass."),
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    return value


def story_checks(card: dict) -> dict:
    return {
        "problem_is_question": isinstance(card.get("problem"), str) and card["problem"].strip().endswith("?"),
        "ordinary_ambiguity_present": isinstance(card.get("before"), str) and len(card["before"].strip()) >= 8,
        "ainglish_contrast_present": isinstance(card.get("after"), str) and " / " in card["after"],
        "operational_consequence_present": isinstance(card.get("consequence"), str) and len(card["consequence"].split()) >= 8,
        "claim_guard_present": isinstance(card.get("claim_guard"), str) and len(card["claim_guard"].split()) >= 6,
    }


def lifecycle_checks(card: dict) -> dict:
    stage = card["stage"]
    allowed = card["allowed_claim"]
    return {
        "pin_current": card["pin_is_current"] is True,
        "ratified_version_consistent": (stage == "ratified") == bool(card.get("ratified_version")),
        "candidate_not_called_standing": stage == "ratified" or "Candidate only:" in allowed,
        "draft_source_declared": card["source"] != "declared_predeploy_overlay" or "Candidate only:" in allowed,
        "next_gate_present": bool((card.get("next_gate") or {}).get("action")),
    }


def main() -> None:
    atlas = checked(ATLAS)
    rows = []
    for card in atlas["cards"]:
        story = story_checks(card)
        lifecycle = lifecycle_checks(card)
        five_second, note = REVIEW_NOTES.get(card["slug"], (True, None))
        editorial_checks = {
            "five_second_contrast": five_second,
            "familiar_ambiguity": True,
            "symmetric_slot": card["slug"] != "repeat-event-restore-state-did-again-repeat-the-action-or-on-2",
            "visible_payoff": True,
            "clean_seam": True,
        }
        story_complete = all(story.values())
        lifecycle_honest = all(lifecycle.values())
        editorial_pass = all(editorial_checks.values())
        if not story_complete or not lifecycle_honest:
            lane = "blocked_publication_copy"
        elif not editorial_pass:
            lane = "research_preview"
        elif card["stage"] == "ratified":
            lane = "standing_semantic_gallery"
        else:
            lane = "labelled_pipeline_preview"
        rows.append({
            "rank": card["rank"],
            "slug": card["slug"],
            "form": card["form"],
            "stage": card["stage"],
            "source": card["source"],
            "story_checks": story,
            "lifecycle_checks": lifecycle,
            "editorial_checks": editorial_checks,
            "story_complete": story_complete,
            "lifecycle_honest": lifecycle_honest,
            "editorial_pass": editorial_pass,
            "publication_lane": lane,
            "editorial_note": note,
        })

    packet = {
        "kind": "dexagon.ainglish.flagship-editorial-audit.v3",
        "atlas_sha256": atlas["content_sha256"],
        "evidentiary_status": "builder-editor audit only; not measurement, ratification, adoption, or human-subject evidence",
        "rows": rows,
        "summary": {
            "total": len(rows),
            "story_complete": sum(row["story_complete"] for row in rows),
            "lifecycle_honest": sum(row["lifecycle_honest"] for row in rows),
            "editorial_pass": sum(row["editorial_pass"] for row in rows),
            "blocked_publication_copy": sum(row["publication_lane"] == "blocked_publication_copy" for row in rows),
        },
        "claim_boundary": "Passing this audit permits suitable semantic copy in the stated lane. It establishes no measured comprehension advantage.",
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = packet["summary"]
    blocked = [row for row in rows if row["publication_lane"] == "blocked_publication_copy"]
    research = [row for row in rows if row["publication_lane"] == "research_preview"]
    lines = [
        "# Flagship editorial audit v3", "",
        "This is a cheap builder/editor screen over the frozen v3 atlas. It is not a model measurement and it does not recruit a large human panel.", "",
        "## Result", "",
        f"- `{summary['lifecycle_honest']}/{summary['total']}` cards keep lifecycle claims honest.",
        f"- `{summary['story_complete']}/{summary['total']}` contain the full problem → ordinary ambiguity → Ainglish contrast → operational consequence story in the captured public data.",
        f"- `{summary['editorial_pass']}/{summary['total']}` pass the bounded editorial judgement.",
        f"- `{summary['blocked_publication_copy']}` are blocked on captured publication copy, not on language quality.", "",
        "The expected pre-deploy finding is that the 13 currently deployed catalogue rows lack the new `problem` and `consequence` fields. Ainglish-Symfony PR 294 supplies them and adds four candidates; a post-deploy audit should see 17 live rows and zero draft overlay rows.", "",
        "## Blocked captured cards", "",
    ]
    for row in blocked:
        missing = [name for name, passed in row["story_checks"].items() if not passed]
        missing += [name for name, passed in row["lifecycle_checks"].items() if not passed]
        lines.append(f"- `{row['form'] or row['slug']}`: {', '.join(missing)}")
    lines += ["", "## Research-preview judgements", ""]
    for row in research:
        lines.append(f"- `{row['form'] or row['slug']}`: {row['editorial_note']}")
    lines += [
        "", "## Stop rules", "",
        "- Do not turn the editorial pass into a comprehension claim.",
        "- Do not promote a candidate by omitting its live stage.",
        "- Do not hand-edit the frozen result after deployment; capture a successor audit.",
        "- Do not require a costly human panel for this bounded copy screen.", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"summary": summary, "content_sha256": packet["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
