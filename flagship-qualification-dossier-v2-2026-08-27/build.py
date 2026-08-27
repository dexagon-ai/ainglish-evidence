#!/usr/bin/env python3
"""Turn the 17-entry live catalog into an explicit qualification action dossier."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODERN = ROOT.parent / "flagship-modern-carriers-v2-2026-08-27" / "index.json"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def action(rank: int, stage: str, qualification: str) -> tuple[str, str]:
    if rank <= 4:
        return "activate-modern-carrier", "Keep the guarded public card; activate its frozen modern form-stratified carrier when both external gates clear."
    if qualification == "candidate_instrument_review":
        return "run-modern-remediation", "Retain both supportive and adverse history; activate the fresh complete-comparator remediation without reusing any observed cell."
    if qualification == "candidate_needs_comprehension":
        return "author-modern-carrier", "Keep the ratified semantic distinction visible with a comprehension-evidence guard; prepare a fresh modern carrier."
    if stage == "seconded":
        return "complete-original-evidence", "Preserve the current revision and complete its declared original evidence before seeking a ballot."
    if stage == "measured":
        return "settle-or-repair", "Resolve adverse or incomplete evidence with the declared comparator; amend the claim rather than pooling conflicts."
    return "hold", "Do not advance a public empirical claim from the current record."


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    unsigned = dict(snapshot)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected
    modern = json.loads(MODERN.read_text(encoding="utf-8"))
    modern_slugs = {row["proposal_revision"] for row in modern["outputs"].values()}
    rows = []
    for entry in snapshot["catalog"]["entries"]:
        p = entry["project"]
        q = p["flagship_qualification"]
        adoption = p["adoption"]
        coverage = (adoption.get("methodology") or {}).get("coverage") or {}
        lane, next_action = action(entry["editorial"]["rank"], p["stage"], q["state"])
        rows.append({
            "rank": entry["editorial"]["rank"],
            "slug": entry["pinned_slug"],
            "public_id": p["public_id"],
            "form": p["form"],
            "stage": p["stage"],
            "surface_current": entry["surface"]["current"],
            "editorial_state": entry["editorial"]["state"],
            "qualification_state": q["state"],
            "qualified": q["qualified"],
            "measurement_hash": q["measurement_hash"],
            "instrument_gaps": q["instrument_gaps"],
            "verdict": p["verdict"],
            "evidence_contract_declared": p["evidence_readiness"]["declared"],
            "adoption": {
                "status": adoption.get("status"),
                "recent_usage": adoption.get("recent_usage"),
                "coverage_status": coverage.get("status"),
                "valid_until": coverage.get("valid_until"),
            },
            "modern_carrier_frozen": entry["pinned_slug"] in modern_slugs,
            "action_lane": lane,
            "next_safe_action": next_action,
            "public_claim": entry["editorial"]["safe_caption"],
            "claim_guard": entry["editorial"]["do_not_say"],
        })
    assert len(rows) == 17 and [row["rank"] for row in rows] == list(range(1, 18))
    dossier = {
        "kind": "dexagon.ainglish.flagship-qualification-dossier.v2",
        "captured_at": snapshot["captured_at"],
        "source_content_sha256": snapshot["source_content_sha256"],
        "rows": rows,
        "summary": {
            "stages": dict(Counter(row["stage"] for row in rows)),
            "qualification_states": dict(Counter(row["qualification_state"] for row in rows)),
            "modern_carriers_frozen": sum(row["modern_carrier_frozen"] for row in rows),
            "qualified": sum(row["qualified"] for row in rows),
        },
        "claim_boundary": "Editorial intuitiveness, lifecycle stage, modern instrument qualification, and adoption coverage are separate facts.",
        "model_calls": 0,
        "governance_writes": 0,
    }
    dossier["content_sha256"] = hashlib.sha256(canonical(dossier)).hexdigest()
    (ROOT / "dossier.json").write_text(json.dumps(dossier, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Flagship qualification dossier v2", "",
        f"Frozen live snapshot: `{snapshot['captured_at']}`. Catalog digest: `{snapshot['source_content_sha256']}`.", "",
        "This covers all 17 editorially shortlisted entries. It is an evidence-control dossier, not a new ratification gate and not a claim that editorial intuitiveness was experimentally validated.", "",
        "| Rank | Form | Stage | Qualification | Modern carrier | Next action |", "|---:|---|---|---|---|---|",
    ]
    for row in rows:
        form = row["form"].replace("|", "\\|")
        lines.append(f"| {row['rank']} | `{form}` | {row['stage']} | `{row['qualification_state']}` | {'frozen' if row['modern_carrier_frozen'] else 'not yet'} | {row['next_safe_action']} |")
    lines += [
        "", "## Current result", "",
        f"The live shortlist contains {dossier['summary']['stages'].get('ratified', 0)} ratified, {dossier['summary']['stages'].get('measured', 0)} measured, and {dossier['summary']['stages'].get('seconded', 0)} seconded entries. None yet clears the modern flagship-comprehension rubric. Five fresh carriers are frozen: the four site-leading examples and the `each-alone / as-one` remediation.", "",
        "The next bottleneck is not more item authoring for those five. It is a second independently qualified reader lineage plus deployment of form-stratified settlement. Until then, the site may show semantic distinctions and live lifecycle state, but it must not promote token savings, ratification, or editorial clarity into a comprehension claim.", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(dossier["summary"], indent=2))


if __name__ == "__main__":
    main()
