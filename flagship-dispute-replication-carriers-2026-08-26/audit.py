#!/usr/bin/env python3
"""Audit fresh dispute carriers without opening target answer-bearing manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
TARGET_MARKERS = ("rather-not", "fine-either-way", "would-welcome", "this-once", "from-now-on")


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


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout


def prior_triples() -> tuple[set[tuple[str, str, str]], str, int]:
    """Read only the repository tree that preceded this carrier's first freeze."""
    relative = str((ROOT / "items-preference.json").relative_to(REPO))
    additions = [
        line for line in git("log", "--diff-filter=A", "--format=%H", "--", relative).splitlines()
        if line
    ]
    if len(additions) != 1:
        raise RuntimeError("cannot identify unique carrier-addition commit")
    prior_tree = git("rev-parse", additions[0] + "^").strip()
    found = set()
    scanned = 0
    for path in git("ls-tree", "-r", "--name-only", prior_tree).splitlines():
        if not path.endswith(".json"):
            continue
        try:
            found.update(triples(json.loads(git("show", f"{prior_tree}:{path}"))))
            scanned += 1
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return found, prior_tree, scanned


def calibration_text(rows: list[dict]) -> str:
    return "\n".join("\n".join([row["english"], row["ainglish"], row["question"], *[str(value) for value in row["options"]], str(row["answer"])]) for row in rows).lower()


def main() -> None:
    snapshots = checked(ROOT / "proposal-snapshots.json")
    index = checked(ROOT / "index.json")
    assert index["proposal_snapshot_sha256"] == snapshots["content_sha256"]
    old, prior_tree, prior_files_scanned = prior_triples()
    seen = set()
    report = []
    for name, meta in index["campaigns"].items():
        packet = json.loads((ROOT / meta["items_path"]).read_text(encoding="utf-8"))
        rows = packet["items"]
        assert hashlib.sha256(canonical(rows)).hexdigest() == packet["sha256"] == meta["items_sha256"]
        scientific = [row for row in rows if not row.get("calibration")]
        calibration = [row for row in rows if row.get("calibration")]
        current = {(row["english"], row["ainglish"], row["question"]) for row in scientific}
        assert len(scientific) == meta["scientific_items"] and len(calibration) == 8
        assert len(current) == len(scientific) and not current & old and not current & seen
        seen |= current
        assert not any(marker in calibration_text(calibration) for marker in TARGET_MARKERS)
        assert all(row["english"] != row["ainglish"] for row in scientific)
        if name == "preference":
            assert {row["form"] for row in scientific} == set(TARGET_MARKERS[:3])
            assert all(sum(row["form"] == form for row in scientific) == 96 for form in TARGET_MARKERS[:3])
            assert all(sum(row["power_stratum"] == power for row in scientific) == 96 for power in ("peer", "superior", "subordinate"))
            assert sum(row["outcome"] == "preference_recovery" for row in scientific) == 144
            assert sum(row["outcome"] == "false_obligation" for row in scientific) == 144
        else:
            assert {row["form"] for row in scientific} == set(TARGET_MARKERS[3:])
            assert sum(row["stratum"] == "core" for row in scientific) == 80
            assert sum(row["stratum"] != "core" for row in scientific) == 60
            assert all(row["scored_probe"] == "applicability" for row in scientific)
        report.append({"campaign": name, "scientific": len(scientific), "calibration": 8, "prior_exact_triple_overlap": 0, "replicates_hash": meta["replicates_hash"]})
    print(json.dumps({
        "status": "ok", "campaigns": report,
        "freshness_prior_tree": prior_tree,
        "freshness_prior_json_files_scanned": prior_files_scanned,
        "model_calls": 0, "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
