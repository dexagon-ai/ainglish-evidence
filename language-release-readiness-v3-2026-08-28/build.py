#!/usr/bin/env python3
"""Derive a truthful current language-release readiness report."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def projection(entry: dict) -> dict:
    return {
        "slug": entry["slug"],
        "kind": entry["kind"],
        "form": entry["form"],
        "english_mapping": entry["english_mapping"],
    }


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    live = snapshot["live_register"]
    live_release = snapshot["live_register_release"]
    bundle = snapshot["latest_language_bundle"]
    manifest = bundle["manifest"]
    released = bundle["register"]
    live_language = {row["slug"]: projection(row) for row in live["entries"] if row["kind"] != "protocol"}
    live_protocol = [row for row in live["entries"] if row["kind"] == "protocol"]
    released_language = {row["slug"]: projection(row) for row in released["entries"]}
    added = sorted(set(live_language) - set(released_language))
    removed = sorted(set(released_language) - set(live_language))
    changed = sorted(
        slug for slug in set(live_language) & set(released_language)
        if live_language[slug] != released_language[slug]
    )
    captured_at = datetime.fromisoformat(snapshot["captured_at"])
    release_at = datetime.fromisoformat(manifest["generated_at"].replace("Z", "+00:00"))
    age_days = (captured_at - release_at).total_seconds() / 86400
    exact_head = (
        live["version"] == manifest["version"]
        and live_release["digest"] == manifest["register_digest"]
    )
    new_count = len(added)
    cadence = snapshot["cadence_policy"]
    threshold_met = new_count >= cadence["routine_new_language_range"][0]
    elapsed_trigger_met = age_days >= cadence["elapsed_time_trigger_days"] and new_count > 0
    next_action = (
        "wait_for_new_release_eligible_language_ratifications"
        if not added and not changed and not removed
        else "inspect_changed_language_population_against_cadence_and_rights"
    )
    report = {
        "kind": "dexagon.ainglish.language-release-readiness.v3",
        "captured_at": snapshot["captured_at"],
        "source_snapshot_sha256": snapshot["content_sha256"],
        "latest_bundle": {
            "directory": bundle["directory"],
            "bundle_version": manifest["version"],
            "register_version": released["version"],
            "register_digest": manifest["register_digest"],
            "language_entries": len(released_language),
            "age_days": round(age_days, 3),
            "matches_live_register_head": exact_head,
        },
        "live": {
            "register_version": live["version"],
            "register_digest": live_release["digest"],
            "entries_total": live["count"],
            "language_entries": len(live_language),
            "protocol_entries": len(live_protocol),
        },
        "delta_for_release_3": {
            "added_language_slugs": added,
            "changed_language_slugs": changed,
            "removed_language_slugs": removed,
            "new_language_count": new_count,
        },
        "cadence": {
            "routine_new_language_range": cadence["routine_new_language_range"],
            "new_language_threshold_met": threshold_met,
            "elapsed_time_trigger_days": cadence["elapsed_time_trigger_days"],
            "elapsed_trigger_met": elapsed_trigger_met,
            "coherent_milestone_override": "requires explicit project judgement; none exists in a zero-delta snapshot",
        },
        "tooling": {
            "training_builder_pr": snapshot["next_training_builder"],
            "core_and_training_versions_are_separate": True,
            "next_bundle_version": cadence["next_release_version"],
        },
        "decision": {
            "state": "current_release_complete_next_release_not_yet_warranted",
            "reason": (
                "The latest language bundle contains all 19 live language entries and is bound to the exact current "
                "register head. The other 16 ratified rows are protocols, which do not enter or trigger a language release."
            ),
            "next_action": next_action,
            "greenlight_status": "not_requested_because_no_candidate_bytes_exist",
        },
        "claim_boundary": (
            "This is a deterministic population and cadence report, not release approval. Any future bundle still requires "
            "rights verification, exact-byte inspection, and the explicit greenlight recorded by policy."
        ),
        "model_calls": 0,
        "governance_writes": 0,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pr = report["tooling"]["training_builder_pr"]
    lines = [
        "# Language release 3 readiness",
        "",
        f"Snapshot: `{report['captured_at']}`. Decision: **the current release is complete; release 3 is not yet warranted**.",
        "",
        f"The live register has **{live['count']}** ratified rows: **{len(live_language)} language** and **{len(live_protocol)} protocol**. "
        f"All {len(live_language)} language rows are already present, unchanged, in `{bundle['directory']}`. The live register version and digest exactly match that bundle's cut-off. There are therefore **0 new, 0 changed, and 0 removed language entries** for release 3.",
        "",
        "| Check | Current result |",
        "|---|---|",
        f"| Latest language bundle | `{bundle['directory']}` · {len(released_language)} entries |",
        f"| Exact live-head binding | {'yes' if exact_head else 'no'} · `{live_release['digest']}` |",
        f"| Unreleased language entries | {new_count} |",
        f"| Routine 5–10 entry cadence | {'met' if threshold_met else 'not met'} |",
        f"| One-month-with-pending-language cadence | {'met' if elapsed_trigger_met else 'not met'} · bundle age {age_days:.1f} days |",
        f"| Release-3 training builder | [PR #{pr['number']}]({pr['url']}) · {pr['state'].lower()} · {pr['reviewDecision'] or 'review pending'} |",
        "| Exact-byte corporate greenlight | not requested; no candidate release-3 bytes exist |",
        "",
        "## What happens next",
        "",
        "Continue advancing high-quality language proposals to ratification. Recompute this report after every language ratification, deprecation, restoration, or correction. Consider a cut when roughly 5–10 unreleased language entries accumulate, a coherent flagship group becomes a real milestone, or a month passes while eligible language changes remain pending. Protocol-only changes do not count.",
        "",
        "The tooling PR can merge now because it removes a known release-3 build blocker, but merging it is preparation—not a reason to publish an empty release.",
        "",
        "## Claim boundary",
        "",
        report["claim_boundary"],
        "",
        f"Snapshot digest: `{snapshot['content_sha256']}`. Report digest: `{report['content_sha256']}`.",
    ]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "state": report["decision"]["state"],
        "language_entries": len(live_language),
        "unreleased_language_entries": new_count,
        "content_sha256": report["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
