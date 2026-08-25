#!/usr/bin/env python3
"""Freeze the v6 new-lineage plan before any candidate download or inference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OPTIONS = ("yes", "no", "cannot tell")

CANDIDATES = {
    "phase-a": [
        {
            "name": "gpt-oss-20b-qualification-v6",
            "lineage": "OpenAI GPT-OSS 20B",
            "producer": "OpenAI",
            "source_model": "gpt-oss:20b",
            "source_manifest_sha256": "17052f91a42e97930aa6e28a6c6c06a983e6a58dbb00434885a0cf5313e376f7",
            "model_blob_sha256": "e7b273f9636059a689e3ddcab3716e4f65abe0143ac978e46673ad0e52d09efb",
            "model_blob_bytes": 13793422144,
            "wrapper_model": "dexagon-gpt-oss-20b-qualification-v6:ctx4k",
            "precision": "mxfp4",
            "modelfile": "Modelfile.gpt-oss",
        },
        {
            "name": "exaone3.5-32b-qualification-v6",
            "lineage": "EXAONE 3.5 32B",
            "producer": "LG AI Research",
            "source_model": "exaone3.5:32b",
            "source_manifest_sha256": "f2f69abac3dadd89fb740b06e78a529baf0295d70b7a96b48c6bb9061a7e247b",
            "model_blob_sha256": "a92c55b71e45d620cee84ed774eef6113d41c39a28bb2da562a871b288f411cf",
            "model_blob_bytes": 19343747808,
            "wrapper_model": "dexagon-exaone3.5-32b-qualification-v6:ctx4k",
            "precision": "q4_k_m",
            "modelfile": "Modelfile.exaone",
        },
    ],
    "reserve-b": [
        {
            "name": "olmo2-13b-qualification-v6",
            "lineage": "OLMo 2 13B",
            "producer": "Allen Institute for AI",
            "source_model": "olmo2:13b",
            "source_manifest_sha256": "6c279ebc980fb07ca7b49cccf17b5faef6a73082cac4b3d44d2226981de676da",
            "model_blob_sha256": "cd836509a1a051178be134eba84115eb3a6653a1bd58473a706bf8ee4ab3a764",
            "model_blob_bytes": 8354349536,
            "wrapper_model": "dexagon-olmo2-13b-qualification-v6:ctx4k",
            "precision": "q4_k_m",
            "modelfile": "Modelfile.olmo",
        },
        {
            "name": "falcon3-10b-qualification-v6",
            "lineage": "Falcon 3 10B",
            "producer": "Technology Innovation Institute",
            "source_model": "falcon3:10b",
            "source_manifest_sha256": "1653ff122acd9292fe21a097c0f08ce419439be595b312d6d6d06ee33df91b88",
            "model_blob_sha256": "c8647169c2b98160c1be33a2e4faa2130bcc5d1c70100ce1e5d159f0448663c6",
            "model_blob_bytes": 6287519808,
            "wrapper_model": "dexagon-falcon3-10b-qualification-v6:ctx4k",
            "precision": "q4_k_m",
            "modelfile": "Modelfile.falcon",
        },
    ],
    "final-reserve": [
        {
            "name": "glm4-9b-qualification-v6",
            "lineage": "GLM-4 9B",
            "producer": "THUDM",
            "source_model": "glm4:9b",
            "source_manifest_sha256": "5b699761eca535dc55047ad9d2dbf54e3b8697709419ef78a70503ed4bfbcf44",
            "model_blob_sha256": "b506a070d1152798d435ec4e7687336567ae653b3106f73b7b4ac7be1cbc4449",
            "model_blob_bytes": 5455319040,
            "wrapper_model": "dexagon-glm4-9b-qualification-v6:ctx4k",
            "precision": "q4_0",
            "modelfile": "Modelfile.glm",
        },
    ],
}

ROWS = {
    "quantifier_force": [
        ("At least seven of the ten relays responded.", "Could exactly six relays have responded?", "no"),
        ("No more than four of the nine reviewers objected.", "Could exactly three reviewers have objected?", "yes"),
        ("Exactly five of the thirteen permits were renewed.", "Were exactly eight permits not renewed?", "yes"),
        ("Each of the six probes completed its check.", "Did any probe fail to complete its check?", "no"),
        ("None of the eight tokens opened the cabinet.", "Did any listed token open the cabinet?", "no"),
        ("More than half of the nine members voted in favour.", "Must at least five members have voted in favour?", "yes"),
        ("All except two of the twelve uploads succeeded.", "Did exactly ten uploads succeed?", "yes"),
        ("Several containers were inspected, but the total number is not stated.", "Does the sentence establish that every container was inspected?", "no"),
    ],
    "set_membership": [
        ("The complete response team is Asha, Bram, and the reader of this message.", "Is the reader on the response team?", "yes"),
        ("Only Cora and Dev possess signing keys.", "Does Enzo possess a signing key?", "no"),
        ("Every silver-badge holder may enter. Fara has a silver badge.", "May Fara enter?", "yes"),
        ("Only auditors may certify a ledger. Gil certified the ledger under this rule.", "Is Gil an auditor?", "yes"),
        ("The note identifies Hana and Inez as members but says the membership list is incomplete.", "Is Jori a member?", "cannot tell"),
        ("The supported export formats are CSV and JSON, with no others supported.", "Is XML supported?", "no"),
        ("Everyone in group K received a badge. Lio belongs to group K.", "Did Lio receive a badge?", "yes"),
        ("Mara received a badge. The record does not state who belongs to group K.", "Does Mara belong to group K?", "cannot tell"),
    ],
    "negation_scope": [
        ("Not every one of the ten checks passed.", "Did at least one check fail?", "yes"),
        ("No approved task was late.", "Was any approved task late?", "no"),
        ("It is false that both services are active.", "Are both services active?", "no"),
        ("The policy does not require archiving the draft.", "Does that sentence impose a duty to archive the draft?", "no"),
        ("None of the listed badges grants roof access.", "Does any listed badge grant roof access?", "no"),
        ("The endpoint is not inaccessible.", "Is the endpoint inaccessible?", "no"),
        ("Niko did not agree to inspect every parcel.", "Did Niko agree to inspect no parcels?", "cannot tell"),
        ("It is not true that any of the four seals failed.", "Did at least one seal fail?", "no"),
    ],
    "disjunction": [
        ("Select amber or violet, but not both.", "May both colours be selected?", "no"),
        ("Send the alert by email, text message, or both.", "May both channels be used?", "yes"),
        ("At least one of test P or test Q must pass, and both are allowed to pass.", "May both tests pass?", "yes"),
        ("Exactly one of the two nodes will become leader.", "May neither node become leader?", "no"),
        ("Save the copy locally or remotely. No exclusivity condition is stated.", "Does the sentence establish that saving in both places is forbidden?", "no"),
        ("Use either route, including both routes if useful.", "May both routes be used?", "yes"),
        ("The defect is in the processor or the memory; the report makes no exclusivity claim.", "Must exactly one component be defective?", "no"),
        ("Choose one of oak, pine, or yew, and choose no more than one.", "May two kinds be chosen?", "no"),
    ],
    "conditional": [
        ("If the sensor is wet, sound the alarm. The sensor is wet.", "Should the alarm sound?", "yes"),
        ("If the test passes, deploy the build. The build was deployed.", "Must the test have passed?", "cannot tell"),
        ("Do not release the package unless it is signed. It is unsigned.", "Should the package be released?", "no"),
        ("A visitor may enter only if they have a badge. This visitor has no badge.", "May this visitor enter?", "no"),
        ("Rotate the credential only when both approvals exist. One approval is missing.", "Should the credential be rotated?", "no"),
        ("Whenever the heartbeat stops, page the on-call engineer. The heartbeat stopped.", "Should the engineer be paged?", "yes"),
        ("If the backup is fresh, restore it. The backup is stale.", "Does the sentence establish that restoration must not occur?", "cannot tell"),
        ("Ship the parcel only provided that payment has cleared. Payment has not cleared.", "May the parcel be shipped under this rule?", "no"),
    ],
    "reference_resolution": [
        ("Oren gave Pema the blue folder. Pema stored the blue folder in the safe.", "Did Pema store the blue folder?", "yes"),
        ("Riva told Sela that she would present the findings.", "Does the sentence unambiguously say Riva will present?", "no"),
        ("The relay restarted the gateway because the relay had overheated.", "Had the relay overheated?", "yes"),
        ("I attached the map to the schedule. The former is outdated.", "Is the map outdated?", "yes"),
        ("The black case is beside the silver case. The note says the silver case is locked.", "Is the black case stated to be locked?", "no"),
        ("Tari emailed Uma after Tari signed the receipt.", "Did Tari sign the receipt?", "yes"),
        ("Vik put the brush beside the cup and then washed it.", "Is the washed object unambiguous?", "no"),
        ("Wren lent Xavi the tablet. Xavi returned the tablet this morning.", "Did Xavi return the tablet?", "yes"),
    ],
    "temporal_order": [
        ("The contract was approved before it was published.", "Was it published before it was approved?", "no"),
        ("After the siren stopped, the workers entered.", "Did the siren stop before the workers entered?", "yes"),
        ("The key and the log arrived on Monday; their order is not recorded.", "Did the key arrive first?", "cannot tell"),
        ("Yara copied the file and then erased the original.", "Did copying happen before erasure?", "yes"),
        ("The inspection must finish by Wednesday.", "Could a Thursday finish satisfy that deadline?", "no"),
        ("The session starts at 14:00 and lasts three hours.", "Is it still running at 16:00?", "yes"),
        ("Zane repaired the unit while Ada calibrated the meter.", "Does the sentence establish which activity began first?", "cannot tell"),
        ("The seal was placed immediately before dispatch.", "Was the seal placed first?", "yes"),
    ],
    "authority_and_permission": [
        ("The policy allows operators to restart the service.", "Are operators permitted to restart it?", "yes"),
        ("The robot is capable of opening the vault, but no permission is stated.", "Does the sentence grant the robot permission to open it?", "no"),
        ("The rule obliges Bela to countersign the report.", "Does Bela have a duty to countersign it?", "yes"),
        ("The forecast predicts that Cian will arrive, and no rule applies.", "Does the forecast impose a duty on Cian to arrive?", "no"),
        ("The manager did not object, and the policy says nothing about the action.", "Does the absence of an objection itself grant permission?", "no"),
        ("Only the custodian may revoke a credential. Dena is not the custodian.", "May Dena revoke it?", "no"),
        ("Eren is expressly authorised to access the archive.", "Is Eren allowed to access it?", "yes"),
        ("Fio might finish tonight. The message contains no rule or instruction.", "Does the message require Fio to finish tonight?", "no"),
    ],
}

PRIOR_SPECS = [
    "reader-qualification-tournament-2026-08-23/spec.json",
    "reader-qualification-v2-2026-08-24/development.json",
    "reader-qualification-v2-2026-08-24/holdout.json",
    "reader-qualification-v3-2026-08-24/development.json",
    "reader-qualification-v3-2026-08-24/development-tuned.json",
    "reader-qualification-v3-2026-08-24/holdout.json",
    "reader-qualification-v4-2026-08-24/development.json",
    "reader-qualification-v4-2026-08-24/development-tuned.json",
    "reader-qualification-v4-2026-08-24/holdout.json",
    "reader-qualification-v5-2026-08-25/phase-a-holdout.json",
    "reader-qualification-v5-2026-08-25/reserve-holdout.json",
    "reader-qualification-v5-2026-08-25/phi-reserve-holdout.json",
]

FORBIDDEN_TERMS = [
    "ainglish", "proxy(", "obs:", "inf:", "rep(", "must-as-", "should-as-",
    "will-as-", "may-not-as-", "all-or-nothing", "keep-successes",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def choices(answer: str, position: int) -> list[str]:
    others = [value for value in OPTIONS if value != answer]
    out = list(others)
    out.insert(position, answer)
    return out


def item_fingerprint(row: dict) -> str:
    return hashlib.sha256(canonical({
        "message": row["message"],
        "question": row["question"],
        "options": sorted(row["options"]),
    })).hexdigest()


def validate_novel_candidates() -> None:
    needles = [row["source_model"].casefold() for phase in CANDIDATES.values() for row in phase]
    for path in REPO.rglob("*"):
        if not path.is_file() or ROOT in path.parents or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix not in {".py", ".md", ".json", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8").casefold()
        except UnicodeDecodeError:
            continue
        for needle in needles:
            if needle in text:
                raise SystemExit(f"REFUSING: candidate {needle} already appears in {path.relative_to(REPO)}")


def main() -> None:
    target = ROOT / "plan.json"
    if target.exists():
        raise SystemExit("REFUSING: plan.json already exists")
    validate_novel_candidates()
    items = []
    for axis, rows in ROWS.items():
        if len(rows) != 8:
            raise SystemExit(f"REFUSING: {axis} does not contain eight items")
        for index, (message, question, answer) in enumerate(rows):
            item = {
                "id": f"v6-hold-{axis}-{index + 1:02d}",
                "axis": axis,
                "message": message,
                "question": question,
                "options": choices(answer, len(items) % 3),
                "answer": answer,
            }
            items.append(item)
    if len(items) != 64 or len({row["id"] for row in items}) != 64:
        raise SystemExit("REFUSING: v6 item count or identity drift")
    forbidden = [term.casefold() for term in FORBIDDEN_TERMS]
    for row in items:
        if any(term in json.dumps(row, ensure_ascii=False).casefold() for term in forbidden):
            raise SystemExit(f"REFUSING: construct leak in {row['id']}")
    prior = set()
    for relative in PRIOR_SPECS:
        path = REPO / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("items", []):
            if all(key in row for key in ("message", "question", "options")):
                prior.add(item_fingerprint(row))
    overlap = prior & {item_fingerprint(row) for row in items}
    if overlap:
        raise SystemExit(f"REFUSING: {len(overlap)} v6 items overlap burned qualification items")
    answer_positions = {position: 0 for position in range(3)}
    for row in items:
        answer_positions[row["options"].index(row["answer"])] += 1
    if sorted(answer_positions.values()) != [21, 21, 22]:
        raise SystemExit(f"REFUSING: answer positions are not balanced: {answer_positions}")
    plan = {
        "kind": "ainglish.panel.reader-qualification-plan.v6",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "freeze_rule": "This plan, candidate order, item set, answer key, prompt, thresholds, and transport bounds are committed before any v6 candidate download or inference.",
        "answer_protocol": "opaque-choice-v1",
        "transport": {"adapter": "ollama-native-chat-v1", "think": False, "temperature": 0, "seed": 2026082521, "num_ctx": 4096, "max_tokens": 4, "timeout_s": 300},
        "axes": list(ROWS),
        "items_per_axis": 8,
        "answer_position_counts": {"A": answer_positions[0], "B": answer_positions[1], "C": answer_positions[2]},
        "forbidden_construct_terms": FORBIDDEN_TERMS,
        "disjoint_from_specs": PRIOR_SPECS,
        "candidate_novelty": "Every source_model string was absent from every pre-v6 text, JSON, and Python artifact in this repository when the plan was frozen.",
        "candidate_tranches": CANDIDATES,
        "tranche_rule": "Run phase A first; acquire and run each later tranche only if accumulated published results still contain fewer than two qualified lineages.",
        "gpu_gate": {"ollama_base_url": "http://127.0.0.1:11434", "minimum_total_free_mib": 36000, "maximum_utilization_percent": 35},
        "selection_rule": {
            "exact_code_cells_required": 64,
            "correct_cells_required": 60,
            "correct_per_axis_required": 7,
            "thinking_bytes_required": 0,
            "minimum_distinct_qualified_lineages": 2,
            "no_roster_action": "Publish every result and mint no scientific reader campaign.",
        },
        "items": items,
    }
    plan["content_sha256"] = hashlib.sha256(canonical(plan)).hexdigest()
    with target.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"items": len(items), "candidate_calls": 0, "downloads": 0, "sha256": plan["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
