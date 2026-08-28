#!/usr/bin/env python3
"""Capture the complete public proposal slug namespace and rank pre-ratification cleanup."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
ACTIVE_STAGES = {"proposed", "seconded", "measured"}
MANUAL_NAMES = {
    "a-0w08sbp8900wxtqb": "by-construction-by-rule-in-practice",
    "a-ptwhg57dq4w4fas4": "same-one-same-kind-same-name",
    "a-1v2tfbyk5zc0g40w": "repeat-event-restore-state",
    "a-vdfmetgvbqe4eczj": "percentage-points-not-percent",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def slug_base(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fit_slug(base: str, suffix: str = "", limit: int = 60) -> str:
    room = max(1, limit - len(suffix))
    prefix = base[:room]
    if len(base) > room and "-" in prefix:
        prefix = prefix.rsplit("-", 1)[0]
    prefix = prefix.rstrip("-") or "proposal"
    return prefix + suffix


def preferred_base(row: dict) -> str:
    if row["kind"] == "protocol":
        return slug_base(row["title"])
    slot = row.get("slot") or {}
    surface = " ".join(slot) if slot else row.get("form", "")
    candidate = slug_base(surface)
    if not any(re.search(r"[a-z]{3}", token) for token in candidate.split("-")):
        candidate = slug_base(row["title"])
    return candidate or "proposal"


def available_name(base: str, public_id: str, owners: dict[str, str]) -> tuple[str, str | None]:
    slug = fit_slug(base)
    collision = owners.get(slug)
    if collision in {None, public_id}:
        return slug, collision
    n = 2
    while True:
        slug = fit_slug(base, f"-{n}")
        if owners.get(slug) in {None, public_id}:
            return slug, collision
        n += 1


def flags(row: dict, preferred: str) -> list[str]:
    slug = row["slug"]
    out = []
    if len(slug) >= 60:
        out.append("at-generation-limit")
    if slug.endswith("-"):
        out.append("trailing-hyphen")
    if re.search(r"-[2-9][0-9]*$", slug):
        out.append("collision-suffix")
    title_prefix = fit_slug(slug_base(row["title"]))
    if slug.rstrip("-") == title_prefix.rstrip("-") or slug.startswith(title_prefix.rstrip("-")[:45]):
        out.append("title-derived")
    if preferred != slug:
        out.append("form-name-differs")
    if len(preferred) + 15 <= len(slug):
        out.append("materially-shorter-name-available")
    return out


def score(row: dict, row_flags: list[str], preferred: str) -> int:
    points = {
        "trailing-hyphen": 7,
        "at-generation-limit": 4,
        "collision-suffix": 2,
        "title-derived": 2,
        "form-name-differs": 2,
        "materially-shorter-name-available": 4,
    }
    value = sum(points[name] for name in row_flags)
    value += {"measured": 3, "seconded": 2, "proposed": 1}.get(row["stage"], 0)
    if row["public_id"] in MANUAL_NAMES and preferred != row["slug"]:
        value += 10
    return value


def main() -> None:
    client = AinglishClient(use_env=False)
    rows = list(client.iter_proposals(page_size=200))
    if len({row["public_id"] for row in rows}) != len(rows):
        raise SystemExit("REFUSING: duplicate public IDs in complete proposal sweep")

    histories = {row["public_id"]: client.proposal_slug_history(row["public_id"]) for row in rows}
    owners = {row["slug"]: row["public_id"] for row in rows}
    for public_id, history in histories.items():
        for alias in history.get("aliases", []):
            if alias in owners and owners[alias] != public_id:
                raise SystemExit(f"REFUSING: namespace collision on {alias}")
            owners[alias] = public_id

    ledger_rows = []
    for row in sorted(rows, key=lambda value: value["public_id"]):
        public_id = row["public_id"]
        base = MANUAL_NAMES.get(public_id, preferred_base(row))
        suggested, collision_owner = available_name(base, public_id, owners)
        row_flags = flags(row, suggested)
        ever_ratified = row.get("ratified_version") is not None
        active = row["stage"] in ACTIVE_STAGES
        visible = row.get("publication_status") == "visible"
        renamable = active and visible and not ever_ratified
        history = histories[public_id]
        ledger_rows.append({
            "public_id": public_id,
            "current_slug": row["slug"],
            "slug_length": len(row["slug"]),
            "title": row["title"],
            "form": row.get("form"),
            "kind": row["kind"],
            "stage": row["stage"],
            "publication_status": row.get("publication_status"),
            "ratified_version": row.get("ratified_version"),
            "active": active,
            "renamable_by_policy": renamable,
            "aliases": history.get("aliases", []),
            "rename_changes": history.get("changes", []),
            "flags": row_flags,
            "preferred_slug": suggested,
            "preferred_slug_length": len(suggested),
            "preferred_name_collision_owner": collision_owner if collision_owner != public_id else None,
            "rename_recommended": renamable and suggested != row["slug"] and score(row, row_flags, suggested) >= 8,
            "priority_score": score(row, row_flags, suggested),
        })

    ranked = sorted(
        (row for row in ledger_rows if row["active"] and row["preferred_slug"] != row["current_slug"]),
        key=lambda row: (-row["priority_score"], row["public_id"]),
    )
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    document = {
        "kind": "dexagon.ainglish.proposal-slug-quality-ledger.v1",
        "generated_at": generated_at,
        "source": "https://ainglish.org/api/v1/proposals plus each public slug-history endpoint",
        "proposal_count": len(ledger_rows),
        "namespace_name_count": len(owners),
        "active_candidate_count": len(ranked),
        "recommended_rename_count": sum(row["rename_recommended"] for row in ledger_rows),
        "policy": {
            "active_stages": sorted(ACTIVE_STAGES),
            "ever_ratified_names_immutable": True,
            "stable_human_identity": "public_id",
            "former_slugs_remain_aliases": True,
            "ranking_is_editorial_triage_not_governance_evidence": True,
        },
        "rows": ledger_rows,
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    (ROOT / "ledger.json").write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    columns = [
        "public_id", "current_slug", "slug_length", "preferred_slug", "preferred_slug_length",
        "title", "kind", "stage", "publication_status", "ratified_version", "active",
        "renamable_by_policy", "rename_recommended", "priority_score", "flags", "aliases",
    ]
    with (ROOT / "ledger.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in ledger_rows:
            flat = {key: row.get(key) for key in columns}
            flat["flags"] = "|".join(row["flags"])
            flat["aliases"] = "|".join(row["aliases"])
            writer.writerow(flat)

    report = [
        "# Ranked active slug cleanup candidates",
        "",
        f"Captured {generated_at}: {len(ledger_rows)} proposals, {len(owners)} reserved names, "
        f"{len(ranked)} active rows with a different form-oriented name.",
        "",
        "Ranking is editorial triage, not evidence about the language proposal and not authority to rename. "
        "The server rechecks visibility, ever-ratified state, reports, namespace ownership, and idempotency under lock.",
        "",
        "| Rank | Score | Stage | Public ID | Current slug | Preferred slug | Flags |",
        "|---:|---:|---|---|---|---|---|",
    ]
    for index, row in enumerate(ranked, 1):
        report.append(
            f"| {index} | {row['priority_score']} | {row['stage']} | `{row['public_id']}` | "
            f"`{row['current_slug']}` | `{row['preferred_slug']}` | {', '.join(row['flags'])} |"
        )
    (ROOT / "ranked-active.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    digests = []
    names = ["ledger.json", "ledger.csv", "ranked-active.md"]
    if (ROOT / "rename-batch.json").is_file():
        names.append("rename-batch.json")
    for name in names:
        digests.append(f"{hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}  {name}")
    (ROOT / "SHA256SUMS").write_text("\n".join(digests) + "\n", encoding="utf-8")
    print(json.dumps({
        "proposal_count": len(ledger_rows),
        "namespace_name_count": len(owners),
        "active_candidate_count": len(ranked),
        "recommended_rename_count": document["recommended_rename_count"],
        "content_sha256": document["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
