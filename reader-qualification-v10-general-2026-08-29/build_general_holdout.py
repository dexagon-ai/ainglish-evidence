#!/usr/bin/env python3
"""Freeze a fresh ordinary-English holdout for two general-scope reader lineages."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
LABELS = ("entailed", "contradicted", "not determined")


def canonical(value: dict) -> bytes:
    material = copy.deepcopy(value)
    material.pop("content_sha256", None)
    return json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def cases() -> dict[str, list[tuple[str, str, str]]]:
    return {
        "quantifier_force": [
            ("Exactly thirteen of the twenty obsidian tickets were validated.", "Exactly seven obsidian tickets were not validated.", "entailed"),
            ("At least nine of the fourteen bronze sensors responded.", "Exactly nine bronze sensors responded.", "not determined"),
            ("At most three of the eleven ivory permits expired.", "Five ivory permits expired.", "contradicted"),
            ("Every one of the six saffron probes completed its check.", "At least one saffron probe did not complete its check.", "contradicted"),
            ("Between four and six of the ten cobalt channels are active, inclusive.", "At least four cobalt channels are active.", "entailed"),
            ("Exactly zero of the nine lilac submissions were rejected.", "None of the lilac submissions were rejected.", "entailed"),
            ("Fewer than five of the twelve umber steps were skipped.", "Exactly three umber steps were skipped.", "not determined"),
            ("More than eight of the ten pearl records were retained.", "Exactly seven pearl records were retained.", "contradicted"),
        ],
        "set_membership": [
            ("Every frosted vial is sterile. Vial R is frosted.", "Vial R is sterile.", "entailed"),
            ("Every amber docket is archived. Docket K is archived.", "Docket K is amber.", "not determined"),
            ("No hexagonal token is flexible. Token M is hexagonal.", "Token M is flexible.", "contradicted"),
            ("Only trained staff enter the north vault. Imani entered the north vault.", "Imani is trained staff.", "entailed"),
            ("All lunar passes are digital. Pass P is lunar. No digital pass is made of paper.", "Pass P is made of paper.", "contradicted"),
            ("Some Rowan badges are active. Neri's badge is a Rowan badge.", "Neri's badge is active.", "not determined"),
            ("Each archive in group Kestrel is encrypted. Archive V is in group Kestrel.", "Archive V is encrypted.", "entailed"),
            ("No member of set Marigold is writable. Item Q is writable.", "Item Q is a member of set Marigold.", "contradicted"),
        ],
        "negation_scope": [
            ("Not every one of the nine coral trials passed.", "At least one coral trial did not pass.", "entailed"),
            ("Zero of the seven indigo relays failed.", "One or more indigo relays failed.", "contradicted"),
            ("The maroon gate is not active.", "The maroon gate is active.", "contradicted"),
            ("The claim that zero silver beacons responded is false.", "One or more silver beacons responded.", "entailed"),
            ("Exactly two of the five topaz locks are not sealed.", "All five topaz locks are sealed.", "contradicted"),
            ("No statement says that the teal report is complete.", "The teal report is incomplete.", "not determined"),
            ("Luma did not inspect every one of the five vermilion folders.", "Luma inspected none of the vermilion folders.", "not determined"),
            ("The policy does not require an audit of the jade package.", "The policy forbids an audit of the jade package.", "not determined"),
        ],
        "disjunction": [
            ("The red channel or the gold channel is active, possibly both.", "At least one of the red and gold channels is active.", "entailed"),
            ("Exactly one of route Cedar and route Elm was selected.", "Both route Cedar and route Elm were selected.", "contradicted"),
            ("Either latch G or latch H is closed, but not both. Latch G is closed.", "Latch H is closed.", "contradicted"),
            ("One or both of mirror J and mirror K is online. Mirror J is online.", "Mirror K is online.", "not determined"),
            ("Both alpha permission and gamma permission apply.", "Alpha permission or gamma permission applies.", "entailed"),
            ("Neither the upper hatch nor the lower hatch is open.", "At least one of the upper and lower hatches is open.", "contradicted"),
            ("At least one of jobs M, N, and P succeeded.", "Job M succeeded.", "not determined"),
            ("Either lamp S or lamp T is lit. Lamp S is not lit.", "Lamp T is lit.", "entailed"),
        ],
        "conditional": [
            ("Whenever the orchid checksum matches, release Orchid proceeds. The checksum did match.", "Release Orchid proceeded.", "entailed"),
            ("Whenever a navy warning appears, process Navy stops. Process Navy stopped.", "A navy warning appeared.", "not determined"),
            ("A valid token Z always causes access Z to be granted. Access Z was denied.", "Token Z was not valid.", "entailed"),
            ("Whenever archive Plum is present, staff index it. Archive Plum is absent.", "Archive Plum is not indexed.", "not determined"),
            ("Indicator White is on exactly when circuit W has power. Indicator White is on.", "Circuit W has power.", "entailed"),
            ("Indicator Black is on exactly when circuit B has power. Circuit B lacks power.", "Indicator Black is on.", "contradicted"),
            ("Deployment Maple occurs if both approvals arrive. The first approval arrived but the second did not.", "Deployment Maple did not occur.", "not determined"),
            ("Passing audit Cyan is necessary for deployment Cyan to occur. Audit Cyan failed.", "Deployment Cyan occurred.", "contradicted"),
        ],
        "reference_resolution": [
            ("Nora compared the cedar report with the silver report. The former had fourteen pages and the latter had eight.", "The cedar report had fourteen pages.", "entailed"),
            ("Pavel compared the bronze file with the ivory file. The former had seven sections and the latter had eleven.", "The ivory file had seven sections.", "contradicted"),
            ("Tariq put a copper key in a case, sealed the case, and explicitly left the key unsealed.", "Tariq sealed the copper key.", "contradicted"),
            ("Uma informed Vela that she had received the promotion.", "Uma received the promotion.", "not determined"),
            ("Rina and Sol each filed a form. The second person's form was invalid.", "Sol filed an invalid form.", "entailed"),
            ("A parcel was placed beside a crate. It was damaged.", "The parcel was damaged.", "not determined"),
            ("Ravi handed Sol a scarlet badge and kept a blue badge. That scarlet badge expired.", "The badge handed to Sol expired.", "entailed"),
            ("After the auditor arrived, Iris spoke with June. She then departed early.", "June departed early.", "not determined"),
        ],
        "temporal_order": [
            ("The olive scan finished at 09:00, before the olive export at 11:30.", "The olive scan finished before the olive export.", "entailed"),
            ("Review Pearl ended before vote Pearl, which ended before publication.", "Review Pearl ended before publication.", "entailed"),
            ("Delivery Mauve had a Tuesday deadline but arrived the following Wednesday.", "Delivery Mauve arrived by its deadline.", "contradicted"),
            ("Migration Lime was allowed starting Thursday, yet it happened on Wednesday.", "Migration Lime obeyed its timing restriction.", "contradicted"),
            ("Audit Coral happened at an unspecified time on Monday.", "Audit Coral happened during Monday morning.", "not determined"),
            ("Backup Amber finished later than rebuild Amber.", "Rebuild Amber finished later than backup Amber.", "contradicted"),
            ("Window Violet starts later than the backup but earlier than the audit.", "The backup happens earlier than the audit.", "entailed"),
            ("Report Indigo was due on or before Friday and arrived Thursday.", "Report Indigo arrived on Friday itself.", "contradicted"),
        ],
        "authority_and_permission": [
            ("The owner role carries authority to approve release Quartz. Mira holds that role.", "Mira may approve release Quartz.", "entailed"),
            ("Reviewer Cedar may recommend a change, while owner Cedar alone makes the decision.", "A recommendation from Reviewer Cedar binds the owner.", "contradicted"),
            ("The rules expressly allow Operator S to restart service Silver.", "Operator S has permission to restart service Silver.", "entailed"),
            ("Observer Bronze may inspect the record and is forbidden from editing it.", "Observer Bronze may edit the record.", "contradicted"),
            ("Delegate Ivory may suggest an option, but Principal Ivory keeps sole decision authority.", "Delegate Ivory's suggestion is final by itself.", "contradicted"),
            ("Each jade administrator has permission to sign the release. Administrator A is a jade administrator.", "Administrator A may sign the release.", "entailed"),
            ("Kai belongs to the team. Package Plum can be released only by a team lead.", "Kai may release Package Plum.", "not determined"),
            ("Auditor Cyan was invited to give advice. The rules say nothing about who can compel changes.", "Auditor Cyan can compel a change.", "not determined"),
        ],
    }


def make_packet() -> dict:
    rows: list[dict] = []
    positions = [0, 0, 0]
    for axis_index, (axis, entries) in enumerate(cases().items()):
        if len(entries) != 8:
            raise SystemExit("REFUSING: every axis must contain eight cases")
        for item_index, (premise, hypothesis, answer) in enumerate(entries):
            position = (axis_index * 8 + item_index) % 3
            options = [label for label in LABELS if label != answer]
            options.insert(position, answer)
            positions[position] += 1
            rows.append({
                "id": f"v10g-{axis[:2]}-{item_index + 1:02d}",
                "axis": axis,
                "premise": premise,
                "hypothesis": hypothesis,
                "options": options,
                "answer": answer,
            })
    packet = {
        "kind": "ainglish.panel.reader-qualification-holdout.v8",
        "instance": "v10-general-2026-08-29",
        "scope": "general Ainglish comprehension carriers only; explicitly not eligible for restricted this-once replication work",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "answer_protocol": "opaque-entailment-choice-v1",
        "task_contract": "Given only the premise, classify the hypothesis as entailed, contradicted, or not determined.",
        "axes": list(cases()),
        "labels": list(LABELS),
        "items_per_axis": 8,
        "answer_positions": positions,
        "model_calls": 0,
        "items": rows,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    return packet


def controls() -> list[dict]:
    phrasings = (
        "Store target code {target} in the answer field.",
        "The required answer value is {target}.",
        "Copy {target} into the answer property.",
        "Return the supplied target, which is {target}.",
    )
    rows = []
    for round_number, wording in enumerate(phrasings, 1):
        for target in "ABC":
            rows.append({"id": f"format-{len(rows) + 1:02d}", "round": round_number, "target": target, "instruction": wording.format(target=target)})
    return rows


def make_plan(short: str, candidate: dict, packet: dict, gpu_minimum: int) -> dict:
    plan = {
        "kind": "ainglish.panel.reader-qualification-plan.v8",
        "instance": "v10-general-2026-08-29",
        "result_kind": "ainglish.panel.reader-qualification-result.v8",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "scope": "general Ainglish comprehension carriers only; not the restricted this-once roster",
        "phase": f"holdout-{short}",
        "freeze_rule": "Commit and push this fresh holdout, both candidate plans, runner, and static audit before either candidate call.",
        "candidate": candidate,
        "runtime": {"ollama_version": "0.32.7", "structured_output_reference": "https://docs.ollama.com/capabilities/structured-outputs"},
        "format_stage": {
            "controls": controls(),
            "gate": {"valid_json_cells_required": 12, "schema_exact_cells_required": 12, "target_correct_cells_required": 12, "thinking_bytes_required": 0, "fault_cells_required": 0},
            "failure_action": "Publish the format result and expose zero semantic holdout items.",
        },
        "semantic_stage": {
            "packet": {"file": f"{ROOT.name}/holdout.json", "content_sha256": packet["content_sha256"]},
            "prompt_contract": "Given only the ordinary-English premise, classify the hypothesis as entailed, contradicted, or not determined. Return the opaque choice code selected from the supplied mapping.",
            "gate": {"valid_json_cells_required": 64, "schema_exact_cells_required": 64, "correct_cells_required": 60, "correct_per_axis_required": 7, "correct_per_label_required": 0, "thinking_bytes_required": 0, "fault_cells_required": 0},
            "pass_meaning": "Qualified ordinary-English reader lineage for prospectively frozen general-scope Ainglish comprehension panels.",
        },
        "transport": {
            "adapter": "ollama-native-chat-json-schema-v1", "think": False, "temperature": 0,
            "seed": 2026082901, "num_ctx": 4096, "max_tokens": 16, "timeout_s": 600,
            "format": {"type": "object", "properties": {"answer": {"type": "string", "enum": ["A", "B", "C"]}}, "required": ["answer"], "additionalProperties": False},
        },
        "gpu_gate": {"ollama_base_url": "http://127.0.0.1:11434", "minimum_total_free_mib": gpu_minimum, "maximum_utilization_percent": 35},
        "result_file": f"holdout-{short}-result.json",
        "journal_file": f"holdout-{short}-attempt-journal.jsonl",
    }
    plan["content_sha256"] = hashlib.sha256(canonical(plan)).hexdigest()
    return plan


def write_frozen(path: Path, value: dict) -> None:
    rendered = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != rendered:
        raise SystemExit(f"REFUSING: frozen file drift: {path.name}")
    if not path.exists():
        path.write_text(rendered, encoding="utf-8")


def main() -> None:
    packet = make_packet()
    qwen = {
        "lineage": "Qwen 3.6 35B", "producer": "Alibaba Cloud", "source_model": "qwen3.6:35b",
        "source_manifest_sha256": "07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522",
        "capabilities": ["completion", "vision", "tools", "thinking"],
        "details": {"family": "qwen35moe", "families": ["qwen35moe"], "parameter_size": "36.0B", "quantization_level": "Q4_K_M", "format": "gguf"},
        "official_reference": "local digest-pinned Ollama qwen3.6:35b artifact",
        "eligibility_record": "reader-qualification-v8-2026-08-26/holdout-results-audit.json; qualified 61/64 on a prior fresh holdout",
        "advertised_thinking_policy": "capability allowed only with transmitted think:false and zero returned thinking bytes",
    }
    seed = {
        "lineage": "Seed-OSS 36B Instruct", "producer": "ByteDance Seed Team", "source_model": "milkey/Seed-OSS-36B-Instruct:Q4_K_M",
        "source_manifest_sha256": "7a66a2f466bf48fdafa7004a7975a7f5fac6e667a6de7d01751aacb98b3f387c",
        "capabilities": ["completion", "tools", "thinking"],
        "details": {"family": "seed_oss", "families": ["seed_oss"], "parameter_size": "36.2B", "quantization_level": "Q4_K_M", "format": "gguf"},
        "registry_reference": "https://ollama.com/milkey/Seed-OSS-36B-Instruct:Q4_K_M",
        "official_model_reference": "https://huggingface.co/ByteDance-Seed/Seed-OSS-36B-Instruct",
        "eligibility_record": "https://github.com/reticuli-labs/panel-artifacts/commit/495c75f0; development passed 24/24",
        "independence_caveat": "Community-uploaded Q4_K_M artifact; all claims bind only the exact acquired digest.",
        "advertised_thinking_policy": "capability allowed only with transmitted think:false, the manifest-bound zero-budget template, and zero returned thinking bytes",
        "template_sha256": "260bb0ab1136b500ee639cffc19703df12098b065be34071b20904538c3c26e2",
    }
    write_frozen(ROOT / "holdout.json", packet)
    write_frozen(ROOT / "holdout-qwen-plan.json", make_plan("qwen", qwen, packet, 36000))
    write_frozen(ROOT / "holdout-seed-plan.json", make_plan("seed", seed, packet, 30000))
    print(json.dumps({"holdout": packet["content_sha256"], "items": len(packet["items"]), "positions": packet["answer_positions"]}, indent=2))


if __name__ == "__main__":
    main()
