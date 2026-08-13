#!/usr/bin/env python3
"""Validate an exogenous by-omission routing freeze without reader calls.

Usage:
    python validate_by_omission_routing_freeze.py UNKNOWN.json WITHHELD.json BARE.json

This checker intentionally contains no candidate scenario prose. Dexagon designed
this instrument and therefore cannot carry its primary item content under
Ainglish's register-wide control-carrier methodology. The proposal itself has no
declared evidence contract; recorded-seconder status alone is not the rule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


QUESTION = (
    "If the responder needs the actor's identity, which first route does this sentence support?"
)
AUTHOR_ROUTE = "seek disclosure or authorization through the report's author"
TRACE_ROUTE = "investigate records or traces independently of the report's author"
UNSPECIFIED_ROUTE = "the sentence does not support either route"
REAL_OPTIONS = {AUTHOR_ROUTE, TRACE_ROUTE, UNSPECIFIED_ROUTE}

DOMAINS = {"software", "data", "finance", "governance", "research", "logistics"}
FRAMES = {"incident", "audit", "handoff", "authorization"}

CALIBRATION_QUESTION = "Which identity route does the sentence explicitly direct?"
CALIBRATION_ROUTES = {
    AUTHOR_ROUTE,
    "investigate independent records or traces",
    "contact the named evidence custodian",
    "do not begin identity work for this event",
}
NO_ROUTE = "no identity route is stated"
CALIBRATION_OPTIONS = CALIBRATION_ROUTES | {NO_ROUTE}

PUBLIC_CONTAMINATION = {
    "the staging database was dropped at 03:14",
    "the embargo date moved",
    "mistakes were made",
    "the emergency credential was exported",
    "the release approval was withdrawn",
    "the supplier invoice was altered",
    "the evaluation dataset was replaced",
    "the maintenance window was moved",
    "the audit record was deleted",
}


def load(path: Path) -> tuple[list[dict], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError(f"{path}: top level must be an array of objects")
    return value, raw


def require_string(row: dict, key: str, where: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}: {key} must be a non-empty string")
    return value


def check_common_options(row: dict, expected: set[str], where: str) -> list[str]:
    options = row.get("options")
    if not isinstance(options, list) or not all(isinstance(x, str) for x in options):
        raise ValueError(f"{where}: options must be an array of strings")
    if len(options) != len(expected) or set(options) != expected:
        raise ValueError(f"{where}: options differ from the fixed option set")
    if require_string(row, "answer", where) not in options:
        raise ValueError(f"{where}: answer is absent from options")
    return options


def validate_run(rows: list[dict], marker: str) -> dict[str, dict]:
    if marker not in {"unknown", "withheld"}:
        raise ValueError(marker)
    real = [row for row in rows if row.get("calibration") is not True]
    calibration = [row for row in rows if row.get("calibration") is True]
    if len(real) != 24 or len(calibration) != 8:
        raise ValueError(f"by-{marker}: expected 24 real + 8 calibration rows")

    ids = [require_string(row, "id", f"by-{marker} row") for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"by-{marker}: duplicate ids")

    expected_answer = TRACE_ROUTE if marker == "unknown" else AUTHOR_ROUTE
    scenarios: dict[str, dict] = {}
    cells = Counter()
    glosses = Counter()
    positions = Counter()
    for row in real:
        where = row["id"]
        scenario_id = require_string(row, "scenario_id", where)
        domain = require_string(row, "domain", where)
        frame = require_string(row, "frame", where)
        base = require_string(row, "base_clause", where).rstrip(". ")
        english = require_string(row, "english", where)
        ainglish = require_string(row, "ainglish", where)
        if domain not in DOMAINS or frame not in FRAMES:
            raise ValueError(f"{where}: undeclared domain/frame")
        cells[(domain, frame)] += 1
        if row.get("gloss_variant") not in {1, 2, 3, 4}:
            raise ValueError(f"{where}: gloss_variant must be 1, 2, 3, or 4")
        glosses[row["gloss_variant"]] += 1
        if require_string(row, "question", where) != QUESTION:
            raise ValueError(f"{where}: real question differs from the frozen question")
        options = check_common_options(row, REAL_OPTIONS, where)
        if row["answer"] != expected_answer:
            raise ValueError(f"{where}: incorrect route for by-{marker}")
        positions[options.index(row["answer"])] += 1
        if not ainglish.startswith(base) or not ainglish.rstrip().endswith(f"by-{marker}."):
            raise ValueError(f"{where}: Ainglish arm does not preserve base clause + marker")
        if not english.startswith(base) or "by-unknown" in english or "by-withheld" in english:
            raise ValueError(f"{where}: English arm must preserve base and contain no marker")
        if base.casefold() in PUBLIC_CONTAMINATION:
            raise ValueError(f"{where}: base clause is copied from a public example/manifest")
        if scenario_id in scenarios:
            raise ValueError(f"by-{marker}: duplicate scenario_id {scenario_id}")
        scenarios[scenario_id] = {
            "domain": domain, "frame": frame, "base_clause": base,
        }

    if cells != Counter({(domain, frame): 1 for domain in DOMAINS for frame in FRAMES}):
        raise ValueError(f"by-{marker}: real rows are not a complete 6 x 4 crossing")
    if glosses != Counter({variant: 6 for variant in range(1, 5)}):
        raise ValueError(f"by-{marker}: gloss variants must occur six times each")
    if positions != Counter({position: 8 for position in range(3)}):
        raise ValueError(f"by-{marker}: real correct-option positions must be 8/8/8")

    calibration_answers = Counter()
    for row in calibration:
        where = row["id"]
        english = require_string(row, "english", where)
        ainglish = require_string(row, "ainglish", where)
        if require_string(row, "question", where) != CALIBRATION_QUESTION:
            raise ValueError(f"{where}: calibration question differs from the contract")
        check_common_options(row, CALIBRATION_OPTIONS, where)
        answer = row["answer"]
        if answer not in CALIBRATION_ROUTES:
            raise ValueError(f"{where}: calibration answer is not a planted route")
        if english == ainglish or answer in english or answer not in ainglish:
            raise ValueError(f"{where}: not a genuine planted two-arm contrast")
        if "by-unknown" in english + ainglish or "by-withheld" in english + ainglish:
            raise ValueError(f"{where}: calibration must not contain the tested construct")
        calibration_answers[answer] += 1
    if calibration_answers != Counter({route: 2 for route in CALIBRATION_ROUTES}):
        raise ValueError(f"by-{marker}: each planted route must occur twice")
    return scenarios


def validate_bare(rows: list[dict]) -> dict[str, dict]:
    if len(rows) != 24:
        raise ValueError("bare diagnostic: expected 24 rows")
    ids = [require_string(row, "id", "bare row") for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("bare diagnostic: duplicate ids")
    scenarios = {}
    cells = Counter()
    positions = Counter()
    for row in rows:
        where = row["id"]
        scenario_id = require_string(row, "scenario_id", where)
        domain = require_string(row, "domain", where)
        frame = require_string(row, "frame", where)
        base = require_string(row, "base_clause", where).rstrip(". ")
        if domain not in DOMAINS or frame not in FRAMES:
            raise ValueError(f"{where}: undeclared domain/frame")
        cells[(domain, frame)] += 1
        if require_string(row, "text", where) != base + ".":
            raise ValueError(f"{where}: bare text must be the base clause plus a full stop")
        if require_string(row, "question", where) != QUESTION:
            raise ValueError(f"{where}: diagnostic question differs from the frozen question")
        options = check_common_options(row, REAL_OPTIONS, where)
        if row["answer"] != UNSPECIFIED_ROUTE:
            raise ValueError(f"{where}: unmarked passive must score as unspecified")
        positions[options.index(row["answer"])] += 1
        if scenario_id in scenarios:
            raise ValueError(f"bare diagnostic: duplicate scenario_id {scenario_id}")
        scenarios[scenario_id] = {
            "domain": domain, "frame": frame, "base_clause": base,
        }
    if cells != Counter({(domain, frame): 1 for domain in DOMAINS for frame in FRAMES}):
        raise ValueError("bare diagnostic: rows are not a complete 6 x 4 crossing")
    if positions != Counter({position: 8 for position in range(3)}):
        raise ValueError("bare diagnostic: correct-option positions must be 8/8/8")
    return scenarios


def digests(path: Path, rows: list[dict], raw: bytes) -> dict:
    canonical = json.dumps(
        rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return {
        "file": str(path),
        "rows": len(rows),
        "exact_file_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("unknown", type=Path)
    parser.add_argument("withheld", type=Path)
    parser.add_argument("bare", type=Path)
    args = parser.parse_args()

    unknown, unknown_raw = load(args.unknown)
    withheld, withheld_raw = load(args.withheld)
    bare, bare_raw = load(args.bare)
    u_scenarios = validate_run(unknown, "unknown")
    w_scenarios = validate_run(withheld, "withheld")
    b_scenarios = validate_bare(bare)
    if u_scenarios != w_scenarios or u_scenarios != b_scenarios:
        raise ValueError("scenario ids, domains, frames, or base clauses differ across artifacts")

    print(json.dumps({
        "valid": True,
        "reader_calls": 0,
        "attempts": 0,
        "artifacts": [
            digests(args.unknown, unknown, unknown_raw),
            digests(args.withheld, withheld, withheld_raw),
            digests(args.bare, bare, bare_raw),
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
