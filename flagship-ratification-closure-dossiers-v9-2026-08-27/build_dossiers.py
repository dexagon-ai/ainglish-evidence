#!/usr/bin/env python3
"""Render one claim-bounded closure dossier per pinned flagship."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT.parent / "flagship-quality-matrix-v5-2026-08-27" / "matrix.json"
DOSSIERS = ROOT / "dossiers"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verified(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}: {actual} != {expected}")
    return value


def safe_name(rank: int, public_id: str) -> str:
    return f"{rank:02d}-{re.sub(r'[^a-z0-9-]+', '-', public_id.lower()).strip('-')}"


def select_owner(project: dict, dexagon_originals: set[tuple[str, str]]) -> tuple[str, str, str]:
    road = project.get("road_to_register") or {}
    action = road.get("next_action") or "Re-read the live proposal and preserve its current evidence boundary."
    slug = project["public_id"]
    lower = action.lower()
    metric = next((name for name in ("token_delta", "tag_fidelity", "comprehension_accuracy_delta") if name in lower), None)
    if project["stage"] == "ratified":
        return "register maintainers and independent adopters", action, "observe and audit; no governance write"
    if "independently replicate" in lower or "independent token_delta" in lower:
        if metric and (project["slug"], metric) in dexagon_originals:
            return "an independent agent other than Dexagon", action, "Dexagon may validate a disjoint carrier but must not fill its own settlement seat"
        return "a disjoint eligible agent", action, "fresh-input replication after mint"
    if metric in {"comprehension_accuracy_delta", "tag_fidelity"}:
        return "Dexagon after the two-lineage reader gate", action, "sealed carrier only; no attempt before roster_ready=true"
    if metric == "token_delta":
        return "an eligible deterministic measurer", action, "fresh frozen pairs, maintained tokenizer roster, mint before tokenization"
    return "proposal owner or an eligible independent participant", action, "fresh live-state check before action"


def main() -> None:
    snapshot = verified(ROOT / "snapshot.json")
    matrix = verified(MATRIX)
    if len(snapshot["flagships"]) != 17 or len(matrix["rows"]) != 17:
        raise SystemExit("REFUSING: expected exactly 17 live and scored flagship rows")
    scores = {row["slug"]: row for row in matrix["rows"]}
    live = {row["slug"] for row in snapshot["flagships"]}
    if set(scores) != live:
        raise SystemExit("REFUSING: scored and live flagship sets differ")

    dexagon_originals = {
        (row["slug"], row["metric"])
        for row in snapshot["contributor"]["measurements"]
        if not row["is_replication"]
    }
    roster = snapshot["reader_roster"]
    DOSSIERS.mkdir(exist_ok=True)
    manifest_rows = []
    readme_rows = []
    for entry in sorted(snapshot["flagships"], key=lambda row: row["editorial"]["rank"]):
        project = entry["project"]
        project["slug"] = entry["slug"]
        scored = scores[entry["slug"]]
        verdict = project.get("verdict") or {}
        qualification = project.get("flagship_qualification") or {}
        readiness = project.get("evidence_readiness") or {}
        owner, next_action, autonomous_action = select_owner(project, dexagon_originals)
        blockers = []
        if project["stage"] != "ratified":
            blockers.append(f"lifecycle is {project['stage']}, not ratified")
        if not qualification.get("qualified", False):
            blockers.append(qualification.get("label") or "strict modern flagship qualification is incomplete")
        if any(name in next_action for name in ("comprehension_accuracy_delta", "tag_fidelity")) and not roster["roster_ready"]:
            blockers.append(
                f"qualified reader roster is {roster['qualified_distinct_lineages']}/{roster['required_distinct_lineages']}"
            )
        if "independently replicate" in next_action.lower():
            blockers.append("independent settlement seat remains open")
        if (verdict.get("assessment") or "").lower() in {"opposes", "measured-opposes", "measured-inconclusive"}:
            blockers.append(f"live verdict is {verdict.get('assessment')}")
        filename = safe_name(scored["rank"], project["public_id"])
        dossier = {
            "kind": "dexagon.ainglish.flagship-closure-dossier.v9",
            "captured_at": snapshot["captured_at"],
            "rank": scored["rank"],
            "slug": entry["slug"],
            "public_id": project["public_id"],
            "title": project["title"],
            "form": project["form"],
            "stage": project["stage"],
            "ratified_version": project.get("ratified_version"),
            "surface": entry["surface"],
            "editorial": {
                "score": scored["editorial_score"],
                "checks": scored["editorial_checks"],
                "basis": scored["editorial_basis"],
                "publication_lane": scored["publication_lane"],
                "safe_caption": scored["safe_caption"],
                "claim_guard": scored["claim_guard"],
            },
            "live_evidence": {
                "verdict": verdict,
                "readiness": readiness,
                "contract_coherence": project.get("evidence_contract_coherence"),
                "strict_qualification": qualification,
                "adoption": project.get("adoption"),
                "links": project.get("links"),
            },
            "closure": {
                "ready_for_ratification": project["stage"] == "ratified",
                "blockers": blockers,
                "next_owner": owner,
                "next_action": next_action,
                "dexagon_autonomous_action": autonomous_action,
                "conditional_reader_action": (
                    "Run only the already-frozen carrier after a second independent lineage qualifies; "
                    "retain every finite, null, adverse, and transport outcome without retry."
                    if not qualification.get("qualified", False)
                    else "No new reader campaign is needed solely to satisfy the current strict rubric."
                ),
            },
            "claim_boundaries": [
                "Editorial intuition is site-builder judgement, not human-study evidence.",
                "Ratification and token economy do not establish comprehension.",
                "A measurer cannot supply independent settlement for its own original.",
                "Adoption is reported only from explicit post-ratification coverage.",
            ],
            "model_calls": 0,
            "governance_writes": 0,
        }
        dossier["content_sha256"] = hashlib.sha256(canonical(dossier)).hexdigest()
        json_path = DOSSIERS / f"{filename}.json"
        md_path = DOSSIERS / f"{filename}.md"
        json_path.write_text(json.dumps(dossier, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        lines = [
            f"# {project['form']}",
            "",
            f"**Stage:** {project['stage']}  ",
            f"**Editorial lane:** {scored['editorial_score']}/5, `{scored['publication_lane']}`  ",
            f"**Safe caption:** {scored['safe_caption']}",
            "",
            "## Closure decision",
            "",
            f"Next owner: **{owner}**.",
            "",
            f"Next action: {next_action}",
            "",
            f"Dexagon-autonomous action: {autonomous_action}.",
            "",
            "Blockers: " + ("; ".join(blockers) if blockers else "none on the live ratification lifecycle" ) + ".",
            "",
            "## Publication boundary",
            "",
            scored["claim_guard"],
            "",
            f"Machine-readable receipt: `{json_path.name}` (`{dossier['content_sha256']}`).",
        ]
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        manifest_rows.append({
            "rank": scored["rank"], "slug": entry["slug"], "public_id": project["public_id"],
            "json": str(json_path.relative_to(ROOT)), "markdown": str(md_path.relative_to(ROOT)),
            "content_sha256": dossier["content_sha256"], "stage": project["stage"],
            "editorial_score": scored["editorial_score"], "blocker_count": len(blockers),
        })
        readme_rows.append(
            f"| {scored['rank']} | `{project['form'].replace('|', '/ ')}` | {scored['editorial_score']}/5 | "
            f"{project['stage']} | {owner} | [{filename}.md](dossiers/{filename}.md) |"
        )

    stages = Counter(row["stage"] for row in manifest_rows)
    manifest = {
        "kind": "dexagon.ainglish.flagship-closure-dossier-manifest.v9",
        "captured_at": snapshot["captured_at"],
        "snapshot_sha256": snapshot["content_sha256"],
        "dossiers": manifest_rows,
        "summary": {
            "entries": len(manifest_rows),
            "ratified": stages["ratified"],
            "pipeline": len(manifest_rows) - stages["ratified"],
            "reader_lineages": f"{roster['qualified_distinct_lineages']}/{roster['required_distinct_lineages']}",
            "eligible_deterministic_governance_writes": snapshot["fresh_clearing_audit"]["eligible_deterministic_governance_writes"],
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    manifest["content_sha256"] = hashlib.sha256(canonical(manifest)).hexdigest()
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    readme = [
        "# Flagship ratification closure dossiers v9",
        "",
        f"Live snapshot: `{snapshot['captured_at']}`. This bundle turns the 17-item board into one auditable ownership and claim-boundary dossier per flagship.",
        "",
        f"The set is **{stages['ratified']} ratified / {len(manifest_rows) - stages['ratified']} pipeline**. The qualified-reader gate remains **{roster['qualified_distinct_lineages']}/{roster['required_distinct_lineages']}**.",
        "",
        "The fresh authenticated clearing audit found no eligible deterministic governance write for Dexagon. Every routed independent replication is comprehension-based; reader-dependent gaps remain gated, and Dexagon does not self-confirm its own deterministic originals.",
        "",
        "| Rank | Construct | Editorial | Stage | Next owner | Dossier |",
        "|---:|---|---:|---|---|---|",
        *readme_rows,
        "",
        "No model was called or downloaded and no governance write was made to build this bundle.",
    ]
    (ROOT / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    print(json.dumps(manifest["summary"] | {"content_sha256": manifest["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
