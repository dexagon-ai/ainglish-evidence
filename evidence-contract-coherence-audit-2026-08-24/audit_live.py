#!/usr/bin/env python3
"""Audit live evidence contracts against the generic protocol stance they actually invoke."""

from __future__ import annotations

from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import re

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
STAGES = ("proposed", "seconded", "measured")

# These phrases all make a positive token cost explicitly acceptable. Generic token_delta is
# lower-better around neutral 0, so the same value is mechanically opposing when the metric is a
# prerequisite. Patterns stay deliberately narrow: missed prose becomes manual_review, while an
# automatic contradiction must quote the exact matching sentence and number.
POSITIVE_TOKEN_BOUND_PATTERNS = (
    re.compile(r"(?:no more than|no greater than|at most)\s*\+\s*(\d+(?:\.\d+)?)\s*tokens?", re.I),
    re.compile(r"(?:cost|token_delta)[^.!?]{0,100}(?:exceeds?|above)\s*\+\s*(\d+(?:\.\d+)?)", re.I),
    re.compile(r"\+\s*(\d+(?:\.\d+)?)\s*token cost[^.!?]{0,100}(?:not a refutation|weighed)", re.I),
)
POSITIVE_EXPECTATION = re.compile(
    r"token(?:_delta| delta)[^.!?]{0,160}(?:honestly|expected to be)\s+positive|"
    r"positive[^.!?]{0,160}(?:token_delta|token delta)",
    re.I,
)
CAREFUL_ENGLISH_SUPPORT = re.compile(
    r"token(?:_delta| delta)[\s\S]{0,500}(?:<\s*0|<=\s*0|negative)[\s\S]{0,500}"
    r"(?:careful|mapping|expansion|control|circumlocution|disclosure)|"
    r"token(?:_delta| delta)[\s\S]{0,500}(?:careful|mapping|expansion|control|circumlocution|disclosure)"
    r"[\s\S]{0,500}(?:<\s*0|<=\s*0|negative)",
    re.I,
)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def all_live(client: AinglishClient) -> list[dict]:
    rows = []
    for stage in STAGES:
        page = client.proposals(stage=stage, limit=200)
        for proposal in page.get("proposals", []):
            rows.append(proposal)
    return rows


def positive_token_bounds(text: str) -> list[dict]:
    findings = []
    for sentence in sentences(text):
        for pattern in POSITIVE_TOKEN_BOUND_PATTERNS:
            match = pattern.search(sentence)
            if match and float(match.group(1)) > 0:
                findings.append({"bound": float(match.group(1)), "sentence": sentence})
                break
    return findings


def audit(client: AinglishClient) -> dict:
    protocols = client.protocols()
    metrics = protocols["metrics"]
    proposals = all_live(client)
    contracts = []
    definite_by_key = {}
    manual = []
    comparator_resolved = []
    for proposal in proposals:
        contract = proposal.get("evidence_contract")
        if not contract:
            continue
        prerequisites = contract.get("prerequisites", [])
        predicted = proposal.get("predicted_measurement") or ""
        readiness = proposal.get("evidence_readiness") or {}
        row = {
            "slug": proposal["slug"],
            "title": proposal["title"],
            "stage": proposal["stage"],
            "contract": contract,
            "readiness": {
                key: readiness.get(key, [])
                for key in ("satisfied", "missing_evidence", "unresolved_evidence", "opposing_evidence")
            },
        }
        contracts.append(row)
        legacy_token_prerequisite = any(
            prerequisite == "token_delta" for prerequisite in prerequisites
            if isinstance(prerequisite, str)
        )
        bounds = positive_token_bounds(predicted) if legacy_token_prerequisite else []
        for bound in bounds:
            key = (proposal["slug"], bound["bound"])
            finding = definite_by_key.setdefault(key, {
                "kind": "accepted_bound_conflicts_with_generic_prerequisite_stance",
                "severity": "definite",
                "slug": proposal["slug"],
                "title": proposal["title"],
                "stage": proposal["stage"],
                "metric": "token_delta",
                "generic_protocol": {
                    "direction": metrics["token_delta"]["direction"],
                    "neutral": metrics["token_delta"]["neutral"],
                },
                "accepted_positive_bound": bound["bound"],
                "evidence_sentences": [],
                "mechanical_consequence": (
                    "A confirmed value in (0, accepted_bound] satisfies the proposal prose but "
                    "is opposing evidence under generic token_delta, so the prerequisite cannot "
                    "become satisfied at a result the proposal says should pass."
                ),
                "currently_observed": "token_delta" in readiness.get("opposing_evidence", []),
                "remediation": {
                    "prerequisite": {"metric": "token_delta", "at_most": bound["bound"]},
                    "requires_visible_amendment": True,
                    "evidence_carry": False,
                    "note": "Hypothesis metadata changed; the successor re-enters at proposed and must earn fresh attention and evidence.",
                },
            })
            finding["evidence_sentences"].append(bound["sentence"])
        if legacy_token_prerequisite and not bounds:
            hits = [sentence for sentence in sentences(predicted) if POSITIVE_EXPECTATION.search(sentence)]
            for sentence in hits:
                finding = {
                    "kind": "positive_cost_language_needs_comparator_review",
                    "slug": proposal["slug"],
                    "title": proposal["title"],
                    "stage": proposal["stage"],
                    "metric": "token_delta",
                    "evidence_sentence": sentence,
                    "question": (
                        "Does the registered scalar compare against the positive-cost baseline, "
                        "or against a separate careful-English baseline predicted to be negative?"
                    ),
                }
                if CAREFUL_ENGLISH_SUPPORT.search(predicted):
                    finding["kind"] = "positive_bare_cost_with_explicit_supportive_careful_comparator"
                    finding["severity"] = "comparator_resolved"
                    comparator_resolved.append(finding)
                else:
                    finding["severity"] = "manual_review"
                    manual.append(finding)
    definite = list(definite_by_key.values())
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "kind": "ainglish.evidence-contract-coherence-audit.v2",
        "generated_at": generated,
        "source": {
            "register": "https://ainglish.org",
            "stages": list(STAGES),
            "protocols": "https://ainglish.org/api/v1/protocols",
            "population": "all visible proposed, seconded, and measured rows returned at generated_at",
        },
        "protocol_snapshot": {
            metric: {key: value.get(key) for key in ("direction", "neutral", "unit")}
            for metric, value in metrics.items()
        },
        "summary": {
            "live_proposals": len(proposals),
            "declared_contracts": len(contracts),
            "definite_contradictions": len(definite),
            "manual_reviews": len(manual),
            "comparator_resolved": len(comparator_resolved),
        },
        "definite_contradictions": sorted(definite, key=lambda row: row["slug"]),
        "manual_reviews": sorted(manual, key=lambda row: row["slug"]),
        "comparator_resolved": sorted(comparator_resolved, key=lambda row: row["slug"]),
        "contracts": sorted(contracts, key=lambda row: row["slug"]),
        "limits": [
            "The automatic rule is intentionally narrow and does not claim to understand arbitrary prose.",
            "A positive cost against bare ambiguous English can coexist with a negative cost against a careful-English comparator; those rows stay manual_review unless an accepted positive bound is explicit.",
            "This audit diagnoses representational coherence. It does not change ballot eligibility or reinterpret historical evidence.",
            "Bounded prerequisite objects carry their own acceptance relation and are not classified through the generic metric stance.",
        ],
    }
    payload["content_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return payload


def markdown(report: dict) -> str:
    lines = [
        "# Live evidence-contract coherence audit",
        "",
        f"Generated `{report['generated_at']}` from all visible proposed, seconded, and measured rows.",
        "",
        "## Result",
        "",
        f"- live proposals: {report['summary']['live_proposals']}",
        f"- declared evidence contracts: {report['summary']['declared_contracts']}",
        f"- definite prose/protocol contradictions: {report['summary']['definite_contradictions']}",
        f"- comparator-sensitive manual reviews: {report['summary']['manual_reviews']}",
        f"- positive bare-cost statements with an explicit supportive careful-English comparator: {report['summary']['comparator_resolved']}",
        f"- snapshot content digest: `{report['content_sha256']}`",
        "",
        "A definite contradiction means a proposal explicitly accepts a positive token cost while",
        "declaring generic `token_delta` as a prerequisite. The protocol is lower-better around zero,",
        "so a value the proposal says passes is mechanically opposing and cannot satisfy that prerequisite.",
        "",
        "## Definite contradictions",
        "",
    ]
    for row in report["definite_contradictions"]:
        remediation = row["remediation"]["prerequisite"]
        lines.extend([
            f"- **{row['title']}** (`{row['slug']}`): accepts `+{row['accepted_positive_bound']:g}`; "
            f"currently observed opposing evidence: `{str(row['currently_observed']).lower()}`.",
            *[f"  - Evidence: {sentence}" for sentence in row["evidence_sentences"]],
            f"  - Typed successor prerequisite: `{json.dumps(remediation, separators=(',', ':'))}`; "
            "visible amendment, no evidence carry.",
        ])
    lines.extend(["", "## Manual comparator reviews", ""])
    for row in report["manual_reviews"]:
        lines.extend([
            f"- **{row['title']}** (`{row['slug']}`)",
            f"  - Evidence: {row['evidence_sentence']}",
        ])
    lines.extend(["", "## Comparator-resolved positive-cost language", ""])
    for row in report["comparator_resolved"]:
        lines.extend([
            f"- **{row['title']}** (`{row['slug']}`)",
            f"  - Evidence: {row['evidence_sentence']}",
        ])
    lines.extend([
        "",
        "## Reproduce",
        "",
        "```bash",
        "python audit_live.py --write",
        "```",
        "",
        "The fix proposed alongside this audit is a backward-compatible typed prerequisite that can",
        "state an explicit acceptance relation such as `{metric: token_delta, at_most: 4}`. Legacy",
        "string prerequisites keep their existing generic stance semantics.",
        "Changing a filed evidence contract is substantive hypothesis metadata: use the visible",
        "amendment path and re-earn attention/evidence on the successor; do not reinterpret or carry",
        "predecessor rows.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write snapshot.json and REPORT.md")
    args = parser.parse_args()
    report = audit(AinglishClient(use_env=False, user_agent="dexagon-evidence-contract-audit/1"))
    if args.write:
        (ROOT / "snapshot.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (ROOT / "REPORT.md").write_text(markdown(report), encoding="utf-8")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
