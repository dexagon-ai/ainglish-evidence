#!/usr/bin/env python3
"""Build an explicit v2 carrier without altering the frozen v1 inputs."""

from __future__ import annotations

from copy import deepcopy
from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
V1 = REPO / "new-language-comprehension-carriers-v1-2026-08-29"
ACTIVATION_REVIEW_SHA256 = "10d3da124b5c1a8205ae0c91d9d3aa941714deae5e8c49003d7b7d2e865e5c5a"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def seal(value: dict) -> dict:
    value["content_sha256"] = hashlib.sha256(canonical(value)).hexdigest()
    return value


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256", None)
    if hashlib.sha256(canonical(unsigned)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: content digest drift at {path}")
    return value


def rotate_to(options: list[str], answer: str, target: int) -> list[str]:
    current = options.index(answer)
    shift = (current - target) % len(options)
    return options[shift:] + options[:shift]


def wrap(reference: str | None, message: str) -> str:
    return message if reference is None else f"{reference}\nMessage: {message}"


def semantic_rows(source: dict) -> list[dict]:
    rows = deepcopy(source["scientific_rows"])
    yes_no = ["yes", "no", "cannot tell"]
    for index, row in enumerate(rows):
        form = row["form"]
        additions = [
            {
                "id": "rely_on_one_satisfier",
                "question": "Does the sentence license relying on at least one member satisfying the predicate?",
                "answer": "no",
            },
            {
                "id": "n_minus_one_satisfiers",
                "question": "Is a world with exactly N-1 satisfying members compatible?",
                "answer": "yes" if form == "not-all-of" else "no",
            },
        ]
        existing = {question["id"] for question in row["questions"]}
        if existing & {addition["id"] for addition in additions}:
            raise SystemExit(f"REFUSING: v1 row already carries a v2 seam question: {row['id']}")
        for offset, addition in enumerate(additions):
            addition["options"] = rotate_to(yes_no, addition["answer"], (index + offset) % 3)
            row["questions"].append(addition)
        row["section"] = "semantic_interval"
        row["source_v1_row_id"] = row["id"]
    return rows


VALIDITY_DOMAINS = {
    "zero_shot": [
        ("mirrors", "current"),
        ("jobs", "complete"),
        ("zones", "reachable"),
        ("signatures", "valid"),
        ("channels", "open"),
        ("agents", "eligible"),
        ("checks", "passing"),
        ("records", "sealed"),
        ("devices", "online"),
        ("packages", "verified"),
    ],
    "definition_conditioned": [
        ("replicas", "healthy"),
        ("tasks", "successful"),
        ("regions", "available"),
        ("permits", "active"),
        ("routes", "clear"),
        ("reviewers", "qualified"),
        ("tests", "green"),
        ("receipts", "signed"),
        ("sensors", "calibrated"),
        ("artifacts", "reproducible"),
    ],
}


CASES = ("empty", "missing", "changing", "multiply_resolved", "fixed_receipt_epoch")


def validity_context(case: str, set_id: str, receipt: str, epoch: str, size: int) -> str:
    if case == "empty":
        return f"Receipt {receipt} records {set_id} as a fixed set with zero members at epoch {epoch}."
    if case == "missing":
        return f"Neither receipt {receipt} nor the local context resolves any set named {set_id}."
    if case == "changing":
        return (
            f"Receipt {receipt} recorded {size} members in {set_id}, membership then changed, "
            "and the claim names no epoch."
        )
    if case == "multiply_resolved":
        return f"Receipt {receipt} uses {set_id} for two distinct non-empty sets and gives no disambiguator."
    if case == "fixed_receipt_epoch":
        return f"Receipt {receipt} fixes the non-empty set {set_id} at epoch {epoch} with exactly {size} members."
    raise AssertionError(case)


def validity_rows(condition: str, reference: str | None) -> list[dict]:
    rows = []
    yes_no = ["yes", "no", "cannot tell"]
    validity_options = ["valid quantifier claim", "invalid or unresolved", "cannot tell"]
    interval_options = ["exactly zero", "zero through N-1", "no valid interval"]
    row_number = 0
    for domain_no, (set_kind, predicate) in enumerate(VALIDITY_DOMAINS[condition], 1):
        for case_no, case in enumerate(CASES, 1):
            context_id = f"validity-{condition[:1]}-{domain_no:02d}-{case_no}"
            receipt = f"R{domain_no:02d}{case_no}"
            epoch = f"E{case_no:02d}"
            set_id = f"{set_kind}-{condition[:1]}{domain_no:02d}-{case_no}"
            size = 2 + ((domain_no + case_no) % 7)
            preamble = validity_context(case, set_id, receipt, epoch, size)
            bare = f"{preamble} All members of {set_id} are not {predicate}."
            for form_no, form in enumerate(("none-of", "not-all-of")):
                row_number += 1
                marker = f"{preamble} {form}({set_id}): {predicate}."
                valid = case == "fixed_receipt_epoch"
                if valid and form == "none-of":
                    careful = f"{preamble} No member of {set_id} is {predicate}."
                    interval = "exactly zero"
                elif valid:
                    careful = (
                        f"{preamble} Fewer than all members of {set_id} are {predicate}; "
                        "zero satisfying members remains possible."
                    )
                    interval = "zero through N-1"
                else:
                    careful = (
                        f"{preamble} This use is invalid or unresolved, so it makes no quantifier "
                        f"claim about whether members are {predicate}."
                    )
                    interval = "no valid interval"
                answers = [
                    ("set_validity", "Does the named set meet the marker's fixed, non-empty, uniquely recoverable boundary?", validity_options, "valid quantifier claim" if valid else "invalid or unresolved"),
                    ("validity_interval", "Which satisfying-count interval is validly asserted?", interval_options, interval),
                    ("rely_on_one_satisfier", "Does the sentence license relying on at least one satisfying member?", yes_no, "no"),
                    ("population_overread", "Does the marker itself establish that this set is the whole population?", yes_no, "no"),
                ]
                questions = []
                for question_no, (qid, question, options, answer) in enumerate(answers):
                    questions.append({
                        "id": qid,
                        "question": question,
                        "options": rotate_to(list(options), answer, (row_number + question_no) % 3),
                        "answer": answer,
                    })
                rows.append({
                    "id": f"{context_id}-{form_no + 1}",
                    "context_id": context_id,
                    "section": "set_validity",
                    "form": form,
                    "validity_case": case,
                    "set_size": size if valid else (0 if case == "empty" else None),
                    "arms": {
                        "ainglish": wrap(reference, marker),
                        "bare_english": wrap(reference, bare),
                        "careful_english": wrap(reference, careful),
                    },
                    "questions": questions,
                    "strata": {
                        "condition": condition,
                        "section": "set_validity",
                        "domain": set_kind,
                        "predicate": predicate,
                        "form": form,
                        "validity_case": case,
                    },
                })
    if len(rows) != 100:
        raise AssertionError(len(rows))
    return rows


def packet(condition: str, source: dict, review: dict, snapshot: dict) -> dict:
    semantic = semantic_rows(source)
    validity = validity_rows(condition, source["reference_card"])
    value = {
        "kind": "dexagon.ainglish.universal-negation-comprehension-items.v2",
        "proposal_slug": snapshot["proposal"]["slug"],
        "proposal_public_id": snapshot["proposal"]["public_id"],
        "condition": condition,
        "reference_card": source["reference_card"],
        "reference_sha256": source["reference_sha256"],
        "source_v1": {
            "file": f"negation-{condition.replace('_', '-')}.json",
            "content_sha256": source["content_sha256"],
            "scientific_rows": len(source["scientific_rows"]),
        },
        "activation_review_sha256": review["content_sha256"],
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "contract": {
            "metric": "comprehension_accuracy_delta",
            "primary": "exact recovery of the asserted satisfying-count interval on valid sets",
            "comparators": {
                "confirmatory": "complete careful English",
                "diagnostic": "balanced bare all-members-are-not wording",
            },
            "support": {
                "pooled": "each form: Ainglish minus bare >= 0.20 and Ainglish minus careful >= -0.05",
                "separate_gates": [
                    "per reader lineage and condition, not-all-of zero_satisfiers accuracy >= 0.90 and no more than 0.05 below careful English",
                    "per reader lineage and condition, not-all-of rely_on_one_satisfier accuracy >= 0.90 and no more than 0.05 below careful English",
                    "per reader lineage and condition, none-of one_satisfier accuracy >= 0.90 and no more than 0.05 below careful English",
                    "per reader lineage and condition, none-of n_minus_one_satisfiers accuracy >= 0.90 and no more than 0.05 below careful English",
                    "per reader lineage and condition, population_overread accuracy >= 0.90",
                    "per reader lineage, condition, form, and invalid-set case, set_validity and validity_interval accuracy >= 0.90 and no more than 0.05 below careful English",
                    "per reader lineage, condition, and form, fixed_receipt_epoch set_validity and validity_interval accuracy >= 0.90 and no more than 0.05 below careful English",
                ],
                "no_pooled_override": True,
            },
            "vetoes": [
                "not-all-of is read as requiring one or more satisfying members",
                "none-of permits a satisfying member",
                "the marker invents whole-population coverage",
                "an empty, missing, changing, or multiply resolved set receives a vacuous quantifier truth",
                "a fixed non-empty receipt-and-epoch control is rejected",
                "calibration or two-independent-lineage qualification fails",
            ],
            "reporting": "per condition, reader lineage, section, form, validity case, domain, set size, arm, and question before any pooled summary",
        },
        "scientific_rows": semantic + validity,
        "calibration_rows": deepcopy(source["calibration_rows"]),
        "counts": {
            "semantic_rows": len(semantic),
            "validity_rows": len(validity),
            "scientific_rows": len(semantic) + len(validity),
            "calibration_rows": len(source["calibration_rows"]),
        },
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_writes": 0,
    }
    return seal(value)


def main() -> None:
    snapshot = checked(ROOT / "proposal-snapshot.json")
    review = checked(V1 / "activation-review.json")
    if review["content_sha256"] != ACTIVATION_REVIEW_SHA256 or review["disposition"] != "frozen_not_activation_ready":
        raise SystemExit("REFUSING: activation review binding drift")
    if snapshot["proposal"]["stage"] != "seconded" or snapshot["measurement_count"] != 0:
        raise SystemExit("REFUSING: snapshot is not the prospective seconded state")
    outputs = {}
    for condition in ("zero_shot", "definition_conditioned"):
        source_name = f"negation-{condition.replace('_', '-')}.json"
        source = checked(V1 / source_name)
        expected = next(row for row in review["frozen_inputs"] if row["condition"] == condition)
        if source["content_sha256"] != expected["content_sha256"]:
            raise SystemExit(f"REFUSING: reviewed v1 digest drift for {condition}")
        output_name = f"negation-{condition.replace('_', '-')}-v2.json"
        outputs[output_name] = packet(condition, source, review, snapshot)
        (ROOT / output_name).write_text(
            json.dumps(outputs[output_name], indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    index = seal({
        "kind": "dexagon.ainglish.universal-negation-carrier-index.v2",
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "activation_review_sha256": review["content_sha256"],
        "packets": [
            {
                "file": name,
                "condition": value["condition"],
                "scientific_rows": value["counts"]["scientific_rows"],
                "semantic_rows": value["counts"]["semantic_rows"],
                "validity_rows": value["counts"]["validity_rows"],
                "calibration_rows": value["counts"]["calibration_rows"],
                "content_sha256": value["content_sha256"],
            }
            for name, value in outputs.items()
        ],
        "separate_gate_count": len(next(iter(outputs.values()))["contract"]["support"]["separate_gates"]),
        "no_pooled_override": True,
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_writes": 0,
    })
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "packets": len(outputs),
        "scientific_rows": sum(row["counts"]["scientific_rows"] for row in outputs.values()),
        "content_sha256": index["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
