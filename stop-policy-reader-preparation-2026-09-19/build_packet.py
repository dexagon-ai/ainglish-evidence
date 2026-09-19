"""Deterministic, CPU-only preparation. Never authenticates, qualifies, mints or calls a reader."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SLUG = "stop-s-finish-started-stop-s-interrupt-started-a-stop"
PUBLIC_ID = "a-7x91n7c1yr2n8gfp"
FORMS = ("finish-started", "interrupt-started")


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


# Positive controls use a DIFFERENT novel dictionary, not the target's semantics.
# The unexposed control deliberately lacks its arbitrary assignment; this is NOT
# a weakened English comparator for a scientific stop-policy case.
CONTROL_WORLDS = [
    ("route", "which chute receives the parcel", "upper chute", "lower chute"),
    ("cover", "which cover the notebook receives", "linen cover", "cork cover"),
    ("visit", "which day the visitor is booked", "Tuesday", "Thursday"),
    ("signal", "which lamp displays the signal", "violet lamp", "amber lamp"),
    ("shelf", "which shelf receives the book", "east shelf", "west shelf"),
    ("meal", "which dish the ticket selects", "bean stew", "rice salad"),
    ("desk", "which desk receives the letter", "stone desk", "wood desk"),
    ("fabric", "which fabric is allocated", "cotton", "wool"),
    ("gate", "which gate the pass selects", "garden gate", "canal gate"),
    ("tone", "which sound the notice selects", "bell", "whistle"),
    ("tray", "which tray receives the sample", "glass tray", "steel tray"),
    ("room", "which room hosts the meeting", "attic room", "cellar room"),
]


def controls(prefix):
    result = []
    for n, (kind, consequence, left, right) in enumerate(CONTROL_WORLDS):
        symbol = f"{prefix}vex{n + 1}"
        selected = (left, right)[n % 2]
        opposite = (right, left)[n % 2]
        unexposed = (
            f"A private two-value dictionary determines {consequence}. "
            f"Its alternatives are {left} and {right}. The assignment of '{symbol}' "
            f"is not otherwise specified. The recorded code is '{symbol}'."
        )
        # No contradictory 'not specified' assertion in the exposed message.
        exposed = (
            f"A private two-value dictionary determines {consequence}. "
            f"Its alternatives are {left} and {right}. Dictionary: '{symbol}' "
            f"selects {selected}, not {opposite}. The recorded code is '{symbol}'."
        )
        options = [left, right, "cannot determine from the supplied dictionary"]
        rotation = n % 3
        options = options[rotation:] + options[:rotation]
        result.append({
            "id": f"{prefix}-{kind}-{n + 1:02d}",
            "calibration": True,
            "calibration_scope": "target-independent",
            "calibration_construct": f"{prefix}-private-assignment",
            "english": unexposed,
            "ainglish": exposed,
            "question": f"Using this dictionary, {consequence}?",
            "options": options,
            "answer": selected,
        })
    return result


def main(source):
    proposal = json.loads(Path(source).read_text())
    assert proposal["public_id"] == PUBLIC_ID and proposal["slug"] == SLUG
    worlds = json.loads((ROOT / "worlds.json").read_text())
    assert len(worlds) == 32 and len({w["id"] for w in worlds}) == 32
    assert set(Counter(w["family"] for w in worlds).values()) == {8}
    teaching = proposal["english_mapping"]
    (ROOT / "entry.txt").write_text(teaching)  # No added newline: exact API field bytes.
    source_fields = {key: proposal[key] for key in [
        "public_id", "slug", "title", "form", "english_mapping", "predicted_measurement", "evidence_contract"
    ]}
    source_fields["content_digest"] = proposal["author_work_notices"]["content_digest"]
    save("proposal-definition-snapshot.json", source_fields)

    real = []
    audit = []
    option_positions = Counter()
    for index, world in enumerate(worlds):
        for form in FORMS:
            arm = "finish" if form == "finish-started" else "interrupt"
            marked = world["scenario"] + f"\nDirective: Stop {world['scope']}, {form}."
            options = list(world["options"])
            answer = options[world[arm]]
            critical = world["finish"] != world["interrupt"]
            bucket = (form, critical)
            desired = (option_positions[bucket] + (1 if arm == "interrupt" else 0) + (0 if critical else 1)) % 3
            option_positions[bucket] += 1
            rotation = (world[arm] - desired) % 3
            options = options[rotation:] + options[:rotation]
            real.append({
                "id": f"{world['id']}--{form}",
                "calibration": False,
                "world_id": world["id"],
                "family": world["family"],
                "tested_form": form,
                "form_changes_answer": world["finish"] != world["interrupt"],
                "strata": {"world_id": world["id"], "family": world["family"],
                           "form": form, "policy_changes_answer": world["finish"] != world["interrupt"]},
                "english": marked,
                "ainglish": marked,
                "question": world["question"],
                "options": options,
                "answer": answer,
            })
            audit.append({
                "id": real[-1]["id"], "answer": answer,
                "entailment": world["proof"],
                "scope": world["scope"], "family": world["family"],
                "form_changes_answer": real[-1]["form_changes_answer"],
                "reviewer": "Dexagon (author; not independent verification)",
            })
    items = controls("cal") + real
    save("items.json", {"kind": "ainglish.stop-policy.learnability-preparation.v1",
                        "sha256": digest(items), "items": items})
    save("gold-audit.json", {"kind": "author-semantic-audit.v1", "rows": audit})

    panel = []
    for name, model, model_digest, lineage in [
        ("mistral-small3.2-24b-opaque-choice-q4_k_m", "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
         "6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de", "mistral-small3.2"),
        ("gemma3-12b-opaque-choice-q4_k_m", "dexagon-gemma3-12b-pp-task:ctx4k",
         "de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f", "gemma3"),
    ]:
        reader = {
            "name": name, "provider": "ollama", "base_url": "http://127.0.0.1:11434/v1",
            "model": model, "precision": "Q4_K_M", "model_digest": "sha256:" + model_digest,
            "digest_source": "Local Ollama /api/tags, verified before any launch",
            "max_tokens": 64, "temperature": 0, "timeout_s": 120,
            "seed": 2026091981, "answer_protocol": "opaque-choice-v1",
        }
        panel.append(reader)
        screen_controls = [
            {"id": c["id"], "detectable": c["ainglish"], "other": c["english"],
             "question": c["question"], "options": c["options"], "answer": c["answer"]}
            for c in controls("qual")
        ]
        save(f"qualification-{lineage}.json", {
            "kind": "ainglish.reader-qualification-screen.v1",
            "roster_id": name + "@Q4_K_M", "reader": reader,
            "lineage": {"key": lineage, "basis": "Distinct Mistral Small and Gemma published model families; not a claim of statistically independent errors."},
            "validity_days": 7, "min_gap_bps": 5000, "min_recovered_bps": 5000,
            "controls": screen_controls,
        })
    runspec = {
        "construct": "finish-started / interrupt-started", "slug": SLUG,
        "form": proposal["form"], "metric": "learnability", "seed": 2026091981,
        "planted_arm": "ainglish", "calibration_min_gap": "0.5",
        "calibration_min_recovered": "0.5", "panel": panel,
        "admissibility": {
            "kind": "ainglish.panel.admissibility.v1", "per_reader_calibration": True,
            "max_off_option_cells": 304, "max_absent_cells": 0,
            "max_truncated_cells": 0, "max_transport_fault_cells": 0,
        },
        "entry": {"text": teaching, "sha256": hashlib.sha256(teaching.encode()).hexdigest(),
                  "source_url": "https://ainglish.org/proposals/" + PUBLIC_ID,
                  "proposal_revision": SLUG},
        # Inline answer-bearing inputs make the derived manifest self-contained.
        "items": items, "items_sha256": digest(items),
        "attempt": {
            "estimand": "Entry-loaded operational-consequence accuracy on this fixed 32-world, two-form bank and two exact local reader editions. Cold accuracy is a labelled diagnostic, not a comparison with English. Overall and each form must reach >=0.95 under the unchanged proposal. Author decision also requires >=0.95 on each form's predeclared policy-changing subset, to prevent easy invariant boundaries masking the central contrast.",
            "admissibility_gates": [
                "No launch before affirmative independent fresh-input replication commitment and explicit retained scientific-spend decision; silence is not assent.",
                "All answer-bearing bytes and exact entry frozen before target exposure; no target pilot, retry, selective replacement or optional stopping.",
                "Both exact reader editions individually pass fresh target-independent qualification and in-panel planted-effect calibration; preserve failed receipts.",
                "Each real reader/item is stateless, cold then entry; both item-arm texts are byte-identical and only the official harness prefixes the entry.",
                "No same-study substitution for the separate careful-English prerequisite. Per-form and policy-changing-subset diagnostics remain load-bearing for the author's adoption recommendation.",
                "Retain every exact prompt, raw response, parsed answer, gold, grade, transport fault and attempt receipt. Live state and resource checks precede a minted official run.",
            ],
            "planned_sample": {
                "worlds": 32, "real_items": 64, "real_items_per_form": 32,
                "readers": 2, "cold_and_entry_calls": 256, "calibration_items": 12,
                "calibration_calls": 48, "qualification_calls_at_most": 48,
                "maximum_original_reader_calls": 352,
                "maximum_original_and_fresh_replication_calls": 704,
                "no_comprehension_study_calls_authorised_by_this_packet": True,
            },
        },
    }
    save("learnability-preparation.json", runspec)
    tracked = ["worlds.json", "entry.txt", "proposal-definition-snapshot.json", "items.json",
               "gold-audit.json", "learnability-preparation.json",
               "qualification-mistral-small3.2.json", "qualification-gemma3.json"]
    save("frozen-inputs.json", {"status": "FROZEN INPUTS; EXECUTION HELD",
                              "files": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in tracked}})
    print(json.dumps({"real_items": len(real), "worlds": len(worlds),
                      "policy_changing_worlds": sum(w["finish"] != w["interrupt"] for w in worlds),
                      "items_sha256": digest(items), "entry_sha256": runspec["entry"]["sha256"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal_snapshot")
    main(parser.parse_args().proposal_snapshot)
