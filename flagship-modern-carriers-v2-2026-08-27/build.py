#!/usr/bin/env python3
"""Freeze five modern, form-stratified flagship comprehension carriers without inference."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PUBLISHED_COMMIT = "3fb3689bdbaf3fa38901082614d3842435cc2aa9"
PUBLISHED_BASE = (
    "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
    f"{PUBLISHED_COMMIT}/flagship-modern-carriers-v2-2026-08-27"
)


SLUGS = {
    "clusivity": "we-including-you-we-excluding-you-clusivity-mark-whether-we--4",
    "addressee": "you-one-you-all-say-whether-you-addresses-one-recipient-or-t",
    "uncertainty": "fact-not-known-choice-not-made-distinguish-missing-evidence-",
    "delegation": "no-delegation-one-hop-delegation-allowed-state-whether-a-tas",
    "collectivity": "each-alone-as-one-distributive-vs-collective-does-the-plural",
}


CONTEXTS = [
    ("audit", "verify the audit ledger", "Nia, Sol and Teo", 3, 200),
    ("release", "sign the release receipt", "Mira and Oren", 2, 350),
    ("incident", "inspect the incident trace", "Ada, Bo, Cy and Di", 4, 125),
    ("archive", "classify the archive batch", "Ivo, Jia and Kian", 3, 480),
    ("payment", "approve the payment record", "Luz and Mo", 2, 600),
    ("research", "review the research sample", "Pia, Quin, Rui, Sia and Tao", 5, 90),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def seal(value: dict) -> dict:
    unsigned = dict(value)
    unsigned.pop("content_sha256", None)
    unsigned["content_sha256"] = hashlib.sha256(canonical(unsigned)).hexdigest()
    return unsigned


def write(name: str, value: dict) -> dict:
    sealed = seal(value)
    (ROOT / name).write_text(json.dumps(sealed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"file": name, "content_sha256": sealed["content_sha256"]}


def rotate(options: list[str], n: int) -> list[str]:
    at = n % len(options)
    return options[at:] + options[:at]


def calibrations(prefix: str) -> list[dict]:
    rows = []
    for index in range(12):
        bay = 70 + index
        answer = f"bay {bay}"
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The logistics note marks parcel {index + 1} with tev({bay}), but gives no rule for tev.",
            "ainglish": f"Control rule: tev(N) means the marked parcel is stored in bay N. The logistics note marks parcel {index + 1} with tev({bay}).",
            "question": "Where does the control rule place the parcel?",
            "options": rotate([answer, f"bay {bay + 1}", "dispatch", "not stated"], index),
            "answer": answer,
            "calibration_construct": "target-independent tev location marker",
            "calibration_scope": "target-independent",
        })
    return rows


def row(prefix: str, index: int, form: str, seam: str, english: str, ainglish: str,
        question: str, options: list[str], answer: str, extra: dict | None = None) -> dict:
    value = {
        "id": f"{prefix}-{form}-{seam}-{index + 1:02d}",
        "english": english,
        "ainglish": ainglish,
        "question": question,
        "options": rotate(options, index + len(form) + len(seam)),
        "answer": answer,
        "form": form,
        "semantic_seam": seam,
        "settlement_stratum": f"{form}.{seam}",
        "frame": index + 1,
    }
    if extra:
        value.update(extra)
    return value


def clusivity() -> list[dict]:
    rows = []
    for i, (domain, action, _group, _n, _amount) in enumerate(CONTEXTS):
        case = 4100 + i
        for form, included in (("we-including-you", True), ("we-excluding-you", False)):
            careful = (f"Case {case}: We — and that includes you, the reader — will {action}."
                       if included else f"Case {case}: We, not including you, will {action}.")
            marked = f"Case {case}: {form} will {action}."
            common = {"domain": domain, "recipient_included": included}
            rows.extend([
                row("clus", i, form, "membership", careful, marked,
                    "Is the reader a member of the group denoted by the subject?",
                    ["yes", "no", "cannot tell"], "yes" if included else "no", common),
                row("clus", i, form, "tasking", careful, marked,
                    "Is the reader among the people this sentence expects to perform the action?",
                    ["yes", "no", "cannot tell"], "yes" if included else "no", common),
                row("clus", i, form, "group-size-nonclaim", careful, marked,
                    "Apart from the reader, how many other people are in the subject group?",
                    ["none", "one", "two or more", "cannot tell"], "cannot tell", common),
                row("clus", i, form, "authority-nonclaim", careful, marked,
                    "Does the subject marker itself establish that the group is authorised to do the action?",
                    ["yes", "no", "cannot tell"], "no", common),
            ])
    return rows


def addressee() -> list[dict]:
    rows = []
    for i, (domain, action, group, n, _amount) in enumerate(CONTEXTS):
        case = 4200 + i
        for form, count_answer in (("you-one", "one"), ("you-all", "every member")):
            if form == "you-one":
                careful = f"Case {case}, addressed to {group}: the one addressee identified by the direct mention must {action}."
                marked = f"Case {case}, addressed to {group} with one direct mention: you-one must {action}."
            else:
                careful = f"Case {case}, addressed to {group}: every member of this addressed group must {action}."
                marked = f"Case {case}, addressed to {group}: you-all must {action}."
            common = {"domain": domain, "addressed_group_size": n}
            rows.extend([
                row("addr", i, form, "referent-count", careful, marked,
                    "How much of the addressed group does the second-person subject denote?",
                    ["one", "every member", "no member", "cannot tell"], count_answer, common),
                row("addr", i, form, "action-count-nonclaim", careful, marked,
                    "How many separate instances of the action does the sentence require?",
                    ["one", str(n), "none", "cannot tell"], "cannot tell", common),
                row("addr", i, form, "delegation-nonclaim", careful, marked,
                    "May a denoted addressee delegate the action to another principal?",
                    ["yes", "no", "cannot tell"], "cannot tell", common),
                row("addr", i, form, "forwarding-boundary", careful, marked,
                    "If the message is forwarded tomorrow to a new reader, does that alone add the new reader to the original addressee set?",
                    ["yes", "no", "cannot tell"], "no", common),
            ])
    return rows


def uncertainty() -> list[dict]:
    rows = []
    for i, (domain, _action, group, _n, _amount) in enumerate(CONTEXTS):
        issue = f"which {domain} region applies in case {4300 + i}"
        for form in ("fact-not-known", "choice-not-made"):
            fact = form == "fact-not-known"
            if fact:
                careful = f"An existing record already determines {issue}, but the speaker lacks enough evidence to state the answer."
            else:
                careful = f"The authorised group {group} has not yet made the operative selection of {issue}."
            marked = f"{form} — {issue}."
            common = {"domain": domain, "operative_answer_exists": fact}
            rows.extend([
                row("unc", i, form, "answer-exists", careful, marked,
                    "Does an operative answer already exist at the reference time?",
                    ["yes", "no", "cannot tell"], "yes" if fact else "no", common),
                row("unc", i, form, "resolution-route", careful, marked,
                    "What kind of act closes the stated gap?",
                    ["retrieve existing evidence", "an authorised selection", "automatic implementation", "cannot tell"],
                    "retrieve existing evidence" if fact else "an authorised selection", common),
                row("unc", i, form, "reader-authority-nonclaim", careful, marked,
                    "Does the marker itself grant the reader authority to settle the issue?",
                    ["yes", "no", "cannot tell"], "no", common),
                row("unc", i, form, "diligence-nonclaim", careful, marked,
                    "Does the marker establish that the speaker searched diligently before writing it?",
                    ["yes", "no", "cannot tell"], "no", common),
            ])
    return rows


def delegation() -> list[dict]:
    rows = []
    for i, (domain, action, group, _n, _amount) in enumerate(CONTEXTS):
        case = 4400 + i
        for form in ("no-delegation", "one-hop-delegation-allowed"):
            allowed = form.startswith("one-hop")
            careful = (
                f"Case {case}: {group} must {action} without assigning any completion-bearing part to a different principal."
                if not allowed else
                f"Case {case}: {group} may assign completion-bearing work to immediate delegates, but those delegates may not delegate again; {group} remains accountable."
            )
            marked = f"Case {case}: {group} must {action}, {form}."
            common = {"domain": domain, "immediate_delegation_allowed": allowed}
            rows.extend([
                row("del", i, form, "first-hop", careful, marked,
                    "May the responsible principal assign a completion-bearing subtask to an immediate delegate?",
                    ["yes", "no", "cannot tell"], "yes" if allowed else "no", common),
                row("del", i, form, "second-hop", careful, marked,
                    "May an immediate delegate pass that assigned subtask to a further principal?",
                    ["yes", "no", "cannot tell"], "no", common),
                row("del", i, form, "accountability", careful, marked,
                    "Does the original responsible principal remain accountable to the issuer?",
                    ["yes", "no", "cannot tell"], "yes", common),
                row("del", i, form, "tool-nonclaim", careful, marked,
                    "Does this qualifier itself prohibit use of a deterministic tool controlled by the responsible principal?",
                    ["yes", "no", "cannot tell"], "no", common),
            ])
    return rows


def collectivity() -> list[dict]:
    rows = []
    for i, (domain, action, group, n, amount) in enumerate(CONTEXTS):
        for form in ("each-alone", "as-one"):
            each = form == "each-alone"
            careful = (f"{group} must each independently {action}; there are {n} separate action instances."
                       if each else f"{group} must collectively {action} as one group; there is one action instance.")
            marked = f"{group} must {action}, {form}."
            common = {"domain": domain, "members": n, "unit_amount": amount}
            rows.extend([
                row("coll", i, form, "action-count", careful, marked,
                    "How many action instances does the sentence assert?",
                    ["one", str(n), "none", "cannot tell"], str(n) if each else "one", common),
                row("coll", i, form, "amount", f"{group} receive £{amount} each, for £{amount * n} total."
                    if each else f"{group} share one £{amount} total grant.",
                    f"{group} receive £{amount}, {form}.",
                    "What total amount is asserted across the group?",
                    [f"£{amount}", f"£{amount * n}", "£0", "cannot tell"],
                    f"£{amount * n}" if each else f"£{amount}", common),
                row("coll", i, form, "timing-nonclaim", careful, marked,
                    "Does the distributive or collective marker itself require the members to act at the same time?",
                    ["yes", "no", "cannot tell"], "no", common),
                row("coll", i, form, "participation", careful, marked,
                    "Does the sentence assert that every named member performs a separate action instance?",
                    ["yes", "no", "cannot tell"], "yes" if each else "no", common),
            ])
    return rows


def template(key: str, construct: str, rows: list[dict], seed: int, remediation: bool = False) -> dict:
    strata = sorted({item["settlement_stratum"] for item in rows})
    counts = Counter(item["settlement_stratum"] for item in rows)
    assert set(counts.values()) == {6}
    items = calibrations(key) + rows
    artifact_name = f"{key}.items.json"
    items_sha = hashlib.sha256(canonical(items)).hexdigest()
    artifact = {"kind": "dexagon.ainglish.manifest-bound-panel-items.v2", "sha256": items_sha, "items": items}
    (ROOT / artifact_name).write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    value = {
        "kind": "dexagon.ainglish.manifest-bound-panel-template.v2",
        "proposal_revision": SLUGS[key],
        "slug": SLUGS[key],
        "construct": construct,
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "Every marked form is compared with its complete registered careful-English meaning; no bare or partial comparator enters the primary estimand.",
        },
        "settlement_strata": [{"id": ident, "weight": 1} for ident in strata],
        "items": items,
        "items_artifact": {
            "file": artifact_name,
            "published_url": f"{PUBLISHED_BASE}/{artifact_name}",
            "items_sha256": items_sha,
        },
        "panel": [
            {"name": "REPLACE-QUALIFIED-READER-A", "provider": "replace", "model": "replace"},
            {"name": "REPLACE-QUALIFIED-READER-B", "provider": "replace", "model": "replace"},
        ],
        "panel_neff": 2,
        "panel_neff_axis": "reader",
        "scientific_items": len(rows),
        "calibration_items": 12,
        "settlement_design": "form x semantic seam; every cell is equal-weight and load-bearing",
        "filing_mode": "fresh modern stratified original",
        "remediation": remediation,
        "activation": {
            "runnable": False,
            "reason": "The required two-lineage independently qualified reader roster remains closed at 1/2.",
            "how": "Use activate_all.py after the roster gate clears; publish its exact outputs before attempt minting or reader spend.",
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    return value


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    definitions = [
        ("clusivity", "we-including-you / we-excluding-you", clusivity(), 2026082751, False),
        ("addressee", "you-one / you-all", addressee(), 2026082752, False),
        ("uncertainty", "fact-not-known / choice-not-made", uncertainty(), 2026082753, False),
        ("delegation", "no-delegation / one-hop-delegation-allowed", delegation(), 2026082754, False),
        ("collectivity", "each-alone / as-one", collectivity(), 2026082755, True),
    ]
    outputs = {}
    for key, construct, rows, seed, remediation in definitions:
        value = template(key, construct, rows, seed, remediation)
        receipt = write(f"{key}.template.json", value)
        receipt.update({
            "construct": construct,
            "proposal_revision": SLUGS[key],
            "scientific_items": len(rows),
            "settlement_strata": len(value["settlement_strata"]),
            "items_sha256": value["items_artifact"]["items_sha256"],
            "remediation": remediation,
        })
        outputs[key] = receipt
    index = {
        "kind": "dexagon.ainglish.flagship-modern-carrier-index.v2",
        "purpose": "four site-leading candidate carriers plus one fresh each-alone/as-one instrument remediation",
        "outputs": outputs,
        "population_status": "answer-bearing bytes frozen before every reader and governance call",
        "model_calls": 0,
        "governance_writes": 0,
        "external_gates": ["server and SDK stratified settlement deployed", "two independently qualified reader lineages"],
    }
    write("index.json", index)
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
