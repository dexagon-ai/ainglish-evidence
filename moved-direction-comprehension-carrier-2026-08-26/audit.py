#!/usr/bin/env python3
"""Offline audit for the frozen moved-direction comprehension carrier."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from build_items import BARE_FAMILY, COMPARATORS, DOMAINS, FORMS, REPO, ROOT, build, canonical


def checked_seal(document: dict) -> None:
    value = dict(document)
    expected = value.pop("content_sha256")
    if hashlib.sha256(canonical(value)).hexdigest() != expected:
        raise SystemExit("REFUSING: sealed-document digest drift")


def rows_in(value: object):
    if isinstance(value, dict):
        if all(isinstance(value.get(key), str) for key in ("english", "ainglish", "question")):
            yield (value["english"], value["ainglish"], value["question"])
        for child in value.values():
            yield from rows_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from rows_in(child)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout


def prior_repository_rows() -> tuple[set[tuple[str, str, str]], str, int]:
    """Read the tree before this carrier was frozen, not its later descendants."""
    relative = str((ROOT / "items-moved-later-vs-careful.json").relative_to(REPO))
    additions = [
        line for line in git("log", "--diff-filter=A", "--format=%H", "--", relative).splitlines()
        if line
    ]
    if len(additions) != 1:
        raise RuntimeError("cannot identify unique carrier-addition commit")
    prior_tree = git("rev-parse", additions[0] + "^").strip()
    rows = set()
    scanned = 0
    for path in git("ls-tree", "-r", "--name-only", prior_tree).splitlines():
        if not path.endswith(".json"):
            continue
        try:
            rows.update(rows_in(json.loads(git("show", f"{prior_tree}:{path}"))))
            scanned += 1
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return rows, prior_tree, scanned


def validate_semantics(row: dict, form: str, comparator: str) -> None:
    probe = row["strata"]["probe"]
    derivation = row["derivation"]
    if row["ainglish"].count(form) != 1:
        raise SystemExit("REFUSING: marked surface occurrence drift")
    if comparator == "careful":
        direction_word = "before" if form == "moved-earlier" else "after"
        if direction_word not in row["english"]:
            raise SystemExit("REFUSING: careful comparator direction drift")
    if probe == "calendar_recovery":
        current = date.fromisoformat(derivation["current"])
        amount = timedelta(days=derivation["amount_days"])
        expected_earlier = (current - amount).isoformat()
        expected_later = (current + amount).isoformat()
        if derivation["earlier"] != expected_earlier or derivation["later"] != expected_later:
            raise SystemExit("REFUSING: calendar derivation drift")
        expected = expected_earlier if form == "moved-earlier" else expected_later
        if row["answer"] != expected or current - amount <= date(2026, 12, 1):
            raise SystemExit("REFUSING: calendar answer or future-but-earlier drift")
    elif probe == "action_consequence":
        current = datetime.strptime(derivation["current"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
        amount = timedelta(hours=derivation["amount_hours"])
        if (
            derivation["earlier"] != (current - amount).strftime("%Y-%m-%dT%H:%MZ")
            or derivation["later"] != (current + amount).strftime("%Y-%m-%dT%H:%MZ")
        ):
            raise SystemExit("REFUSING: action derivation drift")
        expected = "it will run after the occurrence" if form == "moved-earlier" else "it will run before the occurrence"
        if row["answer"] != expected:
            raise SystemExit("REFUSING: action consequence drift")
    elif row["answer"] != "no" or derivation.get("unstated_axis") != probe:
        raise SystemExit("REFUSING: over-reading answer drift")


def main() -> None:
    expected_campaigns, expected_contract, expected_index = build()
    contract = json.loads((ROOT / "proposal-contract.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    checked_seal(contract)
    checked_seal(index)
    if contract != expected_contract or index != expected_index:
        raise SystemExit("REFUSING: contract or index does not reproduce")
    loaded = {}
    for name, expected in expected_campaigns.items():
        path = ROOT / f"items-{name}.json"
        actual = json.loads(path.read_text(encoding="utf-8"))
        if actual != expected:
            raise SystemExit(f"REFUSING: {name} does not reproduce")
        rows = actual["items"]
        scientific, calibration = rows[:-8], rows[-8:]
        if hashlib.sha256(canonical(rows)).hexdigest() != actual["items_sha256"]:
            raise SystemExit(f"REFUSING: {name} row digest drift")
        if len(scientific) != 120 or len(calibration) != 8 or len({row["id"] for row in rows}) != 128:
            raise SystemExit(f"REFUSING: {name} population drift")
        if len({(row["english"], row["ainglish"], row["question"]) for row in scientific}) != 120:
            raise SystemExit(f"REFUSING: {name} duplicate scientific cells")
        if any(row["answer"] not in row["options"] or len(row["options"]) != 3 for row in rows):
            raise SystemExit(f"REFUSING: {name} answer membership drift")
        if any(row["english"] == row["ainglish"] for row in rows):
            raise SystemExit(f"REFUSING: {name} identical experimental arms")
        form, comparator = name.split("-vs-")
        if any(row["marker"] != form or row["strata"]["comparator"] != comparator for row in scientific):
            raise SystemExit(f"REFUSING: {name} routing drift")
        if {row["strata"]["domain"] for row in scientific} != {domain for domain, _ in DOMAINS}:
            raise SystemExit(f"REFUSING: {name} domain loss")
        if {row["strata"]["bare_family"] for row in scientific} != set(BARE_FAMILY):
            raise SystemExit(f"REFUSING: {name} bare-family loss")
        for row in scientific:
            validate_semantics(row, form, comparator)
        loaded[(form, comparator)] = scientific
    for comparator in COMPARATORS:
        earlier = {row["world_pair_id"]: row for row in loaded[(FORMS[0], comparator)]}
        later = {row["world_pair_id"]: row for row in loaded[(FORMS[1], comparator)]}
        if set(earlier) != set(later) or len(earlier) != 120:
            raise SystemExit("REFUSING: hidden-intent world pairing drift")
        for pair_id in earlier:
            left, right = earlier[pair_id], later[pair_id]
            if left["question"] != right["question"] or left["options"] != right["options"]:
                raise SystemExit("REFUSING: paired question or options drift")
            if comparator == "bare" and left["english"] != right["english"]:
                raise SystemExit("REFUSING: paired bare surfaces are not byte-identical")
    prior_triples, prior_tree, scanned_files = prior_repository_rows()
    current_triples = {
        (row["english"], row["ainglish"], row["question"])
        for rows in loaded.values()
        for row in rows
    }
    overlap = current_triples & prior_triples
    if overlap:
        raise SystemExit("REFUSING: scientific cells overlap a prior repository item")
    report = {
        "status": "passed",
        "model_calls": 0,
        "network_calls": 0,
        "campaigns": len(expected_campaigns),
        "scientific_rows": sum(len(payload["items"]) - 8 for payload in expected_campaigns.values()),
        "calibration_rows": 8 * len(expected_campaigns),
        "prior_json_files_scanned": scanned_files,
        "freshness_prior_tree": prior_tree,
        "prior_exact_scientific_triple_overlap": len(overlap),
        "index_sha256": index["content_sha256"],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
