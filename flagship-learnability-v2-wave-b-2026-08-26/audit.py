#!/usr/bin/env python3
"""Offline digest, balance, leakage, and exact-pair novelty audit for wave B."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    return value


def triples(value: object):
    if isinstance(value, dict):
        if all(key in value for key in ("english", "ainglish", "question")):
            yield (str(value["english"]), str(value["ainglish"]), str(value["question"]))
        for child in value.values():
            yield from triples(child)
    elif isinstance(value, list):
        for child in value:
            yield from triples(child)


def prior_triples() -> set[tuple[str, str, str]]:
    found = set()
    for path in REPO.rglob("*.json"):
        if ROOT in path.parents:
            continue
        try:
            found.update(triples(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    return found


def main() -> None:
    snapshot = checked(ROOT / "proposal-snapshots.json")
    index = checked(ROOT / "index.json")
    assert index["proposal_snapshot_sha256"] == snapshot["content_sha256"]
    old = prior_triples()
    seen = set()
    report = []
    target_markers = {meta["marker"] for meta in index["campaigns"].values()}
    for campaign, meta in index["campaigns"].items():
        payload = json.loads((ROOT / meta["items_path"]).read_text(encoding="utf-8"))
        rows = payload["items"]
        assert hashlib.sha256(canonical(rows)).hexdigest() == payload["sha256"] == meta["items_sha256"]
        scientific = [row for row in rows if not row.get("calibration")]
        calibration = [row for row in rows if row.get("calibration")]
        current = {(row["english"], row["ainglish"], row["question"]) for row in scientific}
        assert len(scientific) == 48 and len(calibration) == 8 and len(current) == 48
        assert not current & old and not current & seen
        seen |= current
        assert all(row["english"] == row["ainglish"] and meta["marker"] in row["english"] for row in scientific)
        assert [sum(row["options"].index(row["answer"]) == position for row in scientific) for position in range(3)] == [16, 16, 16]
        calibration_text = "\n".join(
            "\n".join([
                row["english"], row["ainglish"], row["question"],
                *[str(option) for option in row["options"]], str(row["answer"]),
            ])
            for row in calibration
        ).lower()
        assert not any(marker.lower() in calibration_text for marker in target_markers)
        entry = (ROOT / meta["entry"]["path"]).read_text(encoding="utf-8")
        assert hashlib.sha256(entry.encode()).hexdigest() == meta["entry"]["sha256"]
        report.append({"campaign": campaign, "scientific": 48, "calibration": 8, "prior_exact_triple_overlap": 0})
    print(json.dumps({"status": "ok", "campaigns": report, "model_calls": 0, "governance_writes": 0}, indent=2))


if __name__ == "__main__":
    main()
