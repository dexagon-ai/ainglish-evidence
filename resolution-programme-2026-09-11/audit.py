"""Read-only public evidence audit; no tokenizer, reader, mint or governance write.

Raw public envelopes are cached in a caller-selected directory; the compact report
contains source URLs and checkable facts, not private suggestions or conversations.
The snapshot spans sequential reads and must be refreshed before an action.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from ainglish.client import AinglishClient, manifest_commitment

COHORT = {
    "a-dg8qvvp9sq3b0trt", "a-6974j2deetg3rcb5", "a-k2d3rxn56qysr74n",
    "a-0w08sbp8900wxtqb", "a-gw49byppkekthhvg", "a-nyx3ea1n994e3we6",
}


def sign(value):
    return None if not isinstance(value, (int, float)) else (value > 0) - (value < 0)


def interval_state(lo, hi):
    if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
        return "not_reported"
    if lo > hi:
        return "invalid_order"
    return "negative" if hi < 0 else "positive" if lo > 0 else "includes_zero"


def comparison_checks(row):
    comp = row.get("replication_comparison") or {}
    checks = []
    for cell in comp.get("strata") or []:
        a, b, tol = (cell.get(k) for k in ("original_value", "replication_value", "tolerance"))
        if not all(isinstance(v, (int, float)) for v in (a, b, tol)):
            continue
        delta = abs(a - b)
        agrees = delta <= tol + 1e-12
        checks.append({"stratum": cell["id"], "difference_recomputed": delta,
                       "tolerance": tol, "within_tolerance": agrees,
                       "served_agreement": cell.get("reproduced_ok"),
                       "matches_served": agrees == cell.get("reproduced_ok")})
    return checks


def measurement_summary(row):
    comp = row.get("replication_comparison") or {}
    keep = ["metric", "manifest_hash", "attempt_id", "value", "value_lo", "value_hi",
            "resolution_bound", "panel_models", "panel_neff", "settlement_state",
            "settlement_eligible", "reproduced_ok", "counts_toward_verdict", "confirmed",
            "replicates_hash", "stratum_results", "at", "evidence_state"]
    out = {k: row.get(k) for k in keep}
    out["url"] = "https://ainglish.org/measurements/" + row["manifest_hash"]
    out["interval_sign"] = interval_state(row.get("value_lo"), row.get("value_hi"))
    out["source_direction_same"] = (sign(row.get("value")) == sign(comp.get("original_value"))) if comp else None
    out["roster_changed"] = comp.get("roster_changed")
    out["aggregate_reproduced_ok"] = comp.get("aggregate_reproduced_ok")
    out["strata_effect"] = comp.get("strata_effect")
    out["stratum_arithmetic"] = comparison_checks(row)
    out["arms"] = row.get("arms")
    return out


def analyse(progression, proposals, triage, sources, preview, ballots, started, finished):
    rows, alignment, comparisons = [], [], []
    for p in proposals:
        readiness = p.get("evidence_readiness") or {}
        ratification = p.get("ratification") or {}
        summaries = [measurement_summary(m) for m in p.get("measurements", [])]
        comparisons.extend(m for m in summaries if m["replicates_hash"])
        row = {"public_id": p["public_id"], "slug": p["slug"], "title": p["title"],
               "stage": p["stage"], "author": p.get("proposer"),
               "url": "https://ainglish.org/proposals/" + p["public_id"],
               "thread": p["colony_thread_url"], "verdict": p.get("verdict"),
               "evidence_ready": readiness.get("evidence_ready"),
               "work": [{k: w.get(k) for k in ["metric", "role", "state", "target_hashes"]}
                        for w in readiness.get("work_items", [])],
               "ballot": {"readiness": ratification.get("readiness"), "tally": ratification.get("tally")},
               "author_notice": (p.get("author_work_notices") or {}).get("active"),
               "measurements": summaries}
        rows.append(row)
        if readiness.get("success_criteria_review"):
            alignment.append({"public_id": p["public_id"], "title": p["title"], "url": row["url"],
                              "review": readiness["success_criteria_review"]})
    source_checks = []
    for target in triage["targets"]:
        h = target["manifest_hash"]
        source = sources[h]
        manifest = source.get("manifest")
        try:
            recomputed = manifest_commitment(manifest) if isinstance(manifest, dict) else None
        except (TypeError, ValueError):
            recomputed = None
        source_checks.append({k: target.get(k) for k in ["public_id", "manifest_hash", "metric",
                              "preparation_state", "triage_route", "comparison_identity"]} |
                             {"manifest_hash_matches": recomputed == h,
                              "computed_manifest_hash": recomputed,
                              "input_count": len(manifest.get("test_set", [])) if isinstance(manifest, dict) else None,
                              "roster": source.get("panel_models"),
                              "source_url": "https://ainglish.org/measurements/" + h})
    return {"kind": "ainglish.resolution-audit.v1", "started_at": started, "finished_at": finished,
            "read_span_not_atomic": True, "population": progression["population"],
            "release_preview": {k: preview[k] for k in ["count", "summary", "status"]},
            "ballot_counts": ballots["counts"],
            "closure_clocks": [{"public_id": r["public_id"], "title": r["title"], "tally": r["tally"],
                                "closes_at": r["progress"]["closes_at"]}
                               for r in ballots["entries"] if r["status"] == "quorum_clock"],
            "language_proposals": rows, "six_case_ids": sorted(COHORT),
            "alignment_reviews": alignment, "disputed_source_checks": source_checks,
            "comparison_summary": {"replications": len(comparisons),
                 "same_direction_disagreements": sum(r["source_direction_same"] is True and r["reproduced_ok"] is False for r in comparisons),
                 "roster_changed_disagreements": sum(r["roster_changed"] is True and r["reproduced_ok"] is False for r in comparisons),
                 "stratum_checks": sum(len(r["stratum_arithmetic"]) for r in comparisons),
                 "stratum_arithmetic_mismatches": sum(c["matches_served"] is False for r in comparisons for c in r["stratum_arithmetic"])},
            "boundary": "Audit of retained public results, not a new study or independent settlement. Same direction is not magnitude reproduction. A null interval is not noninferiority. Ceiling limits positive headroom, not the size of a possible negative effect. Different readers plus different items do not isolate a causal reader effect. No evidence or lifecycle has been changed."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    client = AinglishClient(use_env=False)

    def capture(name, read):
        path = args.cache / (name + ".json")
        if path.exists():
            return json.loads(path.read_text())
        result = read()
        with path.open("x") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
        return result

    started = datetime.now(timezone.utc).isoformat()
    progression = capture("progression", client.progression)
    preview = capture("release-preview", client.release_preview)
    ballots = capture("ballots", client.ballots)
    triage = capture("triage", client.dispute_triage)
    proposals = []
    for plan in progression["plans"]:
        if plan.get("kind") == "protocol":
            continue
        proposals.append(capture(plan["public_id"], lambda plan=plan: client.proposal(plan["slug"])))
        if len(proposals) % 10 == 0:
            print("Public proposal reads", len(proposals), flush=True)
    sources = {}
    for target in triage["targets"]:
        h = target["manifest_hash"]
        sources[h] = capture(h, lambda h=h: client.measurement(h))
    report = analyse(progression, proposals, triage, sources, preview, ballots, started,
                     datetime.now(timezone.utc).isoformat())
    with args.report.open("x") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"language_proposals": len(proposals), "alignment_reviews": len(report["alignment_reviews"]),
                      "source_hash_mismatches": sum(not r["manifest_hash_matches"] for r in report["disputed_source_checks"]),
                      **report["comparison_summary"]}))


if __name__ == "__main__":
    main()
