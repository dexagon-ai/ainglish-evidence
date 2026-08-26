#!/usr/bin/env python3
"""Render qualification decisions, publication cards, adoption cautions, and semantic seams."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


DECISIONS = {
    1: ("publish-guarded", "Run form-separated comprehension after a qualified reader roster exists."),
    2: ("publish-guarded", "Confirm comprehension; retain the current use-versus-mention caution."),
    3: ("publish-guarded", "Confirm comprehension; distinguish missing evidence from inadequate search."),
    4: ("publish-guarded", "Confirm comprehension and test delegation-chain attachment."),
    5: ("hold-evidence-claim", "Resolve the adverse comprehension original with a fresh disjoint instrument."),
    6: ("hold-evidence-claim", "Adjudicate conflicting comprehension evidence separately by omission pole."),
    7: ("hold-evidence-claim", "Adjudicate deadline-event comprehension and compression conflicts."),
    8: ("hold-evidence-claim", "Resolve the measured-inconclusive record before claiming a win."),
    9: ("hold-evidence-claim", "Resolve the measured-inconclusive record before claiming a win."),
    10: ("advance-pipeline", "Update the editorial pin; complete tag fidelity and one disjoint comprehension settlement."),
    11: ("advance-with-price-caveat", "Update the editorial pin; replicate token price, then run the promised whole/part and attachment comparator."),
    12: ("hold-adverse", "Do not dilute the fresh adverse comprehension replication; diagnose or amend."),
    13: ("repair-contract", "Amend the token prerequisite to the visible accepted bound before comprehension spend."),
}


PUBLICATION_TIERS = {
    1: "A-homepage-now", 2: "A-homepage-now", 3: "A-homepage-now", 4: "A-homepage-now",
    5: "B-ratified-status-guard", 6: "B-ratified-status-guard", 7: "B-ratified-status-guard",
    8: "B-ratified-status-guard", 9: "B-ratified-status-guard",
    10: "C-pipeline-preview", 11: "C-pipeline-preview",
    12: "D-do-not-feature", 13: "D-do-not-feature",
}


COLLISIONS = [
    ("we-including/excluding", "you-one/all", "composable", "speaker-group inclusion and addressee cardinality are separate axes"),
    ("you-one/all", "each-alone/as-one", "scope-sensitive", "plural addressee and distributive action can compose, but order and attachment must be explicit"),
    ("fact-not-known/choice-not-made", "proposal-by/decision-by", "complementary", "epistemic or decision state is distinct from who proposed or decided"),
    ("moved-earlier/later", "start-by/complete-by", "composable", "change direction is distinct from the event constrained by a deadline"),
    ("among-others/and-no-others", "whole/part", "overlap-needs-incremental-test", "both encode completeness; the terminator must earn its place through local attachment"),
    ("some-or-all/some-but-not-all", "among-others/and-no-others", "composable-but-confusable", "quantifier cardinality and list closure are distinct but easy to conflate"),
    ("may-as-permission/possibility", "rather-not/fine-either-way/would-welcome", "complementary", "authority and sender preference are independent"),
    ("or-both/not-both", "some-or-all/some-but-not-all", "orthogonal", "choice-set admissibility and quantified population size are different claims"),
    ("no-delegation/one-hop", "by-unknown/by-withheld", "orthogonal", "handoff authority does not identify or conceal the actor"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}")
    return value


def adoption_shadow() -> dict[str, dict]:
    report = json.loads((REPO / "adoption-v3-shadow-benchmark-2026-08-26" / "report.json").read_text(encoding="utf-8"))
    return {row["proposal_slug"]: row for row in report["constructs"]}


def fmt_missing(readiness: dict | None) -> str:
    if not readiness or not readiness.get("declared"):
        return "unspecified"
    values = list(readiness.get("missing_evidence", [])) + [f"opposing:{x}" for x in readiness.get("opposing_evidence", [])]
    return ", ".join(values) if values else "complete"


def main() -> None:
    snapshot = checked(ROOT / "snapshot.json")
    shadow = adoption_shadow()
    cards = []
    lines = [
        "# Flagship qualification dossier",
        "",
        f"Live snapshot: `{snapshot['captured_at']}`. Catalog digest: `{snapshot['source']['catalog_content_sha256']}`.",
        "",
        "This is an editorial and evidence-control artifact. It does not convert semantic intuitiveness, ratification, token counts, or scanner hits into a comprehension claim.",
        "",
        "## Decision matrix",
        "",
        "| Rank | Construct | Current stage | Evidence gap | Disposition | Next safe action |",
        "|---:|---|---|---|---|---|",
    ]
    for row in snapshot["entries"]:
        rank = row["rank"]
        project = row["current_project"]
        editorial = row["editorial"]
        disposition, action = DECISIONS[rank]
        form = (project.get("form") or row["catalog_project"].get("form") or project.get("title")).replace("|", "\\|")
        lines.append(f"| {rank} | `{form}` | {project['stage']} | {fmt_missing(project.get('evidence_readiness'))} | `{disposition}` | {action} |")
        cards.append({
            "rank": rank,
            "publication_tier": PUBLICATION_TIERS[rank],
            "current_slug": row["current_slug"],
            "pin_is_current": row["pin_is_current"],
            "form": project.get("form") or row["catalog_project"].get("form"),
            "stage": project["stage"],
            "before": editorial["before"],
            "after": editorial["after"],
            "caption": editorial["safe_caption"],
            "claim_guard": editorial["do_not_say"],
            "disposition": disposition,
        })
    lines += [
        "",
        "## Publication recommendation",
        "",
        "The four safest homepage cards now are clusivity, addressee cardinality, missing-fact versus missing-choice, and delegation depth. They are ratified, immediately understandable, and can be presented as semantic distinctions with explicit evidence guards.",
        "",
        "Ranks 5-9 may appear in a secondary ratified gallery only with an evidence-under-review label. `moved-earlier / moved-later` and `among-others / and-no-others` belong in a clearly labelled pipeline preview until their successor surfaces ratify. Do not feature ranks 12-13 while the adverse instrument result and contract defect remain live.",
        "",
        "## Catalog pin audit",
        "",
    ]
    stale = [row for row in snapshot["entries"] if not row["pin_is_current"]]
    for row in stale:
        lines.append(f"- Rank {row['rank']} is pinned to superseded `{row['pinned_slug']}`; current is `{row['current_slug']}`.")
    lines += [
        "",
        "## Adoption audit",
        "",
        "The current site values use the production v2 detector. The frozen v3 shadow benchmark is stricter and abstains on ambiguous mixed messages; these differences make scanner counts unsuitable as popularity scores.",
        "",
        "| Rank | Construct | Current production status/count | Frozen v2 use | Frozen v3 use | V3 abstain |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for row in snapshot["entries"]:
        slug = row["current_slug"]
        adoption = row["catalog_project"].get("adoption") or {}
        found = shadow.get(slug)
        if found:
            lines.append(
                f"| {row['rank']} | `{row['catalog_project']['form'].replace('|', '/')} ` | "
                f"{adoption.get('status')} / {adoption.get('recent_usage')} | {found['v2']['use']} | {found['v3']['use']} | {found['v3'].get('abstain', 0)} |"
            )
    lines += [
        "",
        "Interpretation: clusivity's observed zero is stable under both detectors; delegation's single use is stable. The other flagship counts are materially detector-sensitive. Say `observed use under detector v2`, never `adopted by N agents` or `popular`.",
        "",
        "## Semantic seam review",
        "",
        "| Left | Right | Assessment | Reason |",
        "|---|---|---|---|",
    ]
    for left, right, status, reason in COLLISIONS:
        lines.append(f"| `{left}` | `{right}` | `{status}` | {reason} |")
    lines += [
        "",
        "The actionable collision is list completeness versus `whole/part`: the next `among-others` comprehension carrier must include the promised three-arm comparison and two-enumeration attachment stratum. The existing 48-pair careful-English carrier is therefore retained as design material, not run as the confirmatory claim carrier.",
    ]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    card_packet = {
        "kind": "ainglish.flagship-publication-cards.v1",
        "snapshot_sha256": snapshot["content_sha256"],
        "cards": cards,
        "claim_rule": "captions describe semantic distinctions; empirical claims require attached live receipts",
    }
    card_packet["content_sha256"] = hashlib.sha256(canonical(card_packet)).hexdigest()
    (ROOT / "publication-cards.json").write_text(json.dumps(card_packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "entries": len(cards),
        "tier_counts": {tier: sum(card["publication_tier"] == tier for card in cards) for tier in sorted(set(PUBLICATION_TIERS.values()))},
        "stale_pins": len(stale),
        "semantic_seams": len(COLLISIONS),
        "publication_cards_sha256": card_packet["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
