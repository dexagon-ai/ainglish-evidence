#!/usr/bin/env python3
"""Dry-run or execute one frozen standing-property form exactly once."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from ainglish import __version__ as sdk_version
from ainglish import panel


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "by-construction-by-rule-in-practice-mark-whether-a-standing-"
FORMS = ("by-construction", "by-rule", "in-practice")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("form", choices=FORMS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if sdk_version != "0.2.34":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.34")
    spec = json.loads((ROOT / f"runspec-{args.form}.json").read_text(encoding="utf-8"))
    if args.dry_run:
        preview = dict(spec)
        preview["_dry_run"] = True
        items, _digest = panel.fetch_items(preview["items_url"], preview["items_sha256"])
        preview["items"] = items
        result = panel.run_panel(preview, ask_fn=panel.dry_reader(items, preview))
        if result is None or panel._is_panel_refusal(result):
            raise SystemExit(1)
        print(json.dumps({
            "form": args.form,
            "reader_calls": 0,
            "items_sha256": preview["items_sha256"],
            "preview_value": result["value"],
            "answer_protocol": panel.ANSWER_PROTOCOL,
        }, indent=2))
        return
    if list(ROOT.glob(f"{args.form}.attempt-*")):
        raise SystemExit(f"REFUSING: {args.form} already has an attempt receipt")
    items, digest = panel.fetch_items(spec["items_url"], spec["items_sha256"])
    if digest != spec["items_sha256"]:
        raise SystemExit(f"REFUSING: {args.form} fetched item digest drift")
    manifest = dict(spec)
    manifest["items"] = items
    client = ainglish_client()
    proposal = client.proposal(SLUG, authenticated=True)
    readiness = proposal.get("evidence_readiness") or {}
    if proposal.get("stage") != "measured":
        raise SystemExit(f"REFUSING: live stage changed: {proposal.get('stage')} {readiness}")
    # This packet preregisters three separate construct-level forms.  The first
    # valid filing can satisfy the proposal-wide missing-evidence flag, but it
    # must not suppress the two already-frozen sibling forms.  The local
    # one-attempt-per-form receipt guard above still prevents accidental reruns.
    measurement = panel._run_preregistered_panel(
        manifest,
        spec,
        panel.ask,
        client,
        receipt_dir=str(ROOT),
        receipt_stem=args.form,
    )
    if measurement is None:
        raise SystemExit(1)
    print(json.dumps({
        "form": args.form,
        "value": measurement.get("value"),
        "value_lo": measurement.get("value_lo"),
        "value_hi": measurement.get("value_hi"),
        "arms": measurement.get("arms"),
        "calibration": measurement.get("calibration"),
        "per_member": measurement.get("per_member"),
    }, indent=2))


if __name__ == "__main__":
    main()
