#!/usr/bin/env python3
"""Preserve the completed cells as the legacy target's aggregate replication."""

from __future__ import annotations

import copy
from hashlib import sha256
import json
from pathlib import Path
import sys

from ainglish import panel as panel_harness
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402

ATTEMPT_ID = "7d585dba-0b36-404c-876c-d5acdef83d09"
ATTEMPT_MANIFEST = "3e936cea9b72cedfe62ea7e1a8a1aeb972a2fa645ca70fda9c3a42f9cd41954d"
TARGET = "b661b02842052ced7bc148b50fd4194c6084fbc27f1f70e22e45dd6af88e3d7d"
SLUG = "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2"
REQUEST = ROOT / f"runspec.attempt-{ATTEMPT_ID}.measurement.json"
RUNSPEC = ROOT / "runspec.json"
CALIBRATION = ROOT / f"runspec.attempt-{ATTEMPT_ID}.calibration.cells.json"
CELLS = ROOT / f"runspec.attempt-{ATTEMPT_ID}.cells.json"


def load_rows(path: Path) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise SystemExit(f"REFUSING: {path.name} has no row journal")
    return rows


def main() -> None:
    if (ROOT / "aggregate-result.json").exists():
        raise SystemExit("REFUSING: aggregate recovery already has a result receipt")
    original = json.loads(REQUEST.read_text(encoding="utf-8"))
    if original.get("attempt_id") != ATTEMPT_ID or original.get("replicates_hash") != TARGET:
        raise SystemExit("REFUSING: saved request is not the rejected target-bound attempt")

    # Replay from the frozen input manifest. The saved request has the rendered evidence
    # manifest, not the executable reader panel.
    manifest = copy.deepcopy(json.loads(RUNSPEC.read_text(encoding="utf-8")))
    for key in ("settlement_strata", "settlement_item_field", "settlement_rule", "content_sha256"):
        manifest.pop(key, None)
    manifest["kind"] = "dexagon.ainglish.rather-not-aggregate-compatibility-manifest.v1"
    manifest["aggregate_compatibility"] = {
        "reason": "The server refused manifest-bound stratum governance because the legacy target original declared no stratum contract.",
        "source_attempt_id": ATTEMPT_ID,
        "source_attempt_manifest_hash": ATTEMPT_MANIFEST,
        "source_measurement_request_sha256": sha256(REQUEST.read_bytes()).hexdigest(),
        "adjustment": "Remove settlement_strata, settlement_item_field and settlement_rule; replay the completed cell journal through the same SDK scorer as one aggregate. No reader call, answer, item, arm assignment, model, seed, comparator or target changed.",
        "filing_mode": "backfilled_after_preregistered_server_compatibility_refusal",
    }

    fetched_items, fetched_digest = panel_harness.fetch_items(manifest["items_url"], manifest["items_sha256"])
    manifest["items"] = fetched_items
    manifest["items_sha256"] = fetched_digest
    items = {row["id"]: row for row in fetched_items}
    replay = {}
    for row in load_rows(CALIBRATION) + load_rows(CELLS):
        item = items[row["item_id"]]
        key = (row["reader"], item[row["arm"]], item["question"], tuple(item["options"]))
        if key in replay:
            raise SystemExit("REFUSING: duplicate replay cell key")
        replay[key] = row["answer"]

    def replay_answer(endpoint, text, question, options):
        key = (endpoint["name"], text, question, tuple(options))
        if key not in replay:
            raise RuntimeError("completed cell journal does not cover the aggregate plan")
        return replay.pop(key)

    aggregate = panel_harness.run_panel(manifest, ask_fn=replay_answer)
    if aggregate is None or replay:
        raise SystemExit(f"REFUSING: aggregate replay failed or left {len(replay)} cells unused")
    if aggregate.get("stratum_results") is not None or "settlement_strata" in aggregate["manifest"]:
        raise SystemExit("REFUSING: recovery still carries an unsupported stratum contract")
    aggregate_shift_pp = float(aggregate["value"]) - float(original["value"])
    if abs(aggregate_shift_pp) > 1.0:
        raise SystemExit("REFUSING: aggregate replay changed the headline by more than one point")
    # Keep the wire manifest below the attempt-manifest size cap; the content-addressed
    # public carrier remains the manifest input.
    aggregate["manifest"].pop("items", None)
    aggregate["replicates_hash"] = TARGET

    client = ainglish_client()
    suggestions = client.suggestions()
    offered = [row for row in suggestions.get("suggestions", []) if row.get("replicates_hash") == TARGET]
    proposal = client.proposal(SLUG, authenticated=True)
    targets = [
        target
        for row in (proposal.get("evidence_readiness") or {}).get("work_items", [])
        if row.get("metric") == "comprehension_accuracy_delta"
        for target in (row.get("target_hashes") or [])
    ]
    if len(offered) != 1 or not offered[0].get("executable_now") or TARGET not in targets:
        raise SystemExit("REFUSING: fresh live state no longer offers this target")
    attempt = client.attempt(ATTEMPT_ID)
    if attempt.get("state") != "open":
        raise SystemExit("REFUSING: incompatible attempt is no longer open for an honest abort")
    abort_receipt = {
        "kind": "dexagon.ainglish.aggregate-compatibility-refusal.v1",
        "failed_gate": "server rejected stratum-bearing replication of a legacy aggregate-only original",
        "server_status": 422,
        "server_message": "This legacy original has no manifest-bound stratum contract; file an aggregate replication or start a new stratified original.",
        "reader_inference_completed": True,
        "calibration_cells": len(load_rows(CALIBRATION)),
        "scientific_cells": len(load_rows(CELLS)),
        "measurement_request_sha256": sha256(REQUEST.read_bytes()).hexdigest(),
        "recovery": "The same completed cells are replayed without inference through the aggregate scorer and filed without an attempt id, so the replacement is visibly backfilled rather than falsely presented as mint-before-spend.",
    }
    closed = client.abort_attempt(
        ATTEMPT_ID,
        "legacy target refused a stratum-bearing replication",
        abort_receipt,
        failed_gate_kind="harness_refuse",
    )
    response = client.measure(SLUG, aggregate)
    after = client.proposal(SLUG, authenticated=True)
    result = {
        "kind": "dexagon.ainglish.rather-not-aggregate-recovery-result.v1",
        "source_attempt": {"attempt_id": ATTEMPT_ID, "state": closed["attempt"]["state"]},
        "manifest_hash": manifest_commitment(aggregate["manifest"]),
        "replicates_hash": TARGET,
        "source_stratified_value": original["value"],
        "aggregate_compatibility_shift_pp": round(aggregate_shift_pp, 4),
        "value": aggregate["value"],
        "value_lo": aggregate["value_lo"],
        "value_hi": aggregate["value_hi"],
        "arms": aggregate["arms"],
        "per_member": aggregate["per_member"],
        "server_measurement": response.get("measurement"),
        "post_filing_stage": after.get("stage"),
        "post_filing_consensus": after.get("replication_consensus"),
    }
    (ROOT / "aggregate-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
