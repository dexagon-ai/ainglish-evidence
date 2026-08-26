#!/usr/bin/env python3
"""Audit frozen wave-A artifacts and exercise a candidate panel with mock readers only."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load_panel(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_ainglish_panel", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import candidate panel at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def item_tuples(value: object):
    if isinstance(value, dict):
        if all(key in value for key in ("english", "ainglish", "question")):
            yield (str(value["english"]), str(value["ainglish"]), str(value["question"]))
        for child in value.values():
            yield from item_tuples(child)
    elif isinstance(value, list):
        for child in value:
            yield from item_tuples(child)


def prior_pairs() -> set[tuple[str, str, str]]:
    pairs = set()
    for path in REPO.rglob("*.json"):
        if ROOT in path.parents:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        pairs.update(item_tuples(value))
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    args = parser.parse_args()
    panel = load_panel(args.panel.resolve())
    snapshots = json.loads((ROOT / "proposal-snapshots.json").read_text(encoding="utf-8"))
    asserted_snapshot = snapshots["content_sha256"]
    unsealed_snapshot = dict(snapshots)
    unsealed_snapshot.pop("content_sha256")
    assert hashlib.sha256(canonical(unsealed_snapshot)).hexdigest() == asserted_snapshot
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    asserted_index = index["content_sha256"]
    unsealed = dict(index)
    unsealed.pop("content_sha256")
    assert hashlib.sha256(canonical(unsealed)).hexdigest() == asserted_index
    assert index["proposal_snapshot_sha256"] == snapshots["content_sha256"]
    old_pairs = prior_pairs()
    seen = set()
    summary = []

    for campaign, meta in index["campaigns"].items():
        payload = json.loads((ROOT / meta["items_path"]).read_text(encoding="utf-8"))
        items = payload["items"]
        assert hashlib.sha256(canonical(items)).hexdigest() == meta["items_sha256"] == payload["sha256"]
        real = [row for row in items if not row.get("calibration")]
        calibration = [row for row in items if row.get("calibration")]
        assert len(real) == meta["scientific_items"] == 48 and len(calibration) == 8
        pairs = {(row["english"], row["ainglish"], row["question"]) for row in real}
        assert len(pairs) == 48 and not (pairs & seen) and not (pairs & old_pairs)
        seen |= pairs
        positions = [row["options"].index(row["answer"]) for row in real]
        assert [positions.count(value) for value in range(3)] == [16, 16, 16]
        assert all(row["english"] == row["ainglish"] for row in real)
        assert all(meta["marker"] in row["english"] for row in real)

        proposal_key = meta["proposal_key"]
        surface = snapshots["proposals"][proposal_key]["surface"]
        entry_text = (ROOT / meta["entry"]["path"]).read_text(encoding="utf-8")
        assert hashlib.sha256(entry_text.encode()).hexdigest() == meta["entry"]["sha256"]
        manifest = {
            "construct": f"{campaign}-learnability-v2",
            "slug": surface["slug"],
            "form": surface["form"],
            "metric": "learnability",
            "seed": index["seed"],
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": 2,
            "panel": [{"name": "mock-reader-a"}, {"name": "mock-reader-b"}],
            "comparator": {"kind": "register-entry-learnability-v2"},
            "entry": {
                "text": entry_text,
                "sha256": meta["entry"]["sha256"],
                "source_url": "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/PENDING/" + meta["entry"]["path"],
                "proposal_revision": surface["slug"],
            },
            "items": items,
            "_dry_run": True,
        }
        assert panel._validate_learnability_v2(manifest, real, calibration)
        leaked = [dict(row) for row in calibration]
        leaked[0]["ainglish"] += f" Control entry: {meta['marker']} means the target condition."
        with contextlib.redirect_stdout(io.StringIO()):
            assert not panel._validate_learnability_v2(manifest, real, leaked)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            measurement = panel.run_panel(manifest, ask_fn=panel.dry_reader(items, manifest))
        assert measurement is not None and measurement["metric"] == "learnability"
        assert measurement["value"] == 1.0 and measurement["calibration"]["passed"] is True
        assert measurement["calibration"]["real_cold_arm"]["accuracy"] == 0.0
        assert measurement["manifest"]["real_arm_exposure"]["cells"] == len(real) * 2 * 2
        summary.append({"campaign": campaign, "items_sha256": meta["items_sha256"],
                        "mock_value": measurement["value"], "prior_exact_pair_overlap": 0})

    print(json.dumps({"status": "ok", "campaigns": summary}, indent=2))


if __name__ == "__main__":
    main()
