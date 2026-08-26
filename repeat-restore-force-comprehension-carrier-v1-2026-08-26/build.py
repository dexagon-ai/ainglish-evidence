#!/usr/bin/env python3
"""Build the force-aware carrier without reader or governance calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "repeat-event-restore-state-did-again-repeat-the-action-or-on-3"
FORCES = ("affirmative", "negated", "question", "directive")
FORMS = ("repeat-event", "restore-state")
OPERATIONS = (
    ("Asha", "raise", "raised", "raised", "north signal flag"),
    ("Bram", "lower", "lowered", "lowered", "east loading bridge"),
    ("Cleo", "activate", "activated", "active", "south warning beacon"),
    ("Dario", "deactivate", "deactivated", "inactive", "west transfer relay"),
    ("Esme", "mount", "mounted", "mounted", "upper archive volume"),
    ("Farah", "unmount", "unmounted", "unmounted", "lower scratch volume"),
    ("Galen", "seal", "sealed", "sealed", "inner sample chamber"),
    ("Hana", "unseal", "unsealed", "unsealed", "outer review envelope"),
    ("Iris", "open", "opened", "open", "amber access gate"),
    ("Jules", "close", "closed", "closed", "bronze service hatch"),
    ("Kira", "lock", "locked", "locked", "coral evidence cabinet"),
    ("Leon", "unlock", "unlocked", "unlocked", "dune control panel"),
    ("Mina", "start", "started", "running", "elm indexing worker"),
    ("Noor", "stop", "stopped", "not-running", "flint export worker"),
    ("Omar", "connect", "connected", "connected", "jade telemetry feed"),
    ("Pia", "disconnect", "disconnected", "not-connected", "linen report stream"),
)
FORCE_ANSWERS = {
    "affirmative": "the scoped event is asserted",
    "negated": "the scoped event is denied",
    "question": "the scoped event is questioned",
    "directive": "the scoped event is requested",
}
FORCE_OPTIONS = list(FORCE_ANSWERS.values())


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(options: list[str], answer: str, position: int) -> list[str]:
    current = options.index(answer)
    shift = (current - position) % len(options)
    return options[shift:] + options[:shift]


def state_text(state: str) -> str:
    return {"not-running": "not running", "not-connected": "not connected"}.get(state, state)


def clause(force: str, actor: str, lemma: str, past: str, obj: str) -> str:
    if force == "affirmative": return f"{actor} {past} the {obj}."
    if force == "negated": return f"{actor} did not {lemma} the {obj}."
    if force == "question": return f"did {actor} {lemma} the {obj}?"
    if force == "directive": return f"{actor}, {lemma} the {obj}."
    raise ValueError(force)


def careful_at_issue(force: str, actor: str, lemma: str, past: str, obj: str) -> str:
    if force == "affirmative": return f"The message asserts that {actor} {past} the {obj}."
    if force == "negated": return f"The message denies that {actor} {past} the {obj}."
    if force == "question": return f"The message asks whether {actor} {past} the {obj}."
    return f"The message requests that {actor} {lemma} the {obj}."


def earlier_options(form: str, force: str, actor: str, lemma: str, obj: str, state: str) -> tuple[list[str], str]:
    if form == "repeat-event":
        answer = (
            f"{actor} performed a matching {lemma} event before the requested event; the prefix does not say whether it preceded the message"
            if force == "directive" else
            f"{actor} performed a matching {lemma} event before the scoped event's reference time"
        )
        options = [
            answer,
            f"the {obj} had the result state earlier, with no claim about who caused it",
            f"somebody other than {actor} performed the earlier matching event",
            "the prefix contributes no earlier condition",
        ]
    else:
        state_value = state_text(state)
        answer = (
            f"the {obj} was {state_value} before the requested event; no earlier matching event or same-actor cause is claimed"
            if force == "directive" else
            f"the {obj} was {state_value} during an earlier interval; no earlier matching event or same-actor cause is claimed"
        )
        options = [
            answer,
            f"{actor} performed the same {lemma} event earlier",
            f"the {obj} remained continuously {state_value} with no transition",
            "the prefix contributes no earlier condition",
        ]
    return options, answer


def frame(form: str, force: str, operation_index: int, ordinal: int) -> tuple[dict, list[dict]]:
    actor, lemma, past, state, obj = OPERATIONS[operation_index]
    state_arg = f"{state}({obj.replace(' ', '-')})"
    scoped = clause(force, actor, lemma, past, obj)
    marker = "repeat-event:" if form == "repeat-event" else f"restore-state({state_arg}):"
    ainglish = f"Case RRF-{ordinal:03d} concerns the {obj}. {marker} {scoped}"
    at_issue = careful_at_issue(force, actor, lemma, past, obj)
    if form == "repeat-event":
        earlier = (
            f"Before the requested event, {actor} performed an earlier matching {lemma} event on the same {obj}; this does not say whether that earlier event preceded the message."
            if force == "directive" else
            f"Before the scoped event's reference time, {actor} performed an earlier matching {lemma} event on the same {obj}."
        )
    else:
        earlier = (
            f"The {obj} was {state_text(state)} before the requested event; no earlier matching event or earlier same-actor cause is claimed."
            if force == "directive" else
            f"The {obj} was {state_text(state)} during an earlier interval; no earlier matching event or earlier same-actor cause is claimed."
        )
    english = f"Case RRF-{ordinal:03d} concerns the {obj}. {earlier} {at_issue}"
    e_options, e_answer = earlier_options(form, force, actor, lemma, obj, state)
    base = {
        "frame_id": f"rrf-{form}-{force}-{operation_index + 1:02d}",
        "form": form,
        "force": force,
        "predicate_family": lemma,
        "actor": actor,
        "object": obj,
        "result_state": state_arg,
        "english": english,
        "ainglish": ainglish,
        "directive_time_seam": force == "directive",
    }
    rows = [
        {**base, "id": base["frame_id"] + "-earlier", "probe": "background_condition", "question": "What earlier condition does the target prefix contribute?", "options": rotate(e_options, e_answer, (ordinal * 2) % 4), "answer": e_answer},
        {**base, "id": base["frame_id"] + "-force", "probe": "at_issue_force", "question": "What status does the message give the scoped event?", "options": rotate(list(FORCE_OPTIONS), FORCE_ANSWERS[force], (ordinal * 2 + 1) % 4), "answer": FORCE_ANSWERS[force]},
    ]
    return base, rows


def scientific() -> tuple[list[dict], list[dict]]:
    frames, rows = [], []
    ordinal = 1
    for form in FORMS:
        for force in FORCES:
            for operation_index in range(16):
                base, probes = frame(form, force, operation_index, ordinal)
                frames.append({**base, "probe_ids": [row["id"] for row in probes]})
                rows.extend(probes)
                ordinal += 1
    return frames, rows


def validity() -> list[dict]:
    rows = []
    kinds = ("valid",) * 8 + ("missing-state",) * 8 + ("non-entailed-state",) * 8 + ("ambiguous-state",) * 4 + ("multi-result",) * 4
    for index, kind in enumerate(kinds):
        actor, lemma, past, state, obj = OPERATIONS[index % len(OPERATIONS)]
        if kind == "valid": marker = f"restore-state({state}({obj.replace(' ', '-')})):"; sentence = f"{actor} {past} the {obj}."; valid = True
        elif kind == "missing-state": marker = "restore-state:"; sentence = f"{actor} {past} the {obj}."; valid = False
        elif kind == "non-entailed-state": marker = "restore-state(healthy(service)):"; sentence = f"{actor} repaired the service."; valid = False
        elif kind == "ambiguous-state": marker = "restore-state(ready(system)):"; sentence = f"{actor} adjusted the system."; valid = False
        else: marker = "restore-state(done(work)):"; sentence = f"{actor} changed and archived the work."; valid = False
        answer = "licensed" if valid else "invalid"
        options = [answer, "invalid" if valid else "licensed"]
        if index % 2: options.reverse()
        rows.append({
            "id": f"rrf-validity-{index + 1:02d}", "fixture_kind": kind,
            "ainglish": f"{marker} {sentence}",
            "english": "Check whether the named state is explicit, uniquely resolved, and entailed as the scoped event's result.",
            "question": "Is this restore-state use licensed by the registered mapping?",
            "options": options, "answer": answer, "valid": valid,
        })
    return rows


def calibration() -> list[dict]:
    rows = []
    objects = ("amber disk", "bronze card", "coral token", "dune seal", "elm key", "flint tag", "jade pass", "linen badge")
    for index, obj in enumerate(objects):
        bay = 91 + index; answer = f"bay {bay}"; options = [answer, f"bay {bay + 1}", "not stated", "dispatch desk"]
        options = rotate(options, answer, index % 4)
        rows.append({"id": f"rrf-cal-{index + 1:02d}", "calibration": True, "english": f"The note labels the {obj} zof({bay}), but gives no meaning for zof.", "ainglish": f"Control: zof(<N>) means the labelled object is stored in bay N. The note labels the {obj} zof({bay}).", "question": f"Where does the control place the {obj}?", "options": options, "answer": answer})
    return rows


def main() -> None:
    frames, rows = scientific(); validity_rows = validity(); calibration_rows = calibration()
    assert len(frames) == 128 and len(rows) == 256 and len(validity_rows) == 32 and len(calibration_rows) == 8
    assert Counter((row["form"], row["force"], row["probe"]) for row in rows) == Counter({(form, force, probe): 16 for form in FORMS for force in FORCES for probe in ("background_condition", "at_issue_force")})
    packet = {"kind": "dexagon.ainglish.repeat-restore-force-comprehension-items.v1", "proposal_slug": SLUG, "seed": 2026082649, "frames": frames, "scientific_rows": rows, "validity_rows": validity_rows, "calibration_rows": calibration_rows}
    packet["frames_sha256"] = hashlib.sha256(canonical(frames)).hexdigest(); packet["scientific_rows_sha256"] = hashlib.sha256(canonical(rows)).hexdigest(); packet["validity_rows_sha256"] = hashlib.sha256(canonical(validity_rows)).hexdigest(); packet["calibration_rows_sha256"] = hashlib.sha256(canonical(calibration_rows)).hexdigest(); packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    (ROOT / "items.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = {"kind": "dexagon.ainglish.repeat-restore-force-comprehension-freeze.v1", "proposal_slug": SLUG, "items_path": "items.json", "frames": 128, "scientific_rows": 256, "validity_rows": 32, "calibration_rows": 8, "forms": {"repeat-event": 64, "restore-state": 64}, "forces_per_form": {force: 16 for force in FORCES}, "items_content_sha256": packet["content_sha256"], "model_calls": 0, "tokenizer_calls": 0, "governance_writes": 0, "execution_gate": "proposal seconded, token prerequisite complete, and at least two distinct eligible qualified reader lineages"}
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest(); (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"frames": 128, "scientific_rows": 256, "validity_rows": 32, "calibration_rows": 8, "content_sha256": index["content_sha256"]}, indent=2))


if __name__ == "__main__": main()

