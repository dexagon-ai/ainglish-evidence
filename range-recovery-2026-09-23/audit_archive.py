"""Offline audit of archived originals. No execution of their embedded code."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def assignments(text):
    match = re.search(
        r"parcel Q has destination (chalk|rubber); parcel R has destination (chalk|rubber)\.",
        text,
    )
    require(match is not None, "Unrecognised literal control")
    return f"{match[1]} then {match[2]}"


def main():
    manifest = json.loads((ROOT / "recovery-manifest.json").read_text())
    packets = {}
    for record in manifest["files"]:
        data = (ROOT / record["path"]).read_bytes()
        require(len(data) == record["bytes"], "Original length changed")
        require(hashlib.sha256(data).hexdigest() == record["sha256"], "Original digest changed")
        packets[record["path"]] = json.loads(data)
    frozen = packets["frozen-original.json"]
    stop = packets["qualification-stop-original.json"]
    screen = frozen["qualification_screens"][0]
    qualification = stop["qualification"]
    controls = screen["controls"]
    screen_bytes = json.dumps({"kind": screen["kind"], "controls": controls,
                              "ordering": "control order; detectable then other; one call per cell; no retry"},
                             sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    screen_hash = hashlib.sha256(screen_bytes).hexdigest()
    require(qualification["screen"]["sha256"] == screen_hash
            and qualification["receipt"]["screen_sha256"] == screen_hash,
            "Frozen screen digest mismatch")
    require(qualification["screen"]["controls"] == len(controls), "Screen count mismatch")
    require(len(controls) == 12, "Wrong control count")
    require(len(stop["http"]) == len(qualification["observations"]) == 24, "Wrong call count")
    require(len(frozen["allocation"]) == 64 and len(frozen["items"]) == 72, "Design size mismatch")
    semantic = {"detectable": 0, "other": 0}
    planted = {"detectable": 0, "other": 0}
    errors = []
    for i, control in enumerate(controls):
        require(control["answer"] == assignments(control["detectable"]), "Incorrect frozen key")
        require(control["answer"] != assignments(control["other"]), "Unchanged other-arm key")
        for j, arm in enumerate(("detectable", "other")):
            index = 2 * i + j
            raw = stop["http"][index]
            observation = qualification["observations"][index]
            choices = "\n".join(f"{chr(65+k)}: {v}" for k, v in enumerate(control["options"]))
            prompt = (
                "Read this message written by one agent to another:\n\n---\n"
                f"{control[arm]}\n---\n\nQuestion: {control['question']}\nChoices:\n"
                f"{choices}\nAnswer with EXACTLY one choice code and nothing else."
            )
            require(raw["sequence"] == index + 1, "Sequence mismatch")
            require(raw["request_body"]["model"] == screen["reader"]["model"], "Reader mismatch")
            require(raw["request_body"]["messages"] == [{"role": "user", "content": prompt}], "Prompt mismatch")
            choice = raw["response"]["choices"][0]
            require(choice["finish_reason"] == "stop" and "exception" not in raw, "Incomplete response")
            code = choice["message"]["content"].strip().upper()
            require(len(code) == 1 and code in "ABCD", "Invalid response code")
            answer = control["options"][ord(code) - 65]
            require(observation["control_id"] == control["id"] and observation["cell"] == arm, "Cell mismatch")
            require(observation["answer"] == answer and observation["expected"] == control["answer"], "Answer mismatch")
            require(observation["correct"] == (answer == control["answer"]), "Recorded score mismatch")
            planted[arm] += answer == control["answer"]
            semantic[arm] += answer == assignments(control[arm])
            if answer != assignments(control[arm]):
                errors.append(raw["sequence"])
    require(planted == {"detectable": 11, "other": 0}, "Qualification counts changed")
    require(semantic == {"detectable": 11, "other": 12}, "Semantic counts changed")
    require(errors == [11], "Unexpected semantic error")
    result = qualification["receipt"]["result"]
    require(result == {"detectable_correct": 11, "detectable_total": 12,
                      "other_correct": 0, "other_total": 12,
                      "min_gap_bps": 5000, "min_recovered_bps": 9500,
                      "passed": False}, "Unexpected qualification receipt")
    require(qualification["status"] == "failed" and 11 * 10000 < 12 * 9500, "Failure not preserved")
    require(stop["frozen_inputs"] == manifest["files"][0]["original_url"], "Historical URL rewritten")
    require(frozen["reader_calls_at_publication"] == 0, "Original freeze call boundary changed")
    for field in ("scientific_calls", "experimental_calibration_calls", "second_reader_calls", "mints", "measurements", "retries"):
        require(stop["raw_audit"][field] == 0, "Original stop boundary changed: " + field)
    print(json.dumps({"files_hash_verified": 2, "recorded_calls_replayed": 24,
                      "semantic_correct": semantic, "planted_key_correct": planted,
                      "qualification_passed": False, "new_inference_calls": 0,
                      "boundary": "Audits supplied records; does not certify absence of unrecorded calls."}, indent=2))


if __name__ == "__main__":
    main()
