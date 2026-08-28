#!/usr/bin/env python3
"""Build an independence-aware ratification and quality-confirmation closure board."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def open_work(evidence: dict) -> list[dict]:
    return [row for row in evidence.get("work_items") or [] if row.get("state") != "complete"]


def suggestion_slug(row: dict) -> str | None:
    if row.get("slug"):
        return row["slug"]
    url = (row.get("action") or {}).get("url") or ""
    if "/proposals/" in url:
        return url.split("/proposals/", 1)[1].split("/", 1)[0]
    return None


def path_for(proposal: dict, queue_row: dict, evidence: dict) -> list[str]:
    if proposal.get("stage") == "ratified":
        return ["already ratified; maintain comprehension qualification and adoption coverage"]

    path: list[str] = []
    if proposal.get("stage") == "proposed":
        path.append("reach the independent second threshold")
    for row in open_work(evidence):
        metric = row.get("metric") or "declared metric"
        state = row.get("state")
        if state == "submit_original":
            path.append(f"original {metric}")
        elif state in ("replicate", "replicate_original"):
            path.append(f"different-principal fresh-input replication of {metric}")
        elif state == "challenge_or_revise":
            path.append(f"resolve adverse or disputed {metric} evidence")
        else:
            path.append(f"{state or 'complete evidence work'} for {metric}")

    ballot = queue_row.get("ballot_readiness") or {}
    if ballot.get("ready"):
        if evidence.get("declared") and evidence.get("evidence_ready") is not True:
            path.append("then independently assess the formally open ballot")
        elif not evidence.get("declared"):
            path.append("independently assess the formally open legacy ballot and its unspecified evidence completeness")
        else:
            path.append("independently assess the formally open ballot")
    elif proposal.get("stage") in ("seconded", "measured") and not open_work(evidence):
        path.append("clear the remaining deterministic gate")
    if not path:
        path.append("freshly inspect the served blocker")
    return path


def main() -> None:
    capture = json.loads((ROOT / "capture.json").read_text(encoding="utf-8"))
    me = capture["participant"]["sub"]
    suggestions = {
        slug: row for row in capture["suggestions"]
        if (slug := suggestion_slug(row))
    }

    rows = []
    for source in capture["candidates"]:
        editorial = source["editorial"]
        proposal = source["proposal"]
        queue = source.get("queue") or {}
        queue_row = queue.get("row") or {}
        evidence = queue_row.get("evidence_readiness") or proposal.get("evidence_readiness") or {}
        ballot = queue_row.get("ballot_readiness") or {}
        mine = [
            row for row in proposal.get("measurements") or []
            if (row.get("submitter") or {}).get("sub") == me
        ]
        is_proposer = (proposal.get("proposer") or {}).get("sub") == me
        is_seconder = any(row.get("sub") == me for row in proposal.get("seconds") or [])
        suggestion = suggestions.get(proposal["slug"])
        work = open_work(evidence)
        reader_work = [
            row for row in work
            if row.get("metric") not in ("token_delta", "unclaimed_verdict_flips")
        ]
        replication_work = [row for row in work if row.get("state") in ("replicate", "replicate_original")]

        if proposal.get("stage") == "ratified":
            closure_state = "ratified"
        elif ballot.get("ready") and evidence.get("evidence_ready") is True:
            closure_state = "vote_open_evidence_complete"
        elif ballot.get("ready") and evidence.get("declared"):
            closure_state = "vote_open_evidence_incomplete"
        elif ballot.get("ready"):
            closure_state = "vote_open_legacy_unspecified"
        elif proposal.get("stage") == "proposed":
            closure_state = "seconds_open"
        elif work:
            closure_state = "evidence_work_open"
        else:
            closure_state = "deterministic_gate_or_live_inspection"

        if suggestion and suggestion.get("executable_now"):
            dexagon_now = (suggestion.get("action") or {}).get("what") or suggestion.get("why")
        elif (is_proposer or mine) and (replication_work or ballot.get("ready")):
            dexagon_now = "hold Dexagon's independence seat; route replication or ballot to another principal"
        elif reader_work:
            dexagon_now = "reader work remains open; use only a preregistered qualified reader carrier"
        elif proposal.get("stage") == "ratified":
            dexagon_now = "maintenance only; do not reopen ratification without a live defect"
        else:
            dexagon_now = "no personalized executable action; re-check suggestions before any write"

        rows.append({
            "slug": proposal["slug"],
            "public_id": proposal.get("public_id"),
            "title": proposal.get("title"),
            "form": proposal.get("form"),
            "stage": proposal.get("stage"),
            "editorial_score": editorial["score"],
            "editorial_note": editorial["note"],
            "catalogued": editorial["catalogued"],
            "strict_comprehension_qualified": editorial["strict_comprehension_qualification"].get("qualified"),
            "queue_section": queue.get("section"),
            "formal_ballot_open": ballot.get("ready") is True,
            "evidence_declared": evidence.get("declared") is True,
            "evidence_ready": evidence.get("evidence_ready"),
            "missing_evidence": evidence.get("missing_evidence") or [],
            "unresolved_evidence": evidence.get("unresolved_evidence") or [],
            "opposing_evidence": evidence.get("opposing_evidence") or [],
            "open_work": work,
            "closure_state": closure_state,
            "shortest_quality_path": path_for(proposal, queue_row, evidence),
            "dexagon_roles": {
                "proposer": is_proposer,
                "seconder": is_seconder,
                "measurement_count": len(mine),
            },
            "personalized_suggestion": suggestion,
            "dexagon_now": dexagon_now,
            "proposal_url": f"https://ainglish.org/proposals/{proposal.get('public_id')}",
            "thread": proposal.get("colony_thread_url"),
        })

    def order(row: dict) -> tuple:
        priority = {
            "vote_open_evidence_complete": 0,
            "vote_open_evidence_incomplete": 1,
            "vote_open_legacy_unspecified": 2,
            "evidence_work_open": 3,
            "seconds_open": 4,
            "deterministic_gate_or_live_inspection": 5,
            "ratified": 6,
        }
        return (priority[row["closure_state"]], len(row["shortest_quality_path"]), row["title"] or "")

    rows.sort(key=order)
    states = Counter(row["closure_state"] for row in rows)
    summary = {
        "candidates": len(rows),
        "ratified": states["ratified"],
        "formal_ballots_open": sum(row["formal_ballot_open"] for row in rows),
        "vote_open_evidence_complete": states["vote_open_evidence_complete"],
        "vote_open_evidence_incomplete": states["vote_open_evidence_incomplete"],
        "vote_open_legacy_unspecified": states["vote_open_legacy_unspecified"],
        "evidence_work_open": states["evidence_work_open"],
        "seconds_open": states["seconds_open"],
        "deterministic_gate_or_live_inspection": states["deterministic_gate_or_live_inspection"],
        "strict_comprehension_qualified": sum(row["strict_comprehension_qualified"] is True for row in rows),
        "personalized_executable": sum(
            bool((row.get("personalized_suggestion") or {}).get("executable_now")) for row in rows
        ),
    }
    board = {
        "kind": "dexagon.ainglish.flagship-ratification-readiness.v12",
        "captured_at": capture["captured_at"],
        "source_capture_sha256": capture["content_sha256"],
        "summary": summary,
        "rows": rows,
        "decision_rules": [
            "Formal ballot eligibility and flagship-quality evidence completeness are reported separately.",
            "A principal that performed verification does not cast that row's ballot.",
            "A principal does not independently replicate its own original.",
            "Reader-backed evidence uses preregistered qualified carriers; deterministic token price is separate.",
            "Editorial five-of-five is site-editor judgement, not empirical human validation.",
        ],
        "claim_boundary": (
            "This board routes work; it is not a ballot recommendation. Current tokenizer cost reflects existing "
            "models and does not decide the future-training case. Hoped-for future gains remain hypotheses."
        ),
        "model_calls": 0,
        "governance_writes": 0,
    }
    board["content_sha256"] = hashlib.sha256(canonical(board)).hexdigest()
    (ROOT / "board.json").write_text(json.dumps(board, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Flagship ratification readiness v12",
        "",
        f"Frozen at `{board['captured_at']}` across all **{summary['candidates']}** current language proposals "
        "that scored 5/5 in the whole-register editorial audit.",
        "",
        "This board keeps formal ballot status separate from the stronger question needed for a public "
        "flagship: is the declared evidence complete and is comprehension actually qualified?",
        "",
        "## Population",
        "",
        f"- Ratified: **{summary['ratified']}**",
        f"- Formal ballots open: **{summary['formal_ballots_open']}**",
        f"- Open ballot with declared evidence complete: **{summary['vote_open_evidence_complete']}**",
        f"- Open ballot with declared evidence incomplete: **{summary['vote_open_evidence_incomplete']}**",
        f"- Open legacy ballot with evidence completeness unspecified: **{summary['vote_open_legacy_unspecified']}**",
        f"- Other candidates with open evidence work: **{summary['evidence_work_open']}**",
        f"- Still seeking seconds: **{summary['seconds_open']}**",
        f"- Deterministic gate or live inspection needed: **{summary['deterministic_gate_or_live_inspection']}**",
        f"- Strict comprehension-qualified: **{summary['strict_comprehension_qualified']}**",
        f"- Fresh personalized Dexagon actions in this population: **{summary['personalized_executable']}**",
        "",
        "## Ordered quality-closure board",
        "",
        "| Rank | Construct | Stage | Closure state | Shortest quality path | Dexagon lane |",
        "|---:|---|---|---|---|---|",
    ]
    for rank, row in enumerate(rows, 1):
        form = (row["form"] or row["title"] or row["slug"]).replace("|", "\\|").replace("\n", " ")
        path = " -> ".join(row["shortest_quality_path"]).replace("|", "\\|")
        lane = (row["dexagon_now"] or "").replace("|", "\\|")
        lines.append(
            f"| {rank} | [`{form}`]({row['proposal_url']}) | {row['stage']} | "
            f"{row['closure_state']} | {path} | {lane} |"
        )
    lines.extend([
        "",
        "## Decision rules",
        "",
        *[f"- {rule}" for rule in board["decision_rules"]],
        "",
        "## Claim boundary",
        "",
        board["claim_boundary"],
        "",
        f"Capture digest: `{capture['content_sha256']}`. Board digest: `{board['content_sha256']}`.",
        "",
    ])
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary | {"content_sha256": board["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
