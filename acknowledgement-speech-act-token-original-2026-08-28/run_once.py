#!/usr/bin/env python3
"""Preregister, execute, and file the acknowledgement-pair token prerequisite."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "p-ack-as-receipt-r-p-ack-as-agreement-r"
RECEIPT = ROOT / "receipt.json"
ENCODINGS = ["cl100k_base", "o200k_base", "p50k_base"]
MODELS = [f"tiktoken/{name}" for name in ENCODINGS]
FORMS = ["receipt", "agreement"]
DOMAINS = [
    "policy",
    "contracts",
    "design_review",
    "incident_handoff",
    "safety_instructions",
    "workplace_coordination",
]
SETTLEMENT_STRATA = [{"id": form, "weight": 1} for form in FORMS]


# Fourteen principal/reference pairs per domain. Each becomes two cells with the exact same
# P and R but opposite intended readings. This freezes the future panel surface before any
# reader call while keeping the token prerequisite deterministic.
BASES = {
    "policy": [
        ("Legal", "policy-v3@91ac"),
        ("Privacy", "retention-rule@7f20"),
        ("Compliance", "screening-standard@2b6e"),
        ("Finance", "expense-policy@c194"),
        ("PeopleOps", "leave-guidance@45dd"),
        ("Security", "access-policy@11a8"),
        ("Governance", "delegation-rule@fe02"),
        ("Risk", "exception-process@8d31"),
        ("Audit", "records-policy@6aa4"),
        ("Procurement", "supplier-code@77c5"),
        ("Research", "disclosure-policy@3e19"),
        ("Accessibility", "caption-standard@a420"),
        ("DataOffice", "classification-rule@9cb7"),
        ("Operations", "continuity-policy@51f6"),
    ],
    "contracts": [
        ("BuyerCounsel", "msa-clause-12@0d8f"),
        ("VendorCounsel", "dpa-annex-b@be71"),
        ("Licensing", "usage-term-4@2f45"),
        ("Treasury", "payment-schedule@851c"),
        ("Insurer", "coverage-rider@0ac3"),
        ("Landlord", "lease-addendum@624e"),
        ("Publisher", "rights-schedule@73d9"),
        ("Partner", "revenue-share@142b"),
        ("Sponsor", "event-agreement@98e1"),
        ("Carrier", "service-level@5c70"),
        ("Customer", "renewal-quote@19af"),
        ("Subprocessor", "security-annex@d433"),
        ("Bank", "covenant-waiver@401d"),
        ("University", "research-licence@ea62"),
    ],
    "design_review": [
        ("Architecture", "design-rfc-208@34bc"),
        ("Frontend", "navigation-spec@219e"),
        ("Backend", "retry-contract@731a"),
        ("Database", "schema-change@c0e6"),
        ("Mobile", "offline-flow@82f9"),
        ("Identity", "oauth-sequence@9a13"),
        ("SRE", "failover-plan@4df2"),
        ("QA", "test-strategy@1b08"),
        ("UX", "consent-dialog@f612"),
        ("APIReview", "pagination-contract@55ce"),
        ("Localization", "fallback-rules@7a40"),
        ("Analytics", "event-schema@60db"),
        ("Platform", "queue-topology@e37c"),
        ("Docs", "migration-guide@2aa5"),
    ],
    "incident_handoff": [
        ("IncidentLead", "handoff-2026-08-28@8bc1"),
        ("OnCallEU", "mitigation-step-4@127d"),
        ("OnCallUS", "status-note-17@2ab4"),
        ("DatabaseLead", "recovery-checklist@731f"),
        ("NetworkLead", "routing-change@20e9"),
        ("SecurityLead", "containment-order@b56c"),
        ("SupportLead", "customer-brief@169a"),
        ("CommsLead", "public-update-3@d810"),
        ("Forensics", "evidence-index@4c27"),
        ("PaymentsOnCall", "reconciliation-plan@9f06"),
        ("CloudOps", "capacity-request@6e3a"),
        ("ServiceOwner", "rollback-decision@18c2"),
        ("DutyManager", "escalation-note@a475"),
        ("PostmortemOwner", "timeline-draft@052e"),
    ],
    "safety_instructions": [
        ("LabLead", "shutdown-procedure@6c15"),
        ("SafetyOfficer", "evacuation-card@312d"),
        ("SiteManager", "fire-watch-plan@884a"),
        ("FlightDirector", "abort-rule@2db0"),
        ("ClinicalLead", "dose-check@a157"),
        ("WorkshopLead", "lockout-step@73b8"),
        ("Facilities", "gas-isolation@c82e"),
        ("RadiationOfficer", "exposure-limit@10f3"),
        ("FieldLead", "weather-trigger@9e4b"),
        ("Marshalling", "vehicle-route@552c"),
        ("QualityLead", "quarantine-rule@e208"),
        ("RescueLead", "entry-plan@42a9"),
        ("Biosecurity", "sample-handling@7dc1"),
        ("EmergencyDesk", "shelter-order@603f"),
    ],
    "workplace_coordination": [
        ("Mira", "meeting-notes@41ad"),
        ("Owen", "budget-sheet@e720"),
        ("Priya", "launch-checklist@91bc"),
        ("Ravi", "interview-plan@056e"),
        ("Sofia", "travel-request@b2d4"),
        ("Theo", "rota-change@73af"),
        ("Uma", "training-outline@3d18"),
        ("Victor", "inventory-list@f601"),
        ("Wren", "venue-quote@2ce5"),
        ("Yasmin", "translation-brief@84a1"),
        ("Zane", "sprint-plan@9b30"),
        ("Aiko", "hiring-scorecard@44fc"),
        ("Bruno", "delivery-window@0e67"),
        ("Cleo", "publication-calendar@d518"),
    ],
}


def cell(domain: str, index: int, principal: str, reference: str, form: str) -> dict:
    common = {
        "pair_id": f"{domain}-{index:02d}",
        "domain": domain,
        "form": form,
        "principal": principal,
        "reference": reference,
        "context": f"{reference} was sent to {principal}. The status line now reads:",
        "bare": f"{principal} acknowledged {reference}.",
    }
    if form == "receipt":
        return common | {
            "ainglish": f"{principal} ack-as-receipt({reference}).",
            "english": (
                f"{principal} explicitly confirmed receipt and identification of {reference}, "
                "without expressing agreement or disagreement."
            ),
            "practical_english": f"{principal} confirmed receipt of {reference}.",
            "expected": {
                "receipt": True,
                "agreement": None,
                "disagreement": None,
                "authority": None,
                "promise_to_comply": None,
                "truth": None,
                "implementation": None,
            },
        }
    return common | {
        "ainglish": f"{principal} ack-as-agreement({reference}).",
        "english": (
            f"{principal} explicitly agreed with the content of {reference}; receipt is entailed, "
            "but authority and compliance are unasserted."
        ),
        "practical_english": f"{principal} agreed with {reference}.",
        "expected": {
            "receipt": True,
            "agreement": True,
            "disagreement": False,
            "authority": None,
            "promise_to_comply": None,
            "truth": None,
            "implementation": None,
        },
    }


TEST_SET = [
    cell(domain, index, principal, reference, form)
    for domain in DOMAINS
    for index, (principal, reference) in enumerate(BASES[domain], start=1)
    for form in FORMS
]


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def build_manifest() -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "ack-as-receipt(<R>) / ack-as-agreement(<R>)",
        "models": MODELS,
        "settlement_strata": SETTLEMENT_STRATA,
        "test_set": TEST_SET,
        "seed": "none - deterministic frozen semantic cells",
        "estimand": {
            "population": (
                "168 frozen form-balanced semantic cells: the same 84 exact principal/reference "
                "pairs rendered once per marker across six equally sized declared domains"
            ),
            "comparator": (
                "the cell's shortest careful-English expression of the proposal's complete "
                "receipt/agreement mapping; bare acknowledged and short practical-English arms "
                "are frozen for later panel and advisory price comparisons but do not set settlement"
            ),
            "aggregation": (
                "mean within receipt and agreement per tokenizer, equal weight across forms, "
                "then the least-favourable maximum tokenizer mean"
            ),
        },
        "method": (
            "For cl100k_base, o200k_base, and p50k_base under tiktoken 0.13.0, compute "
            "len(encode(ainglish)) - len(encode(english)) per cell without special tokens. "
            "Average within form, weight the two form means equally per tokenizer, and report "
            "the maximum tokenizer mean as the settlement value. Preserve per-form cells and "
            "advisory deltas against bare acknowledged and the short practical-English competitor."
        ),
        "analysis_plan": (
            "File every finite result once. Acceptance is token_delta <= +2. Token price cannot "
            "establish comprehension; the same frozen cells remain unseen by readers and retain "
            "the bare and practical-English arms for the later claim-carrier panel."
        ),
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": "source commit pushed before mint; every answer-bearing cell is generated from fixed public tables",
        },
        "environment": {
            "library": "tiktoken",
            "version": importlib.metadata.version("tiktoken"),
            "python": sys.version.split()[0],
        },
    }


def preflight(client, manifest: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    me = suggestions["sub"]
    measurements = list(proposal.get("measurements") or [])

    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not seconded")
    if (proposal.get("proposer") or {}).get("sub") == me:
        raise RuntimeError("proposer and original measurer must be different principals")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("installed tiktoken version is not 0.13.0")
    if any(row.get("metric") == "token_delta" and row.get("evidence_state") == "valid" for row in measurements):
        raise RuntimeError("a valid token_delta original already exists; stop and reassess")
    if any((row.get("submitter") or {}).get("sub") == me for row in measurements):
        raise RuntimeError("this identity already measured the proposal")

    form_counts = {form: sum(row["form"] == form for row in TEST_SET) for form in FORMS}
    domain_counts = {domain: sum(row["domain"] == domain for row in TEST_SET) for domain in DOMAINS}
    pair_forms = {}
    for row in TEST_SET:
        pair_forms.setdefault(row["pair_id"], set()).add(row["form"])
    if len(TEST_SET) != 168 or form_counts != {form: 84 for form in FORMS}:
        raise RuntimeError(f"frozen form balance failed: n={len(TEST_SET)}, forms={form_counts}")
    if domain_counts != {domain: 28 for domain in DOMAINS}:
        raise RuntimeError(f"frozen domain balance failed: {domain_counts}")
    if len(pair_forms) != 84 or any(forms != set(FORMS) for forms in pair_forms.values()):
        raise RuntimeError("each principal/reference pair must have both opposite-reading forms")
    for key in ("ainglish", "english", "practical_english"):
        values = [row[key] for row in TEST_SET]
        if len(values) != len(set(values)) or any(not value for value in values):
            raise RuntimeError(f"{key} arms are empty or non-unique")
    bare_counts = {
        value: sum(row["bare"] == value for row in TEST_SET)
        for value in {row["bare"] for row in TEST_SET}
    }
    if len(bare_counts) != 84 or set(bare_counts.values()) != {2}:
        raise RuntimeError("each opposite-reading pair must share one bare acknowledged arm")
    if any(row["ainglish"] == row["english"] for row in TEST_SET):
        raise RuntimeError("identical comparison arms found")
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean; frozen source is ambiguous")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"],
        cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return {
        "proposal_stage": proposal["stage"],
        "proposer_measurer_distinct": True,
        "existing_valid_token_rows": 0,
        "cells": len(TEST_SET),
        "paired_principal_references": len(pair_forms),
        "forms": form_counts,
        "domains": domain_counts,
        "reader_calls_before_freeze": 0,
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
    }


def mean(values: list[int]) -> float:
    return round(sum(values) / len(values), 4)


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken

    deltas: dict[str, dict[str, list[int]]] = {
        model: {"english": [], "bare": [], "practical_english": []} for model in MODELS
    }
    form_cells: dict[str, dict[str, list[int]]] = {
        model: {form: [] for form in FORMS} for model in MODELS
    }
    for encoding_name, model in zip(ENCODINGS, MODELS):
        encoding = tiktoken.get_encoding(encoding_name)
        for row in TEST_SET:
            marked_n = len(encoding.encode(row["ainglish"]))
            for comparator in deltas[model]:
                deltas[model][comparator].append(marked_n - len(encoding.encode(row[comparator])))
            form_cells[model][row["form"]].append(deltas[model]["english"][-1])

    per_form = {
        form: {model: mean(form_cells[model][form]) for model in MODELS}
        for form in FORMS
    }
    settlement_means = {
        model: round(sum(per_form[form][model] for form in FORMS) / len(FORMS), 4)
        for model in MODELS
    }
    headline_model = max(MODELS, key=lambda model: settlement_means[model])
    value = settlement_means[headline_model]
    stratum_results = [
        {
            "id": form,
            "value": per_form[form][headline_model],
            "value_lo": min(per_form[form].values()),
            "value_hi": max(per_form[form].values()),
        }
        for form in FORMS
    ]
    advisory = {
        comparator: {model: mean(deltas[model][comparator]) for model in MODELS}
        for comparator in ("bare", "practical_english")
    }
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(settlement_means.values()),
        "value_hi": max(settlement_means.values()),
        "panel_models": MODELS,
        "per_member": [{"model": model, "value": settlement_means[model]} for model in MODELS],
        "stratum_results": stratum_results,
        "manifest": manifest,
    }
    return payload, {
        "settlement_means": settlement_means,
        "per_form": per_form,
        "headline_model": headline_model,
        "stratum_results": stratum_results,
        "advisory_deltas": advisory,
        "value": value,
        "acceptance_at_most": 2,
        "acceptance_pass": value <= 2,
    }


def abort_if_open(client, attempt_id: str, detail: str, checked: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight": checked,
    }
    result = client.abort_attempt(
        attempt_id, detail[:160], receipt, failed_gate_kind="harness_error",
    )
    return {"abort_sent": True, "preflight_receipt": receipt, "result": result}


def main() -> None:
    client = ainglish_client()
    manifest = build_manifest()
    checked = preflight(client, manifest)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    if RECEIPT.exists():
        raise SystemExit(f"REFUSING: {RECEIPT.name} already exists; this run is one-shot")

    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable maximum mean token_delta across tiktoken cl100k_base, "
            "o200k_base, and p50k_base 0.13.0 on 168 frozen form-balanced semantic cells, "
            "against each cell's shortest complete careful-English mapping, with equal "
            "receipt and agreement weights."
        ),
        admissibility_gates=[
            "the proposal remains seconded and has no valid token_delta original immediately before mint",
            "the original measurer is a different principal from the proposer and has not already measured this proposal",
            "all 168 cells remain unique and balanced 84/84 across forms and 28 each across six declared domains",
            "each of 84 exact principal/reference pairs has both opposite-reading forms",
            "the answer-bearing source commit is clean and publicly reachable from origin/main before mint",
            "no reader or model has seen these cells before the immutable manifest is minted",
            "all three named tiktoken 0.13.0 resources load only after mint and return finite integer counts",
            "every finite result is filed once regardless of sign or whether the <= +2 prerequisite passes",
        ],
        planned_sample={
            "metric": "token_delta",
            "items": 168,
            "arms_scored": 2,
            "additional_frozen_arms": ["bare acknowledged", "short practical English"],
            "tokenizers": MODELS,
            "forms": {form: 84 for form in FORMS},
            "domains": {domain: 28 for domain in DOMAINS},
            "weighting": "equal within form and across forms; least-favourable tokenizer mean",
        },
    )["attempt"]
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        closure = abort_if_open(client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked)
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise

    receipt = {
        "kind": "ainglish.token-delta-original.v1",
        "proposal": SLUG,
        "attempt": opened,
        "preflight": checked,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
