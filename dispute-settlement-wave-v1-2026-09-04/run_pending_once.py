#!/usr/bin/env python3
"""Run the two frozen comprehension carriers skipped by the first wave."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness
from ainglish.client import manifest_commitment

from run_all_once import preflight, live_target, unload, ainglish_client


ROOT = Path(__file__).resolve().parent
PENDING = ("proposal-decision", "preference-release")


def main() -> None:
    if sdk_version != "0.2.52":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.52")
    if (ROOT / "pending-results.json").exists():
        raise SystemExit("REFUSING: this pending one-shot run already has an outcome")
    if subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT.parent,
        check=True, capture_output=True, text=True,
    ).stdout.strip():
        raise SystemExit("REFUSING: evidence repository is not clean")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"],
        cwd=ROOT.parent, check=True,
    )

    index = json.loads((ROOT / "runspec-index.json").read_text(encoding="utf-8"))
    specs = {
        name: json.loads((ROOT / index["runspecs"][name]["file"]).read_text(encoding="utf-8"))
        for name in PENDING
    }
    print("RESOURCE PREFLIGHT:", json.dumps(preflight(list(specs.values())), sort_keys=True), flush=True)
    client = ainglish_client()
    results = []

    for name, spec in specs.items():
        suggestions = client.suggestions()
        offered = {
            row.get("replicates_hash") for row in suggestions.get("suggestions", [])
            if row.get("tier") == "replications"
        }
        proposal = client.proposal(spec["slug"], authenticated=True)
        if spec["replicates_hash"] not in offered or not live_target(proposal, spec["replicates_hash"]):
            result = {
                "campaign": name,
                "state": "not_currently_offered",
                "replicates_hash": spec["replicates_hash"],
                "suggestions_generated_at": suggestions.get("generated_at"),
            }
            results.append(result)
            print("SKIP:", json.dumps(result, sort_keys=True), flush=True)
            continue

        items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
        manifest = dict(spec, items=items, items_sha256=items_digest)
        if any(field in manifest for field in ("settlement_strata", "settlement_item_field", "settlement_rule")):
            raise SystemExit("REFUSING: legacy replication carries a server settlement-strata declaration")
        print(f"START {name} after fresh personalised routing {suggestions.get('generated_at')}", flush=True)
        measurement = panel_harness._run_preregistered_panel(
            manifest, spec, panel_harness.ask, client,
            receipt_dir=str(ROOT), receipt_stem=f"runspec-{name}",
        )
        unload(spec)
        if measurement is None:
            result = {
                "campaign": name,
                "state": "aborted_or_refused",
                "replicates_hash": spec["replicates_hash"],
            }
        else:
            result = {
                "campaign": name,
                "state": "filed",
                "replicates_hash": spec["replicates_hash"],
                "manifest_hash": manifest_commitment(measurement["manifest"]),
                "value": measurement["value"],
                "value_lo": measurement["value_lo"],
                "value_hi": measurement["value_hi"],
                "arms": measurement["arms"],
                "calibration": measurement["calibration"],
                "panel_agreement": measurement["panel_agreement"],
                "per_member": measurement["per_member"],
                "yield_report": measurement.get("yield_report"),
            }
        results.append(result)
        print("RESULT:", json.dumps(result, sort_keys=True), flush=True)

    output = {
        "kind": "dexagon.ainglish.dispute-settlement-pending-results.v1",
        "runspec_index": index["content_sha256"],
        "results": results,
    }
    (ROOT / "pending-results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
