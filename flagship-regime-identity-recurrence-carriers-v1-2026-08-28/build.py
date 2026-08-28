#!/usr/bin/env python3
"""Build two fresh flagship carriers and rebind the existing repeat/restore freeze, without inference."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PUBLISHED_COMMIT = "2763406986a907de3dcea5ee25b0fa898ef8791d"
PUBLISHED_BASE = (
    "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
    f"{PUBLISHED_COMMIT}/{ROOT.name}"
)
REPEAT_DIR = REPO / "manifest-bound-flagship-carriers-v1-2026-08-27"

REGIME_CONTEXTS = [
    ("gateway responses", "valid JSON", "interface team"),
    ("audit logs", "free of personal data", "privacy steward"),
    ("published cache entries", "immutable", "storage team"),
    ("outbound payments", "approved before release", "finance controller"),
    ("interactive requests", "completed within 200 milliseconds", "latency owner"),
    ("nightly backups", "recoverable", "continuity lead"),
    ("release artifacts", "cryptographically signed", "release custodian"),
    ("customer records", "retained for ninety days", "records officer"),
]
REGIME_FORMS = ("by-construction", "by-rule", "in-practice")
REGIME_SEAMS = ("exception_possible", "exception_consequence", "responsibility", "intent_nonclaim")

IDENTITY_CONTEXTS = [
    ("deployment configuration", "service.yaml", "parsed-field equality", "2026-08-20T09:00Z", "byte-for-byte equality"),
    ("route table", "routes-main", "rendered-route equality", "2026-08-20T10:00Z", "source-file equality"),
    ("schema document", "orders-v4", "normalised-schema equality", "2026-08-20T11:00Z", "signature equality"),
    ("policy document", "access-policy", "selected-key equality", "2026-08-20T12:00Z", "whole-document equality"),
    ("package bundle", "worker-kit", "package-name-and-version equality", "2026-08-20T13:00Z", "archive-byte equality"),
    ("query module", "invoice-query", "syntax-tree equality", "2026-08-20T14:00Z", "source-text equality"),
    ("image asset", "status-icon", "decoded-pixel equality", "2026-08-20T15:00Z", "file-byte equality"),
    ("database extract", "daily-ledger", "query-result equality", "2026-08-20T16:00Z", "database-state equality"),
]
IDENTITY_FORMS = ("same-one", "same-kind", "same-name")
IDENTITY_SEAMS = ("propagation", "relation_recovery", "later_divergence", "stronger_relation")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verify_seal(value: dict) -> None:
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected


def seal(value: dict) -> dict:
    unsigned = dict(value)
    unsigned.pop("content_sha256", None)
    unsigned["content_sha256"] = hashlib.sha256(canonical(unsigned)).hexdigest()
    return unsigned


def write(name: str, value: dict) -> dict:
    value = seal(value)
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return value


def rotate(values: list[str], offset: int) -> list[str]:
    at = offset % len(values)
    return values[at:] + values[:at]


def calibrations(prefix: str, marker: str, start: int) -> list[dict]:
    rows = []
    for index in range(12):
        bay = start + index
        answer = f"bay {bay}"
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The control note labels parcel {index + 1} {marker}({bay}), but gives no rule for {marker}.",
            "ainglish": f"Control rule: {marker}(N) means the labelled parcel is stored in bay N. The note labels parcel {index + 1} {marker}({bay}).",
            "question": "Where does the control rule place the parcel?",
            "options": rotate([answer, f"bay {bay + 1}", "dispatch desk", "not stated"], index),
            "answer": answer,
            "calibration_construct": f"target-independent {marker} location marker",
            "calibration_scope": "target-independent",
        })
    return rows


def regime_surfaces(index: int, form: str) -> tuple[str, str, str]:
    subject, property_text, owner = REGIME_CONTEXTS[index]
    common = f"Case REG-{index + 1:02d}. The registry names the {owner} as custodian."
    marked = f"{common} The {subject} are {property_text} {form}."
    if form == "by-construction":
        careful = (
            f"{common} The {subject} are {property_text} because of how the mechanism is built: "
            "while it remains unchanged, an exception cannot occur; observing one makes this claim "
            "false or shows that the mechanism changed."
        )
    elif form == "by-rule":
        careful = (
            f"{common} A standing rule requires the {subject} to be {property_text}. Exceptions can "
            f"occur; each is a violation for which the {owner} owes repair or explanation."
        )
    else:
        careful = (
            f"{common} Every observed instance of the {subject} has been {property_text} so far. "
            "Nothing in this statement prevents an exception or makes one a violation; one would be "
            "new information."
        )
    return marked, careful, owner


def regime_rows() -> tuple[list[dict], list[dict]]:
    scientific = []
    bare = []
    consequence = {
        "by-construction": "the assertion is overturned or the mechanism changed",
        "by-rule": "a duty-holder is in breach and owes remediation",
        "in-practice": "the history gains an unusual observation, with no breach",
    }
    for index, (subject, property_text, owner) in enumerate(REGIME_CONTEXTS):
        for form in REGIME_FORMS:
            marked, careful, named_owner = regime_surfaces(index, form)
            definitions = [
                (
                    "exception_possible",
                    "Could one qualifying case fail the stated property without a revision to the mechanism?",
                    ["yes", "no", "cannot determine"],
                    "no" if form == "by-construction" else "yes",
                ),
                (
                    "exception_consequence",
                    "A counterexample is later documented while implementation is unchanged. Which bookkeeping result follows?",
                    list(consequence.values()) + ["cannot determine"],
                    consequence[form],
                ),
                (
                    "responsibility",
                    "Who owes remediation solely because of the target regime claim?",
                    [f"the {named_owner}", "no party is assigned by this claim", "every observer", "cannot determine"],
                    f"the {named_owner}" if form == "by-rule" else "no party is assigned by this claim",
                ),
                (
                    "intent_nonclaim",
                    "Does the target wording itself establish that somebody deliberately chose this property?",
                    ["yes", "no", "cannot determine"],
                    "no",
                ),
            ]
            bare_text = f"Case REG-{index + 1:02d}. The registry names the {owner} as custodian. The {subject} are {property_text}."
            for seam, question, options, answer in definitions:
                row_id = f"reg-{form}-{seam}-{index + 1:02d}"
                row = {
                    "id": row_id,
                    "english": careful,
                    "ainglish": marked,
                    "question": question,
                    "options": rotate(options, index + len(form) + len(seam)),
                    "answer": answer,
                    "form": form,
                    "semantic_seam": seam,
                    "domain": subject,
                    "frame": index + 1,
                    "settlement_stratum": f"{form}.{seam}",
                }
                scientific.append(row)
                bare.append({
                    "id": row_id + "-bare",
                    "source_scientific_id": row_id,
                    "text": bare_text,
                    "question": question,
                    "options": row["options"],
                    "class_key": form,
                    "class_answer": answer,
                    "descriptive_only": True,
                })
    return scientific, bare


def identity_surfaces(index: int, form: str) -> tuple[str, str]:
    object_type, label, check, moment, _stronger = IDENTITY_CONTEXTS[index]
    common = f"Case IDN-{index + 1:02d}. Arin and Bex each use the label '{label}'."
    if form == "same-one":
        marked = f"{common} Arin and Bex edit the same-one {object_type}."
        careful = (
            f"{common} Arin and Bex reach one single {object_type} through two mentions. A modification "
            "through either mention modifies that one object and is visible through both."
        )
    elif form == "same-kind":
        marked = f"{common} Arin's {object_type} is a same-kind {object_type} to Bex's ({check}, as of {moment})."
        careful = (
            f"{common} Arin and Bex hold distinct {object_type} objects. Their content was verified equal "
            f"under {check} at {moment}; they can diverge afterward and no modification propagates."
        )
    else:
        marked = f"{common} Arin and Bex hold same-name {object_type} objects."
        careful = (
            f"{common} Arin and Bex hold distinct {object_type} objects with a matching identifier only. "
            "Content equality has not been checked or claimed."
        )
    return marked, careful


def identity_rows() -> tuple[list[dict], list[dict]]:
    scientific = []
    bare = []
    for index, (object_type, label, check, moment, stronger) in enumerate(IDENTITY_CONTEXTS):
        for form in IDENTITY_FORMS:
            marked, careful = identity_surfaces(index, form)
            relation = {
                "same-one": "one object by identity",
                "same-kind": f"distinct objects, equal only under {check} at {moment}",
                "same-name": "identifier match only; content is unverified",
            }[form]
            definitions = [
                (
                    "propagation",
                    "Arin now modifies what Arin holds. Has what Bex holds changed too?",
                    ["yes", "no", "cannot determine"],
                    "yes" if form == "same-one" else "no",
                ),
                (
                    "relation_recovery",
                    "Which relationship does the target claim establish?",
                    [
                        "one object by identity",
                        f"distinct objects, equal only under {check} at {moment}",
                        "identifier match only; content is unverified",
                        "cannot determine",
                    ],
                    relation,
                ),
                (
                    "later_divergence",
                    "Without replacing either holding, can the two holdings later differ?",
                    ["yes", "no", "cannot determine"],
                    "no" if form == "same-one" else "yes",
                ),
                (
                    "stronger_relation",
                    f"Does the target claim establish {stronger}?",
                    ["yes", "no", "cannot determine"],
                    "yes" if form == "same-one" else "no",
                ),
            ]
            bare_text = f"Case IDN-{index + 1:02d}. Arin and Bex each use the label '{label}'. Arin and Bex use the same {object_type}."
            for seam, question, options, answer in definitions:
                row_id = f"idn-{form}-{seam}-{index + 1:02d}"
                row = {
                    "id": row_id,
                    "english": careful,
                    "ainglish": marked,
                    "question": question,
                    "options": rotate(options, index + len(form) + len(seam)),
                    "answer": answer,
                    "form": form,
                    "semantic_seam": seam,
                    "domain": object_type,
                    "named_check": check,
                    "verification_moment": moment,
                    "stronger_relation": stronger,
                    "frame": index + 1,
                    "settlement_stratum": f"{form}.{seam}",
                }
                scientific.append(row)
                bare.append({
                    "id": row_id + "-bare",
                    "source_scientific_id": row_id,
                    "text": bare_text,
                    "question": question,
                    "options": row["options"],
                    "class_key": form,
                    "class_answer": answer,
                    "descriptive_only": True,
                })
    return scientific, bare


def template(name: str, slug: str, construct: str, items: list[dict], seed: int,
             snapshot_sha: str, comparator: str, diagnostic_file: str) -> dict:
    scientific = [row for row in items if not row.get("calibration")]
    strata = sorted(Counter(row["settlement_stratum"] for row in scientific))
    artifact_name = f"{name}.items.json"
    items_sha = hashlib.sha256(canonical(items)).hexdigest()
    return seal({
        "kind": "dexagon.ainglish.manifest-bound-panel-template.v1",
        "proposal_revision": slug,
        "slug": slug,
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": comparator,
        },
        "settlement_strata": [{"id": stratum, "weight": 1} for stratum in strata],
        "items": items,
        "panel": [
            {"name": "REPLACE-QUALIFIED-READER-A", "provider": "replace", "model": "replace"},
            {"name": "REPLACE-QUALIFIED-READER-B", "provider": "replace", "model": "replace"},
        ],
        "panel_neff": 2,
        "activation": {
            "runnable": False,
            "reason": "No exact eligible reader panel is bound; activation requires at least two independently qualified base-model lineages.",
            "how": "Use the generic manifest-bound activate.py after a fresh proposal/readiness check, then commit the runspec before minting and mint before the first reader call.",
        },
        "model_calls": 0,
        "governance_writes": 0,
        "construct": construct,
        "proposal_snapshot_sha256": snapshot_sha,
        "scientific_items": len(scientific),
        "calibration_items": len(items) - len(scientific),
        "settlement_design": "form x semantic seam; every equal-weight cell is load-bearing and no pooled headline can rescue one",
        "diagnostic_sidecar": {
            "file": diagnostic_file,
            "status": "frozen descriptive bare-English population; excluded from the governance metric",
            "rule": "A bare-arm default estimate cannot replace non-inferiority to complete careful English.",
        },
        "items_artifact": {
            "file": artifact_name,
            "published_url": f"{PUBLISHED_BASE}/{artifact_name}",
            "items_sha256": items_sha,
            "activation_rule": "Publish these exact bytes, then bind this HTTPS URL plus digest; never embed a mutable branch URL.",
        },
    })


def main() -> None:
    snapshot = json.loads((ROOT / "proposal-snapshot.json").read_text(encoding="utf-8"))
    verify_seal(snapshot)
    proposals = snapshot["proposals"]
    assert proposals["by-construction-by-rule-in-practice"]["form"] == "by-construction / by-rule / in-practice"
    assert proposals["same-one-same-kind-same-name"]["form"] == "same-one / same-kind / same-name"
    assert proposals["repeat-event-restore-state"]["form"].startswith("repeat-event:")

    regime_scientific, regime_bare = regime_rows()
    identity_scientific, identity_bare = identity_rows()
    regime_items = calibrations("reg", "tev", 210) + regime_scientific
    identity_items = calibrations("idn", "lur", 310) + identity_scientific

    regime_artifact = write("regime.items.json", {
        "kind": "dexagon.ainglish.flagship-comprehension-items.v1",
        "campaign": "standing-property-regime",
        "proposal_public_id": proposals["by-construction-by-rule-in-practice"]["public_id"],
        "proposal_revision": "by-construction-by-rule-in-practice",
        "scientific_items": len(regime_scientific),
        "calibration_items": 12,
        "items": regime_items,
    })
    identity_artifact = write("identity.items.json", {
        "kind": "dexagon.ainglish.flagship-comprehension-items.v1",
        "campaign": "identity-strength",
        "proposal_public_id": proposals["same-one-same-kind-same-name"]["public_id"],
        "proposal_revision": "same-one-same-kind-same-name",
        "scientific_items": len(identity_scientific),
        "calibration_items": 12,
        "items": identity_items,
    })
    write("regime-bare-diagnostic.json", {
        "kind": "dexagon.ainglish.bare-english-diagnostic-items.v1",
        "campaign": "standing-property-regime",
        "governance_metric": None,
        "items": regime_bare,
    })
    write("identity-bare-diagnostic.json", {
        "kind": "dexagon.ainglish.bare-english-diagnostic-items.v1",
        "campaign": "identity-strength",
        "governance_metric": None,
        "items": identity_bare,
    })

    regime_template = template(
        "regime",
        "by-construction-by-rule-in-practice",
        "by-construction / by-rule / in-practice",
        regime_items,
        2026082801,
        proposals["by-construction-by-rule-in-practice"]["surface_sha256"],
        "Each form versus its full current regime mapping, with exception possibility, consequence, responsibility, and intent non-claim scored separately.",
        "regime-bare-diagnostic.json",
    )
    identity_template = template(
        "identity",
        "same-one-same-kind-same-name",
        "same-one / same-kind / same-name",
        identity_items,
        2026082802,
        proposals["same-one-same-kind-same-name"]["surface_sha256"],
        "Each form versus its full current identity mapping, preserving named-check and named-moment limits and relation-laundering failures.",
        "identity-bare-diagnostic.json",
    )
    write("regime.template.json", {key: value for key, value in regime_template.items() if key != "content_sha256"})
    write("identity.template.json", {key: value for key, value in identity_template.items() if key != "content_sha256"})

    old_repeat = json.loads((REPEAT_DIR / "repeat-restore.template.json").read_text(encoding="utf-8"))
    verify_seal(old_repeat)
    old_items = json.loads((REPEAT_DIR / "repeat-restore.items.json").read_text(encoding="utf-8"))
    assert old_items["sha256"] == hashlib.sha256(canonical(old_items["items"])).hexdigest()
    assert old_items["items"] == old_repeat["items"]
    assert hashlib.sha256(canonical(old_items["items"])).hexdigest() == old_repeat["items_artifact"]["items_sha256"]
    repeat = deepcopy(old_repeat)
    repeat.pop("content_sha256")
    repeat["proposal_revision"] = "repeat-event-restore-state"
    repeat["slug"] = "repeat-event-restore-state"
    repeat["proposal_snapshot_sha256"] = proposals["repeat-event-restore-state"]["surface_sha256"]
    repeat["source_template"] = {
        "path": "manifest-bound-flagship-carriers-v1-2026-08-27/repeat-restore.template.json",
        "content_sha256": old_repeat["content_sha256"],
        "operation": "metadata-only rebind from the retained pre-rename slug to the current slug; answer-bearing items unchanged",
    }
    repeat["items_artifact"]["file"] = "../manifest-bound-flagship-carriers-v1-2026-08-27/repeat-restore.items.json"
    repeat["activation"] = {
        "runnable": False,
        "reason": "No exact eligible reader panel is bound; activation requires at least two independently qualified base-model lineages.",
        "how": "Use the generic manifest-bound activate.py after a fresh proposal/readiness check, commit the runspec, then mint before spend.",
    }
    repeat_template = write("repeat-restore-current.template.json", repeat)

    outputs = {
        "regime": {
            "items": "regime.items.json",
            "items_content_sha256": regime_artifact["content_sha256"],
            "template": "regime.template.json",
            "template_content_sha256": regime_template["content_sha256"],
            "scientific": len(regime_scientific),
            "strata": len(REGIME_FORMS) * len(REGIME_SEAMS),
        },
        "identity": {
            "items": "identity.items.json",
            "items_content_sha256": identity_artifact["content_sha256"],
            "template": "identity.template.json",
            "template_content_sha256": identity_template["content_sha256"],
            "scientific": len(identity_scientific),
            "strata": len(IDENTITY_FORMS) * len(IDENTITY_SEAMS),
        },
        "repeat_restore": {
            "template": "repeat-restore-current.template.json",
            "template_content_sha256": repeat_template["content_sha256"],
            "scientific": repeat_template["scientific_items"],
            "strata": len(repeat_template["settlement_strata"]),
            "answer_bearing_items_changed": False,
        },
    }
    write("index.json", {
        "kind": "dexagon.ainglish.flagship-regime-identity-recurrence-index.v1",
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "outputs": outputs,
        "fresh_answer_bearing_items": len(regime_scientific) + len(identity_scientific),
        "reused_answer_bearing_items": repeat_template["scientific_items"],
        "model_calls": 0,
        "tokenizer_calls": 0,
        "attempt_mints": 0,
        "governance_writes": 0,
    })
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()
