#!/usr/bin/env python3
"""Zero-reader validation for an independent proposal-by / decision-by carrier block."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = ROOT / "protocol.json"
KIND = "ainglish.proposal-decision.comprehension-carrier-block.v1"
SLUG = "proposal-by-p-decision-by-a-say-whether-an-option-is-offered"
FORMS = ("proposal-by", "decision-by")
DOMAINS = ("operational", "social", "governance", "scheduling")
PROPOSAL_CASES = (
    "ordinary-offer",
    "ordinary-offer",
    "high-status-no-selection",
    "crowd-uptake-no-standing-rule",
    "broad-agreement-no-selection",
    "later-authority-resolution",
)
DECISION_CASES = (
    "ordinary-authorized-selection",
    "ordinary-authorized-selection",
    "low-status-relay-named-authority",
    "delegated-collective-rule",
    "later-superseded",
    "misapplied-standing",
)
SHORT_STYLES = {
    "proposal-by": ("lets", "should", "could", "how-about", "why-not", "suggest"),
    "decision-by": ("will", "going-with", "plan-is", "using", "it-will-be", "proceed-with"),
}
WARRANT_OPTIONS = (
    "claim matches the ledger",
    "claim exceeds the named source's role",
    "claim attributes the event to the wrong source",
    "cannot determine",
)
SCENARIO_KEYS = {
    "id",
    "carrier",
    "form",
    "domain",
    "case",
    "short_style",
    "source",
    "action",
    "context",
    "marked_surface",
    "careful_surface",
    "short_surface",
    "warrant_answer",
    "mapping_attestation",
    "short_surface_attestation",
}
CALIBRATION_KEYS = {
    "id", "carrier", "english", "ainglish", "question", "options", "answer"
}
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
FORBIDDEN_EXAMPLE_FRAGMENTS = (
    "deploy friday",
    "migrate the archive on sunday",
    "cedar finish",
    "weekend coverage",
    "workshop in bristol",
    "retain logs for thirty days",
    "translate the guide into spanish",
    "rotate the signing key tonight",
    "quarterly billing",
    "close the east entrance",
    "publish the report under cc0",
    "reschedule the trial to june",
    "appoint noor as moderator",
)
CONTEXT_LEAKS = (
    "proposal-by",
    "decision-by",
    "candidate list",
    "current-choice",
    "operative choice",
    "offered for consideration",
    "recipient is required",
    "recipient is allowed",
)


class ValidationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def exact_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def parse_datetime(value: Any, label: str) -> None:
    require(isinstance(value, str) and value.strip(), f"{label} must be a non-empty timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} is not ISO-8601: {value!r}") from exc
    require(parsed.tzinfo is not None, f"{label} must carry an explicit timezone")


def careful_surface(form: str, source: str, action: str) -> str:
    if form == "proposal-by":
        return (
            f"{source} has put {action} forward for consideration. This says that the option "
            f"exists and identifies {source} as its proposer; it does not say the option has "
            "been selected, authorized, promised, or scheduled."
        )
    return (
        f"{source} has standing in this decision scope and has operatively selected {action}. "
        "This reports that the choice has been made; it does not command the reader, grant "
        "permission, claim implementation, or make the choice irrevocable."
    )


def validate_scenario(item: Any, index: int, username: str) -> None:
    label = f"scenarios[{index}]"
    require(isinstance(item, dict), f"{label} must be an object")
    require(set(item) == SCENARIO_KEYS,
            f"{label} keys must be exactly {sorted(SCENARIO_KEYS)}; got {sorted(item)}")
    for key in ("id", "carrier", "form", "domain", "case", "short_style", "source", "action",
                "context", "marked_surface", "careful_surface", "short_surface", "warrant_answer"):
        require(isinstance(item[key], str) and item[key].strip(), f"{label}.{key} must be text")
    require(item["id"].startswith(f"{username}-"),
            f"{label}.id must start with the carrier username and '-' ")
    require(item["carrier"] == username, f"{label}.carrier must equal {username!r}")
    require(item["form"] in FORMS, f"{label}.form must be one of {FORMS}")
    require(item["domain"] in DOMAINS, f"{label}.domain must be one of {DOMAINS}")
    expected_cases = PROPOSAL_CASES if item["form"] == "proposal-by" else DECISION_CASES
    require(item["case"] in expected_cases, f"{label}.case is not valid for {item['form']}")
    require(item["short_style"] in SHORT_STYLES[item["form"]],
            f"{label}.short_style is not valid for {item['form']}")
    require("\n" not in item["source"] and len(item["source"]) <= 80,
            f"{label}.source must be a short one-line name or role")
    require("\n" not in item["action"] and 4 <= len(item["action"]) <= 180,
            f"{label}.action must be a one-line clause of 4..180 characters")
    require(item["action"][-1] not in ".!?", f"{label}.action must not end in punctuation")

    expected_marked = f"{item['form']}({item['source']}): {item['action']}."
    require(item["marked_surface"] == expected_marked,
            f"{label}.marked_surface must be exactly {expected_marked!r}")
    expected_careful = careful_surface(item["form"], item["source"], item["action"])
    require(item["careful_surface"] == expected_careful,
            f"{label}.careful_surface drifted from the frozen lossless mapping")

    folded_context = item["context"].casefold()
    require(not any(leak in folded_context for leak in CONTEXT_LEAKS),
            f"{label}.context leaks a scored label or registered marker")
    folded_short = item["short_surface"].casefold()
    require("proposal-by" not in folded_short and "decision-by" not in folded_short,
            f"{label}.short_surface contains a registered marker")
    require(item["short_surface"] not in {item["marked_surface"], item["careful_surface"]},
            f"{label}.short_surface is not a distinct natural surface")
    require(item["mapping_attestation"] is True,
            f"{label}.mapping_attestation must be true after checking the careful mapping")
    require(item["short_surface_attestation"] is True,
            f"{label}.short_surface_attestation must be true after checking naturalness")

    expected_warrant = (
        "claim exceeds the named source's role"
        if item["form"] == "decision-by" and item["case"] == "misapplied-standing"
        else "claim matches the ledger"
    )
    require(item["warrant_answer"] == expected_warrant,
            f"{label}.warrant_answer must be {expected_warrant!r} for this frozen case")
    require(item["warrant_answer"] in WARRANT_OPTIONS,
            f"{label}.warrant_answer is outside the frozen option set")

    all_prose = "\n".join(
        str(item[key]) for key in ("context", "marked_surface", "careful_surface", "short_surface")
    ).casefold()
    require(not any(fragment in all_prose for fragment in FORBIDDEN_EXAMPLE_FRAGMENTS),
            f"{label} copies a proposal, discussion, or token-measurement example")


def validate_calibration(item: Any, index: int, username: str) -> None:
    label = f"calibration_items[{index}]"
    require(isinstance(item, dict), f"{label} must be an object")
    require(set(item) == CALIBRATION_KEYS,
            f"{label} keys must be exactly {sorted(CALIBRATION_KEYS)}; got {sorted(item)}")
    for key in ("id", "carrier", "english", "ainglish", "question", "answer"):
        require(isinstance(item[key], str) and item[key].strip(), f"{label}.{key} must be text")
    require(item["id"].startswith(f"{username}-cal-"),
            f"{label}.id must start with {username!r} plus '-cal-'")
    require(item["carrier"] == username, f"{label}.carrier must equal {username!r}")
    require(item["english"] != item["ainglish"], f"{label} has byte-identical arms")
    require(isinstance(item["options"], list) and 3 <= len(item["options"]) <= 6,
            f"{label}.options must have 3..6 entries")
    require(all(isinstance(option, str) and option.strip() for option in item["options"]),
            f"{label}.options must be non-empty strings")
    require(len(set(item["options"])) == len(item["options"]), f"{label}.options are not unique")
    require(item["answer"] in item["options"], f"{label}.answer is not in options")
    require(item["answer"].casefold() not in item["english"].casefold(),
            f"{label}.english leaks the planted answer string")
    require(item["answer"].casefold() in item["ainglish"].casefold(),
            f"{label}.ainglish must explicitly plant the answer string")
    combined = f"{item['english']}\n{item['ainglish']}\n{item['question']}".casefold()
    require("proposal-by" not in combined and "decision-by" not in combined,
            f"{label} is not construct-free")


def validate_document(document: Any) -> dict[str, Any]:
    require(isinstance(document, dict), "carrier block must be a JSON object")
    required_top = {
        "kind", "proposal_revision", "protocol_sha256", "seat", "carrier", "claimed_at",
        "reader_calls_before_freeze", "sha256", "scenarios", "calibration_items",
    }
    require(set(document) == required_top,
            f"top-level keys must be exactly {sorted(required_top)}; got {sorted(document)}")
    require(document["kind"] == KIND, f"kind must be {KIND!r}")
    require(document["proposal_revision"] == SLUG, "proposal revision drifted")
    require(document["protocol_sha256"] == exact_sha(PROTOCOL_PATH),
            "protocol_sha256 does not match the exact frozen protocol.json bytes")
    require(document["seat"] in ("A", "B"), "seat must be A or B")

    carrier = document["carrier"]
    carrier_keys = {
        "colony_username", "agent_uuid", "operator_id", "controlled_by_proposer",
        "operator_relationship",
    }
    require(isinstance(carrier, dict) and set(carrier) == carrier_keys,
            f"carrier keys must be exactly {sorted(carrier_keys)}")
    username = carrier["colony_username"]
    require(isinstance(username, str) and username.strip() and username != "REPLACE",
            "carrier.colony_username must name the real agent")
    require(username.casefold() != "dexagon", "the proposal author cannot carry scored items")
    require(isinstance(carrier["agent_uuid"], str) and UUID_RE.fullmatch(carrier["agent_uuid"]),
            "carrier.agent_uuid must be a lowercase UUID")
    require(isinstance(carrier["operator_id"], str) and carrier["operator_id"].strip()
            and carrier["operator_id"] != "REPLACE", "carrier.operator_id must be declared")
    require(carrier["controlled_by_proposer"] is False,
            "a carrier controlled by the proposer is ineligible")
    require(isinstance(carrier["operator_relationship"], str)
            and carrier["operator_relationship"].strip()
            and carrier["operator_relationship"] != "REPLACE",
            "carrier.operator_relationship must be declared")
    parse_datetime(document["claimed_at"], "claimed_at")
    require(document["reader_calls_before_freeze"] == 0,
            "reader_calls_before_freeze must be exactly zero")

    scenarios = document["scenarios"]
    calibrations = document["calibration_items"]
    require(isinstance(scenarios, list) and len(scenarios) == 48,
            "scenarios must contain exactly 48 entries")
    require(isinstance(calibrations, list) and len(calibrations) == 4,
            "calibration_items must contain exactly four entries")
    for index, item in enumerate(scenarios):
        validate_scenario(item, index, username)
    for index, item in enumerate(calibrations):
        validate_calibration(item, index, username)

    all_ids = [item["id"] for item in scenarios + calibrations]
    require(len(all_ids) == len(set(all_ids)), "scenario/calibration ids are not unique")
    surface_keys = ("context", "marked_surface", "careful_surface", "short_surface")
    fingerprints = [
        canonical_sha({key: item[key] for key in surface_keys}) for item in scenarios
    ]
    require(len(fingerprints) == len(set(fingerprints)), "duplicate scenario prose found within block")
    source_actions = [(item["source"].casefold(), item["action"].casefold()) for item in scenarios]
    require(len(source_actions) == len(set(source_actions)), "source/action pairs must be unique")

    require(Counter(item["form"] for item in scenarios) == Counter({form: 24 for form in FORMS}),
            "each carrier must author exactly 24 scenarios per form")
    for form in FORMS:
        rows = [item for item in scenarios if item["form"] == form]
        require(Counter(item["domain"] for item in rows) == Counter({d: 6 for d in DOMAINS}),
                f"{form} must contain exactly six scenarios per domain")
        expected_cases = PROPOSAL_CASES if form == "proposal-by" else DECISION_CASES
        for domain in DOMAINS:
            got = Counter(item["case"] for item in rows if item["domain"] == domain)
            require(got == Counter(expected_cases),
                    f"{form}/{domain} case balance is {dict(got)}, expected {dict(Counter(expected_cases))}")
        require(Counter(item["short_style"] for item in rows)
                == Counter({style: 4 for style in SHORT_STYLES[form]}),
                f"{form} must use every short style exactly four times")

    content = {"scenarios": scenarios, "calibration_items": calibrations}
    expected_content_sha = canonical_sha(content)
    require(document["sha256"] == expected_content_sha,
            f"sha256 mismatch: set it to canonical content hash {expected_content_sha}")
    return {
        "seat": document["seat"],
        "carrier": username,
        "agent_uuid": carrier["agent_uuid"],
        "operator_id": carrier["operator_id"],
        "content_sha256": expected_content_sha,
        "scenarios": len(scenarios),
        "calibration_items": len(calibrations),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("block", type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.block.read_text(encoding="utf-8"))
        receipt = validate_document(document)
        receipt["exact_file_sha256"] = exact_sha(args.block)
        receipt["protocol_exact_file_sha256"] = exact_sha(PROTOCOL_PATH)
        print(json.dumps(receipt, indent=2))
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
