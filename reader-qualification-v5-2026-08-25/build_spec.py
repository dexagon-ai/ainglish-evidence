#!/usr/bin/env python3
"""Freeze the one-shot v5 ordinary-English qualification holdout without inference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
OPTIONS = ("yes", "no", "cannot tell")
MODELS = (
    ("gemma3-12b-qualification-v5", "Gemma 3 12B", "dexagon-gemma3-12b-qualification-v5:ctx4k", "q4_k_m"),
    ("llama3.1-8b-qualification-v5", "Llama 3.1 8B", "dexagon-llama3.1-8b-qualification-v5:ctx4k", "q4_k_m"),
    ("phi4-14b-qualification-v5", "Phi-4 14B", "dexagon-phi4-14b-qualification-v5:ctx4k", "q4_k_m"),
    ("granite3.3-8b-qualification-v5", "Granite 3.3 8B", "dexagon-granite3.3-8b-qualification-v5:ctx4k", "q4_k_m"),
    ("command-r7b-qualification-v5", "Command R7B", "dexagon-command-r7b-qualification-v5:ctx4k", "q4_k_m"),
)

ROWS = {
    "quantifier_force": [
        ("At least six of the eleven valves opened.", "Could exactly five valves have opened?", "no"),
        ("No more than three delegates signed.", "Could two delegates have signed?", "yes"),
        ("Every one of the four parcels arrived.", "Did any parcel fail to arrive?", "no"),
        ("Exactly eight of twelve lamps are lit.", "Are four lamps unlit?", "yes"),
        ("Some but not necessarily all mirrors were cleaned.", "Does the sentence establish that every mirror was cleaned?", "no"),
        ("Fewer than two alarms sounded.", "Could one alarm have sounded?", "yes"),
        ("All but one of the nine requests succeeded.", "Did exactly one request fail?", "yes"),
        ("A majority of the seven jurors agreed.", "Must at least four jurors have agreed?", "yes"),
    ],
    "set_membership": [
        ("The audit team contains Nia, Sol and the reader of this note.", "Is the reader on the audit team?", "yes"),
        ("Only Uma and Vic hold archive keys.", "Does Wen hold an archive key?", "no"),
        ("All bronze-pass holders may enter. Jo has a bronze pass.", "May Jo enter?", "yes"),
        ("Only maintainers may merge. Kai merged the patch under this rule.", "Is Kai a maintainer?", "yes"),
        ("The message names Lia and Max as editors and gives no complete membership list.", "Is Noor an editor?", "cannot tell"),
        ("The supported zones are north and east, and no other zone is supported.", "Is south supported?", "no"),
        ("Everyone in cohort C received a token. Paz is in cohort C.", "Did Paz receive a token?", "yes"),
        ("Rae received a token. The note does not say who belongs to cohort C.", "Is Rae in cohort C?", "cannot tell"),
    ],
    "negation_scope": [
        ("The scanner did not inspect every file.", "Was at least one file not inspected?", "yes"),
        ("No approved invoice remained unpaid.", "Did an approved invoice remain unpaid?", "no"),
        ("It is false that both gates opened.", "Did both gates open?", "no"),
        ("The rule does not prohibit copying the summary.", "Does that sentence itself require copying the summary?", "no"),
        ("None of the five codes unlocked the case.", "Did any listed code unlock it?", "no"),
        ("The endpoint is not unreachable.", "Is the endpoint unreachable?", "no"),
        ("Mira did not promise to review every document.", "Did Mira promise to review no documents?", "cannot tell"),
        ("Not every sensor is offline.", "Is at least one sensor online?", "yes"),
    ],
    "disjunction": [
        ("Choose cedar or birch, but not both.", "May both be chosen?", "no"),
        ("The notice may go by mail, courier, or both.", "May both channels be used?", "yes"),
        ("At least one of check A or check B must pass; both may pass.", "May both checks pass?", "yes"),
        ("Exactly one of the two replicas becomes primary.", "Can both become primary under this sentence?", "no"),
        ("Store the copy in Rome or Oslo. The sentence gives no exclusivity rule.", "Does the sentence establish that using both is forbidden?", "no"),
        ("Use either checksum, including both if desired.", "May both checksums be used?", "yes"),
        ("The fault is in the cable or the port; no claim about exclusivity is made.", "Must exactly one be faulty?", "no"),
        ("One and only one of red or blue must be selected.", "May neither be selected?", "no"),
    ],
    "conditional": [
        ("If the latch is open, sound the buzzer. The latch is open.", "Should the buzzer sound?", "yes"),
        ("If the build passes, publish it. It was published.", "Must the build have passed?", "cannot tell"),
        ("Do not dispatch the crate unless it is sealed. It is unsealed.", "Should it be dispatched?", "no"),
        ("A guest may enter only if registered. This guest is unregistered.", "May this guest enter?", "no"),
        ("Run the migration only when both backups exist. One backup is missing.", "Should the migration run?", "no"),
        ("If a drill is active, notify Pat. A drill is active.", "Should Pat be notified?", "yes"),
        ("If the card is valid, the door opens. The card is invalid.", "Does the sentence establish that the door stays closed?", "cannot tell"),
        ("Whenever frost is detected, heat the pipe. Frost was detected.", "Should the pipe be heated?", "yes"),
    ],
    "reference_resolution": [
        ("Tess gave Uri the brass key. Uri locked it in the drawer.", "Did Uri put the brass key in the drawer?", "yes"),
        ("Vera told Wes that he would chair the meeting.", "Does the sentence unambiguously say Vera will chair?", "no"),
        ("The modem sent the router a reset because the modem had stalled.", "Had the modem stalled?", "yes"),
        ("I attached the chart to the memo. The former needs revision.", "Does the chart need revision?", "yes"),
        ("The green bin stands beside the white bin. This note says the white bin is full.", "Is the green bin stated to be full?", "no"),
        ("Xia called Yara after Xia completed the scan.", "Did Xia complete the scan?", "yes"),
        ("Zed placed the cup on the tray and then washed it.", "Is the washed object unambiguous?", "no"),
        ("Ari lent Bea the camera. Bea returned the camera today.", "Did Bea return the camera?", "yes"),
    ],
    "temporal_order": [
        ("The index was signed before it was uploaded.", "Was it uploaded before it was signed?", "no"),
        ("After the alarm ended, the doors reopened.", "Did the alarm end before the doors reopened?", "yes"),
        ("The report and the invoice arrived on Tuesday; no order is stated.", "Did the report arrive first?", "cannot tell"),
        ("Quin backed up the file, then deleted the original.", "Did the backup happen before deletion?", "yes"),
        ("The review must finish no later than Friday.", "Could a Saturday finish satisfy that deadline?", "no"),
        ("The job starts at 09:00 and lasts two hours.", "Is it still running at 10:00?", "yes"),
        ("Rin approved the draft while Sam was editing it.", "Does the sentence establish which activity began first?", "cannot tell"),
        ("The patch landed immediately after the test completed.", "Did the test complete first?", "yes"),
    ],
    "authority_and_permission": [
        ("The policy permits reviewers to download the log.", "Are reviewers allowed to download it?", "yes"),
        ("The system is capable of deleting the log, but no permission is stated.", "Does the sentence grant permission to delete it?", "no"),
        ("The rule requires Dana to sign the form.", "Does the sentence create or report a duty for Dana?", "yes"),
        ("Eli is expected to arrive, and no rule applies.", "Does the sentence impose a duty on Eli to arrive?", "no"),
        ("The supervisor did not forbid the change.", "Does that fact alone establish that the change is permitted?", "no"),
        ("Only the owner may rotate the key. Fia is not the owner.", "May Fia rotate the key?", "no"),
        ("Gus can reach the server and is expressly allowed to connect.", "Is Gus allowed to connect?", "yes"),
        ("Hana might finish tonight. The message says nothing about rules.", "Does the message impose a requirement on Hana?", "no"),
    ],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def choices(answer: str, position: int) -> list[str]:
    others = [value for value in OPTIONS if value != answer]
    out = list(others)
    out.insert(position, answer)
    return out


def tags() -> dict[str, str]:
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=20) as response:
        return {row["name"]: row["digest"] for row in json.load(response).get("models", [])}


def main() -> None:
    target = ROOT / "holdout.json"
    if target.exists():
        raise SystemExit("REFUSING: holdout.json already exists")
    known = tags()
    panel = []
    for name, lineage, model, precision in MODELS:
        digest = known.get(model)
        if not digest:
            raise SystemExit(f"REFUSING: model {model} is not installed")
        panel.append({
            "name": name, "lineage": lineage, "provider": "ollama", "model": model,
            "model_digest": f"sha256:{digest}", "precision": precision,
            "max_tokens": 4, "timeout_s": 180, "temperature": 0, "seed": 2026082508,
        })
    items = []
    for axis, rows in ROWS.items():
        for index, (message, question, answer) in enumerate(rows):
            items.append({
                "id": f"v5-hold-{axis}-{index + 1:02d}", "axis": axis,
                "message": message, "question": question,
                "options": choices(answer, index % 3), "answer": answer,
            })
    spec = {
        "kind": "ainglish.panel.reader-qualification-holdout.v5",
        "result_kind": "ainglish.panel.reader-qualification-holdout-result.v5",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "answer_protocol": "opaque-choice-v1",
        "transport": {"adapter": "ollama-native-chat-v1", "think": False},
        "axes": list(ROWS), "items_per_axis": 8,
        "forbidden_construct_terms": [
            "ainglish", "proxy(", "obs:", "inf:", "rep(", "must-as-", "should-as-",
            "will-as-", "may-not-as-", "all-or-nothing", "keep-successes",
        ],
        "disjoint_from_specs": [
            str(ROOT.parent / "reader-qualification-tournament-2026-08-23/spec.json"),
            str(ROOT.parent / "reader-qualification-v2-2026-08-24/development.json"),
            str(ROOT.parent / "reader-qualification-v2-2026-08-24/holdout.json"),
            str(ROOT.parent / "reader-qualification-v3-2026-08-24/development.json"),
            str(ROOT.parent / "reader-qualification-v3-2026-08-24/holdout.json"),
            str(ROOT.parent / "reader-qualification-v4-2026-08-24/holdout.json"),
        ],
        "gpu_gate": {
            "ollama_base_url": "http://127.0.0.1:11434",
            "minimum_total_free_mib": 36000, "maximum_utilization_percent": 35,
        },
        "selection_rule": {
            "exact_code_cells_required": 64, "correct_cells_required": 60,
            "correct_per_axis_required": 7, "minimum_distinct_qualified_lineages": 2,
            "no_roster_action": "Publish every result; if fewer than two lineages qualify, mint no scientific reader campaign.",
        },
        "panel": panel, "items": items,
    }
    spec["content_sha256"] = hashlib.sha256(canonical(spec)).hexdigest()
    target.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(items), "models": len(panel), "reader_calls": 0, "sha256": spec["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

