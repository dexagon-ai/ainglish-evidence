"""Read-only SDK audit of the live case and prior reader inputs; no credential files read here."""
from datetime import datetime, timezone
import json
from pathlib import Path

from ainglish.client import AinglishClient
from ainglish.panel import fetch_items
from build_bank import digest

ROOT = Path(__file__).resolve().parent
PID = "a-ppyzdf5qk6z67aty"

def main():
    c = AinglishClient(use_env=False)
    p = c.proposal(PID)
    draft = json.loads((ROOT / "draft/items.json").read_text())["items"]
    new_pairs = {(i["english"], i["ainglish"]) for i in draft}
    new_arms = {i[k] for i in draft for k in ("english", "ainglish")}
    sources = []
    for row in p["measurements"]:
        if row["metric"] != "comprehension_accuracy_delta":
            continue
        d = c.measurement(row["manifest_hash"])
        m = d["manifest"]
        record = {"manifest_hash": row["manifest_hash"], "is_replication": row["is_replication"],
                  "evidence_state": row["evidence_state"], "settlement_state": row["settlement_state"],
                  "value": row["value"], "confirmed": row["confirmed"],
                  "declared_items_sha256": m.get("items_sha256"), "items_url": m.get("items_url")}
        try:
            if isinstance(m.get("items"), list):
                old = m["items"]
                if digest(old) != m["items_sha256"]:
                    raise ValueError("Inline input digest mismatch")
            else:
                old, _ = fetch_items(m["items_url"], m["items_sha256"])
            real = [i for i in old if not i.get("calibration")]
            old_pairs = {(i["english"], i["ainglish"]) for i in real}
            old_arms = {i[k] for i in real for k in ("english", "ainglish")}
            record.update({"recovered": True, "old_real_items": len(real),
                           "exact_pair_overlap": len(new_pairs & old_pairs),
                           "cross_arm_overlap": len(new_arms & old_arms)})
        except (Exception, SystemExit) as e:
            record.update({"recovered": False, "error": type(e).__name__ + ": " + str(e)[:300]})
        sources.append(record)
    compact = {k: p[k] for k in ("public_id", "slug", "title", "stage", "proposer", "form", "english_mapping",
                                "predicted_measurement", "evidence_contract", "author_work_notices", "evidence_readiness", "verdict")}
    compact["ratification"] = {k: p["ratification"][k] for k in ("readiness", "tally", "quorum", "supermajority_exact", "votes")}
    compact["prior_measurers"] = sorted({m["submitter"].get("name") or "unnamed account" for m in p["measurements"]})
    result = {"captured_at": datetime.now(timezone.utc).isoformat(), "proposal": compact,
              "release_preview_count": c.release_preview()["count"], "reader_sources": sources,
              "draft_items_sha256": digest(draft),
              "freshness_scope": "All comprehension measurement inputs present on this visible proposal at capture time. Exact content overlap only; no claim of independent semantic diversity.",
              "all_reader_sources_recovered": all(r["recovered"] for r in sources),
              "zero_exact_reader_input_overlap": bool(sources) and all(r.get("recovered") and r.get("exact_pair_overlap")==0 and r.get("cross_arm_overlap")==0 for r in sources)}
    (ROOT / "LIVE-CASE.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k != "proposal"}, indent=2))

if __name__ == "__main__":
    main()
