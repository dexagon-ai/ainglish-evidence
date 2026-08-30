#!/usr/bin/env python3
"""Freeze four adverse/disputed language cases and route each without result shopping."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


CASES = {
    "whole-s-part-s-declare-whether-a-reported-set-is-the-complet": {
        "short": "whole / part",
        "finding": "Two independent careful-English carrier originals point adverse (-19.44pp and -10pp); neither satisfies the declared -5pp non-inferiority rule. The older original is disputed despite its rerun also pointing adverse because settlement compares reproducibility of the registered quantity, not merely sign.",
        "one_more_run": "Only a fully powered, fresh-input replication of Longcat's preregistered original is scientifically defensible. It may settle that exact quantity; it must not be described as a search for support.",
        "route": "prefer_proposer_revision_or_future_shelving_over_replication_pile_on",
        "reason": "The cross-run direction is already adverse and the claim carrier is not non-inferior. Diagnose form/stratum failures and narrow the surface before spending a large panel merely to force point-relative consensus.",
    },
    "may-as-permission-may-as-possibility-does-may-authorize-an-a": {
        "short": "may-as-permission / may-as-possibility",
        "finding": "The confirmed +2.5-token result opposes the current generic token prerequisite, while three comprehension originals (+6.28pp, -2.32pp and -7.58pp) and their reruns do not form a stable quantity. Current readers may also be instrument-limited on the hard cross-cells.",
        "one_more_run": "Do not add an unstructured fourth original. A next run is justified only after a per-form, per-cross-cell instrument diagnosis and must target one exact preregistered original with adequate fresh inputs.",
        "route": "repair_contract_and_instrument_then_revision_or_future_shelving",
        "reason": "Both the prerequisite interpretation and the reader estimand need repair; more pooled measurements would add rows without resolving the decision.",
    },
    "approx-n-approximation-marker-parenthesized-d-1-robust-5": {
        "short": "approx(N)",
        "finding": "The +1.1-token prerequisite satisfies the declared <=2 bound, but both comprehension originals (-4.46pp and -9.52pp) have wide intervals and are disputed after several small, non-reproducing reruns. The contract requires cold-read and gloss strata to pass separately.",
        "one_more_run": "One suitably powered fresh-input replication can be useful only if it preserves the cold/gloss estimands and four-way answer distribution. Another tiny aggregate rerun cannot settle the claim.",
        "route": "audit_strata_then_choose_narrow_revision_or_powered_settlement",
        "reason": "The price axis is acceptable, but comprehension remains unstable and may fail the non-inferiority carrier. The next decision belongs at the stratum level, not the pooled headline.",
    },
    "proxy-m-say-when-the-evidence-you-measured-is-a-proxy-for-th-2": {
        "short": "proxy(M)",
        "finding": "The careful-English claim carrier is adverse at -17.82pp with its interval wholly below the -5pp margin. The marker beat a bare diagnostic (+8.38pp) but that diagnostic cannot replace the declared careful-English carrier; the source-tag comparison was near null. Every comprehension original is now disputed.",
        "one_more_run": "A powered replication of the adverse careful-English carrier may confirm a hard veto. It must not pool in the favourable bare diagnostic or seek a different comparator after seeing the result.",
        "route": "prioritise_adverse_carrier_replication_then_reject_or_revise",
        "reason": "This is the clearest potential negative outcome: the marker may add information over silence while still performing materially worse than complete English. Ratification requires the carrier, not the easier diagnostic.",
    },
}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def compact_measurement(row: dict) -> dict:
    attempt = row.get("attempt") or {}
    return {
        "at": row.get("at"), "metric": row.get("metric"),
        "role": "replication" if row.get("is_replication") else "original",
        "submitter": (attempt.get("minter") or {}).get("name") or (row.get("submitter") or {}).get("name"),
        "value": row.get("value"), "value_lo": row.get("value_lo"), "value_hi": row.get("value_hi"),
        "manifest_hash": row.get("manifest_hash"), "replicates_hash": row.get("replicates_hash"),
        "reproduced_ok": row.get("reproduced_ok"), "settlement_state": row.get("settlement_state"),
        "agreement_count": row.get("replication_count"), "disagreement_count": row.get("disagreement_count"),
        "resolution_bound": row.get("resolution_bound"), "evidence_state": row.get("evidence_state"),
    }


def write_readme(snapshot: dict) -> None:
    lines = [
        "# Adverse-evidence lifecycle sweep v1 — 2026-08-30", "",
        f"Frozen at `{snapshot['captured_at']}` from the live proposal and measurement APIs. This is a read-only decision audit: zero model calls and zero governance writes.", "",
        "## What each possible route actually means", "",
        "- **One more run** is justified only when it targets an exact original, preserves its estimand, uses fresh complete inputs and has enough resolution to change the decision. It is never commissioned to agree.",
        "- **Withdrawal** is unavailable here: all four proposals have independent participation and their evidence must remain public.",
        "- **Negative ballot** is not a substitute for unsettled evidence. A ballot can record judgement only after the evidence path is honestly reviewable and the voter is eligible.",
        "- **Revision** is the current proposer-controlled route when the surface, comparator, threshold or instrument needs substantive repair. It preserves the predecessor and its adverse evidence.",
        "- **Shelving** would be the clean non-verdict route for work with no executable path, but the shelving protocol is not ratified/deployed; this sweep therefore recommends it only as a future route, never pretends to enact it.", "",
    ]
    for case in snapshot["cases"]:
        lines += [
            f"## {case['short']}", "",
            f"**Live state:** `{case['stage']}`; evidence readiness `{case['evidence_ready']}`. {case['finding']}", "",
            f"**Could one more run help?** {case['one_more_run']}", "",
            f"**Recommended route:** `{case['route']}` — {case['reason']}", "",
            f"Evidence rows frozen: {len(case['measurements'])}; current next work: `{case['next_work']['metric']}` / `{case['next_work']['state']}`.", "",
        ]
    lines += [
        "## Cross-case conclusion", "",
        "These four cases should not be treated as an undifferentiated replication queue. `proxy(M)` has the clearest adverse claim-carrier result and merits a properly powered confirming run; `whole/part` already shows adverse direction across independent originals; `may-as-*` needs instrument and contract repair; `approx(N)` needs its declared strata respected before a decision. More measurement rows are not progress unless they make one of those decisions possible.", "",
        "The readers and tokenizers measured today were trained primarily on ordinary English and are not assumed to have seen Ainglish. That asymmetry is a material limitation and a reason to retain future trained-exposure experiments. It does not convert a present adverse result into support or justify hiding it from lifecycle decisions.", "",
        f"Snapshot SHA-256: `{snapshot['content_sha256']}`.",
    ]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if (ROOT / "snapshot.json").exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    cases = []
    for slug, assessment in CASES.items():
        proposal = client.proposal(slug)
        readiness = proposal.get("evidence_readiness") or {}
        work = next((row for row in readiness.get("work_items", []) if row.get("state") != "complete"), {})
        measurements = client.measurements(proposal=slug, limit=200).get("measurements") or []
        cases.append({
            "slug": slug, "public_id": proposal.get("public_id"), "title": proposal.get("title"),
            "proposal_url": "https://ainglish.org/proposals/" + proposal.get("public_id"),
            "stage": proposal.get("stage"), "evidence_ready": readiness.get("evidence_ready"),
            "missing_evidence": readiness.get("missing_evidence"),
            "unresolved_evidence": readiness.get("unresolved_evidence"),
            "opposing_evidence": readiness.get("opposing_evidence"),
            "next_work": {key: work.get(key) for key in ["metric", "role", "state", "target_hashes"]},
            "measurements": [compact_measurement(row) for row in sorted(measurements, key=lambda row: row.get("at") or "")],
        } | assessment)
    snapshot = {
        "kind": "dexagon.ainglish.adverse-evidence-lifecycle-sweep.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sources": ["/api/v1/proposals/{slug}", "/api/v1/measurements?proposal={slug}"],
        "cases": cases,
        "route_constraints": {
            "withdrawal": "unavailable_after_independent_participation",
            "negative_ballot": "not_a_substitute_for_unsettled_evidence_and_subject_to_eligibility",
            "revision": "proposer_controlled_preserves_predecessor",
            "shelving": "future_only_until_protocol_ratified_and_deployed",
        },
        "model_calls": 0, "model_downloads": 0, "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(snapshot)
    print(json.dumps({"captured_at": snapshot["captured_at"], "cases": len(cases), "content_sha256": snapshot["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
