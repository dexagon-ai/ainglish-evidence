"""Generate/freeze a scoped only-focus study. No target inference or API writes.

Generation and binding are separate so the public item commit can be pinned before
the SDK constructs an attempt manifest. Output files are exclusive-created.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "native-followthrough-2026-09-13"
PROPOSAL = "a-hr8ktarqq22derhx"
LABELS = ["Entailed", "Contradicted", "Not determined"]
# Each row defines an actor, a peer, two relevant objects and two relevant actions.
# The counterfactual event probes are logically evaluated, not scored by row position.
TOPICS = [
    ("Mira", "Sol", "the tests", "the docs", "changed", "deleted"),
    ("Anik", "Jo", "the report", "the appendix", "approved", "printed"),
    ("Nia", "Omar", "the invoices", "the receipts", "copied", "signed"),
    ("Eli", "Uma", "the archive", "the backup", "checked", "erased"),
    ("Ada", "Bo", "the first draft", "the final draft", "reviewed", "printed"),
    ("Inez", "Kai", "the blue queue", "the red queue", "paused", "cleared"),
    ("Tess", "Ren", "the routing table", "the firewall rules", "saved", "edited"),
    ("Zoe", "Lev", "the signed release notes", "the unsigned draft notes", "uploaded", "renamed"),
    ("Pia", "Max", "the raw images", "the final images", "archived", "inspected"),
    ("Luz", "Kit", "the schedule", "the roster", "updated", "published"),
    ("Eva", "Noor", "the staging files", "the production files", "scanned", "moved"),
    ("Ari", "Dee", "the job list", "the error log", "opened", "exported"),
]
CONDITIONS = [
    ("during retries", "during first attempts"),
    ("during backups", "during restores"),
    ("during uploads", "during downloads"),
    ("during migrations", "during rollbacks"),
    ("during validation", "during generation"),
    ("during deployments", "during previews"),
    ("during imports", "during exports"),
    ("during compilation", "during linking"),
    ("during indexing", "during searches"),
    ("during synchronization", "during reconciliation"),
    ("during rotation", "during renewal"),
    ("during compression", "during extraction"),
]


def save(name, data):
    with (HERE / name).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def truth(statement, asserted, excluded):
    """Three-valued entailment from a positive event plus a scoped exclusion.

    Events are (actor, action, object). Negation inverts a known event value and
    preserves unknown. No closed-world assumption is applied to an unmarked slot.
    """
    event, negated = statement
    value = True if event in asserted else False if event in excluded else None
    if value is not None and negated:
        value = not value
    return "Not determined" if value is None else "Entailed" if value else "Contradicted"


def frame(site, index):
    topic = TOPICS[index % len(TOPICS)]
    actor, peer, obj, other, action, other_action = topic
    if index >= len(TOPICS):
        actor, peer, obj, other = peer, actor, other, obj
    intended_negative = (index + index // len(TOPICS)) % 2 == 0
    positive = (actor, action, obj)
    if site == "subject":
        context = (f"This note reports which people {action} {obj}. The relevant people "
                   f"are {actor} and {peer}; {obj} and {other} are distinct objects.")
        marked = f"only-{actor} {action} {obj}."
        placement = f"Only {actor} {action} {obj}."
        bare = f"{actor} only {action} {obj}."
        careful = f"{actor} {action} {obj}, and no other relevant person {action} {obj}."
        excluded = {(peer, action, obj)}
        intended = (peer, action, obj)
        orthogonal = (actor, other_action, obj)
    elif site == "verb":
        context = (f"This note reports which actions {actor} performed on {obj}. "
                   f"The relevant actions are {action} and {other_action}; "
                   f"{obj} and {other} are distinct objects.")
        marked = f"{actor} only-{action} {obj}."
        placement = bare = f"{actor} only {action} {obj}."
        careful = f"{actor} {action} {obj} and did nothing else of the relevant kind to it."
        if obj.endswith(("tests", "docs", "invoices", "receipts", "rules", "notes", "images", "files")):
            careful = careful.replace("to it.", "to them.")
        excluded = {(actor, other_action, obj)}
        intended = (actor, other_action, obj)
        orthogonal = (actor, action, other)
    elif site == "nominal":
        context = (f"This note reports which objects {actor} {action}. The relevant "
                   f"objects are {obj} and {other}; these are distinct objects.")
        marked = f"{actor} {action} only-{obj.replace(' ', '-')} .".replace(" .", ".")
        placement = f"{actor} {action} only {obj}."
        bare = f"{actor} only {action} {obj}."
        careful = f"{actor} {action} {obj} and {action} no other relevant objects."
        excluded = {(actor, action, other)}
        intended = (actor, action, other)
        orthogonal = (actor, other_action, obj)
    else:
        condition, alternative = CONDITIONS[index % len(CONDITIONS)]
        actor = "The worker" if index < len(CONDITIONS) else "The gateway"
        context = (f"This note reports under which conditions {actor.lower()} fails. "
                   f"{condition.capitalize()} and {alternative} are the relevant, "
                   "non-overlapping conditions. It is not a report of failure frequency.")
        marked = f"{actor} fails only-{condition.replace(' ', '-')} .".replace(" .", ".")
        placement = f"{actor} fails only {condition}."
        bare = f"{actor} only fails {condition}."
        careful = (f"{actor} fails {condition} and never {alternative}. "
                   f"This does not say that every occurrence {condition} causes a failure.")
        positive = (actor, "fails-sometimes", condition)
        excluded = {(actor, "fails-sometimes", alternative)}
        intended = (actor, "fails-sometimes", alternative)
        orthogonal = (actor, "fails-always", condition)

    def render(event, negative):
        who, act, what = event
        if act == "fails-sometimes":
            return f"{who} {'never fails' if negative else 'sometimes fails'} {what}."
        if act == "fails-always":
            return f"{who} fails on every occurrence {what}."
        # Avoid inflecting arbitrary past-tense verbs mechanically.
        clause = f"{who} {act} {what}"
        return f"It is not the case that {clause}." if negative else clause + "."

    probes = []
    for axis, event, negative in (("intended", intended, intended_negative),
                                   ("orthogonal", orthogonal, False)):
        answer = truth((event, negative), {positive}, excluded)
        probes.append({"axis": axis, "statement": render(event, negative), "answer": answer,
                       "event": event, "negated": negative})
    assert probes[0]["answer"] != "Not determined" and probes[1]["answer"] == "Not determined"
    return {"id": f"of13-{site}-{index + 1:02d}", "site": site, "context": context,
            "claims": {"marked": marked, "careful": careful, "placement": placement, "bare": bare},
            "asserted": [positive], "excluded": sorted(excluded), "probes": probes}


def generate():
    worlds = [frame(site, i) for site in ("subject", "verb", "nominal", "adjunct") for i in range(24)]
    assert len({w["id"] for w in worlds}) == 96
    controls = [i for i in json.loads((PRIOR / "rent-one-reader-runspec.json").read_text())["items"]
                if i.get("calibration")]
    assert len(controls) == 8
    files = {}
    for contrast in ("careful", "placement", "bare"):
        items = []
        for number, world in enumerate(worlds):
            for probe in world["probes"]:
                options = LABELS[(number + (probe["axis"] == "orthogonal")) % 3:]
                options += LABELS[:(number + (probe["axis"] == "orthogonal")) % 3]
                item = {
                    "id": world["id"] + "-" + probe["axis"],
                    "english": world["context"] + "\nNote: " + world["claims"][contrast],
                    "ainglish": world["context"] + "\nNote: " + world["claims"]["marked"],
                    "question": ("Considering only this note and its stated context, is this "
                                 "statement entailed, contradicted, or not determined? " + probe["statement"]),
                    "options": options, "answer": probe["answer"],
                    "settlement_stratum": world["site"] + "-" + probe["axis"],
                    "strata": {"world_id": world["id"], "focus_site": world["site"], "probe_axis": probe["axis"]},
                }
                assert item["answer"] in item["options"]
                items.append(item)
        items.extend(deepcopy(controls))
        name = f"only-focus-{contrast}-items.json"
        save(name, items)
        files[name] = digest(items)
    save("only-focus-worlds.json", worlds)
    save("only-focus-design-audit.json", {
        "worlds": 96, "target_items_per_contrast": 192, "contrasts": files,
        "focus_sites": dict(Counter(w["site"] for w in worlds)),
        "keys_per_contrast": dict(Counter(p["answer"] for w in worlds for p in w["probes"])),
        "oracle": "Explicit positive event and focal exclusion; all unclosed axes remain unknown.",
        "review": "Generated keys validated symbolically; requires main-agent text review before binding.",
    })


def bind(commit):
    from ainglish.panel import _planned_panel_manifest, prepare_reader_instruments
    from local_colony_auth import ainglish_client

    client = ainglish_client()
    proposal = client.proposal(PROPOSAL, authenticated=True)
    assert proposal["author_work_notices"]["active"] is None
    work = next(w for w in proposal["evidence_readiness"]["work_items"]
                if w["metric"] == "comprehension_accuracy_delta")
    assert work["state"] == "submit_original", work
    assert (HERE / "ONLY-FOCUS-REVIEW.md").exists(), "Text review must be recorded before binding"
    save("only-focus-proposal-contract.json", {k: proposal[k] for k in (
        "public_id", "slug", "form", "english_mapping", "predicted_measurement", "evidence_contract")})
    panels, qualifications = [], []
    for family in ("gemma", "mistral"):
        panels.append(json.loads((PRIOR / f"{family}-screen.json").read_text())["reader"])
        q = json.loads((PRIOR / f"{family}-qualification.json").read_text())
        assert q["status"] == "passed"
        qualifications.append(q["receipt"])
    for n, contrast in enumerate(("careful", "placement", "bare")):
        name = f"only-focus-{contrast}"
        items = json.loads((HERE / f"{name}-items.json").read_text())
        scope = (f"Cold-reader marked only-weld versus {contrast} English, in 96 templated focus-determinate worlds, "
                 "24 per focus site, two probes each, two exact qualified native readers. "
                 "One component original, not full-prediction certification or independent replication. "
                 "All three linked contrasts were frozen before any target exposure. "
                 "Bare-only contrast is descriptive ambiguity evidence, never the confirmatory denominator. "
                 "No fine tuning or tokenizer adaptation; English is the incumbent in both models.")
        spec = {
            "slug": proposal["slug"], "construct": "only-focus four-site core comprehension",
            "form": proposal["form"], "metric": "comprehension_accuracy_delta",
            "seed": 2026091321 + n, "panel_neff": 2, "panel": deepcopy(panels),
            "reader_qualifications": deepcopy(qualifications),
            "items": items, "items_sha256": digest(items),
            "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/completion-batch-2026-09-13/{name}-items.json",
            "settlement_strata": [{"id": site + "-" + axis, "weight": 1}
                                   for site in ("subject", "verb", "nominal", "adjunct")
                                   for axis in ("intended", "orthogonal")],
            "planted_arm": "ainglish", "calibration_min_gap": 0.5, "calibration_min_recovered": 0.75,
            "admissibility": {"kind": "ainglish.panel.admissibility.v1", "per_reader_calibration": True,
                              "max_off_option_cells": 0, "max_absent_cells": 0,
                              "max_truncated_cells": 0, "max_transport_fault_cells": 0},
            "study_purpose": "diagnostic" if contrast == "bare" else "claim_test", "study_scope": scope,
            "attempt": {
                "estimand": (scope + " Equal weight across eight focus-site/probe-axis strata. "
                             "Official item-bootstrap intervals are descriptive for these templated dependent probes; "
                             "also report frame-cluster sensitivity, per-reader/per-site accuracy, intended and orthogonal separately. "
                             "Do not count three contrasts or two models as independent participants. "
                             "The nominal +5/-5 and careful-English -5 noninferiority questions and verb/adjunct +10 "
                             "placement question must be reported separately, never inferred from the pooled top line."),
                "admissibility_gates": [
                    "All 96 worlds, 192 keys and three linked contrasts frozen and publicly pinned before target exposure",
                    "Valid exact-settings qualification and target-independent calibration before target calls",
                    "First finite single-pass result; retain null/adverse outcomes, no target-driven model or prompt substitution",
                    "Zero transport errors, truncation, missing or off-option cells; abort honestly on any fault",
                    "No composition, corruption, conditional carve-out, adoption or shortest-English certification from this component",
                    "Native SSD only; no new model downloads; two probe items per world are dependent",
                ],
                "planned_sample": {"worlds": 96, "items": 192, "calibration_items": 8,
                                   "readers": 2, "target_calls": 384, "calibration_calls": 32},
            },
        }
        prepare_reader_instruments(spec)
        planned = _planned_panel_manifest(spec)
        preflight = client.preflight_attempt(proposal["slug"], planned, **spec["attempt"])
        save(f"{name}-runspec.json", spec)
        save(f"{name}-planned-manifest.json", planned)
        save(f"{name}-preflight.json", preflight)
        print(name, json.dumps(preflight))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("generate", "bind"))
    parser.add_argument("--commit")
    args = parser.parse_args()
    if args.action == "generate":
        generate()
    else:
        assert args.commit and len(args.commit) == 40
        bind(args.commit)
