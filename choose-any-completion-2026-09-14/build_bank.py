"""Deterministic DRAFT instrument generation. No models, tokenizers, credentials or network.

Each scenario is ONE official-panel item. Its four answer records are the Cartesian product
of two policy-set answers and two guarantee-set answers. This retains separate probe scores
without treating different reader/arm assignments as an observed joint answer.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

SEED = 2026091451
FORMS = ("choose-any", "draw-uniform")
DOMAINS = (
    ("service-routing", "the next health request", "service endpoint", "latency"),
    ("reviewer-assignment", "the next manuscript", "reviewer", "queue length"),
    ("evaluation-item-selection", "the next evaluation slot", "evaluation item", "preparation cost"),
    ("failover", "the next failover request", "standby node", "activation cost"),
    ("content-choice", "the next content slot", "content item", "retrieval cost"),
    ("resource-allocation", "the next workload", "worker", "current load"),
)
NAMES = ("Juniper", "Kestrel", "Cobalt", "Saffron", "Tundra", "Harbour", "Quartz", "Orchard")
FRAMES = (
    "An operator is preparing {task}.",
    "A scheduler has reached the selection step for {task}.",
    "An auditor is checking the instruction for {task} before anything runs.",
    "A queued job needs one selection for {task}.",
    "A runbook records the next selection for {task}.",
    "The previous job is finished; this separate request concerns {task}.",
    "An implementation team is reviewing the request for {task}.",
    "Two engineers are checking the selection contract for {task}.",
    "A task handover contains an instruction for {task}.",
    "A test environment is about to exercise the selection step for {task}.",
    "The logged request has not been executed; it concerns {task}.",
    "A dispatcher has received the following selection request for {task}.",
)

def canonical(value):
    # This bank has string keys, integers, booleans and strings; no floats or exotic key order.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def make_world(index, form, domain_index, local_index):
    domain, task, member_type, criterion = DOMAINS[domain_index]
    n = 2 + (local_index + 2 * domain_index + FORMS.index(form)) % 7
    ref = f"selection-{domain}-{form}-{local_index + 1:03d}@r1"
    members = [f"{NAMES[j]}-{domain_index + 1}{local_index + 1:03d}" for j in range(n)]
    outsider = f"Outpost-{domain_index + 1}{local_index + 1:03d}"
    # Unique criterion scores; its chosen member is distinct from the constant-first choice.
    scores = [n + 10] + list(range(1, n))
    common = (
        FRAMES[local_index % len(FRAMES)].format(task=task) + "\n"
        f"Eligible {member_type} identities, in order: {', '.join(members)}. "
        f"Their {criterion} scores in that order are {', '.join(map(str, scores))}. "
        f"The named set {ref} is this frozen, nonempty snapshot of distinct identities. "
        f"{outsider} is not a member. No other requirements have been added."
    )
    ainglish = common + f"\nRequest: {form}({ref})."
    if form == "choose-any":
        expansion = (
            f"Choose exactly one member of {ref}; every member is acceptable and the selection "
            "policy is otherwise unconstrained. A deterministic first-member rule, a criterion-based "
            "rule, a weighted rule, or a uniform draw may be used. This makes no claim of randomness, "
            "equal probability, unpredictability, independence, rotation, or fairness."
        )
    else:
        expansion = (
            f"Make exactly one stochastic draw from {ref}. Conditional on this frozen eligibility "
            f"set and before the outcome is known, each distinct member identity has probability "
            f"exactly 1/{n} of being returned. This does not by itself promise cryptographic "
            "unpredictability, public verifiability, independence between repeated draws, sampling "
            "with or without replacement, or a balanced finite run; it specifies one draw only."
        )
    english = common + "\nRequest: " + expansion
    return {
        "id": f"ca-completion-{index + 1:04d}", "form": form, "domain": domain,
        "frame_family": f"frame-{local_index % len(FRAMES):02d}",
        "n": n, "set_ref": ref, "members": members, "outsider": outsider,
        "scores": scores, "criterion": criterion, "english": english, "ainglish": ainglish,
    }

def implementations(world):
    members, n, outsider = world["members"], world["n"], world["outsider"]
    smallest = members[world["scores"].index(min(world["scores"]))]
    rows = [
        {"kind": "constant-first", "text": f"Always returns {members[0]}; no other result can occur.",
         "distribution": {members[0]: "1"}},
        {"kind": "criterion-based", "text": f"Always returns {smallest}, the identity with the lowest {world['criterion']} score.",
         "distribution": {smallest: "1"}},
        {"kind": "unequal-weight", "text": f"Returns {members[0]} with probability 2/{n+1} and each other listed identity with probability 1/{n+1}.",
         "distribution": {x: str(Fraction(2 if j == 0 else 1, n+1)) for j, x in enumerate(members)}},
        {"kind": "equal-probability", "text": f"Returns one listed identity, with probability 1/{n} assigned to each identity before the draw.",
         "distribution": {x: str(Fraction(1, n)) for x in members}},
        {"kind": "out-of-set", "text": f"Always returns {outsider}; no other result can occur.",
         "distribution": {outsider: "1"}},
    ]
    random.Random(f"{SEED}:{world['id']}:policies").shuffle(rows)
    for i, row in enumerate(rows, 1):
        row["label"] = f"P{i}"
    return rows

def admissible(world, policy):
    distribution = {key: Fraction(value) for key, value in policy["distribution"].items()}
    if sum(distribution.values()) != 1 or any(v < 0 for v in distribution.values()):
        raise ValueError("Not a probability distribution")
    if not set(distribution).issubset(world["members"]):
        return False
    if world["form"] == "choose-any":
        return True
    return all(distribution.get(member, 0) == Fraction(1, world["n"]) for member in world["members"])

def make_item(world, index):
    policies = implementations(world)
    allowed = {r["label"] for r in policies if admissible(world, r)}
    contrast_kind = ("constant-first", "criterion-based", "unequal-weight", "equal-probability", "out-of-set")[(index // 2) % 5]
    toggled = next(p["label"] for p in policies if p["kind"] == contrast_kind)
    wrong_allowed = allowed ^ {toggled}
    guarantees = [
        {"key": "one-eligible", "text": "The returned identity belongs to the listed snapshot and there is exactly one result."},
        {"key": "equal-odds", "text": "Before this selection happens, each listed identity has the same chance of being returned."},
        {"key": "crypto-unpredictable", "text": "A well-informed adversary cannot predict the result better than chance."},
        {"key": "cross-draw-independent", "text": "Knowing this result does not change the probability distribution of a later selection."},
    ]
    random.Random(f"{SEED}:{world['id']}:guarantees").shuffle(guarantees)
    for i, row in enumerate(guarantees, 1):
        row["label"] = f"G{i}"
    true_keys = {"one-eligible"} | ({"equal-odds"} if world["form"] == "draw-uniform" else set())
    true_guarantees = {r["label"] for r in guarantees if r["key"] in true_keys}
    contrast_key = ("one-eligible", "equal-odds", "crypto-unpredictable", "cross-draw-independent")[(index // 2 + FORMS.index(world["form"])) % 4]
    contrasted_guarantee = next(g for g in guarantees if g["key"] == contrast_key)
    wrong_guarantees = true_guarantees ^ {contrasted_guarantee["label"]}
    profiles = []
    for policy_correct, guarantee_correct in ((True, True), (True, False), (False, True), (False, False)):
        pset = allowed if policy_correct else wrong_allowed
        gset = true_guarantees if guarantee_correct else wrong_guarantees
        profiles.append({"policies": sorted(pset), "guarantees": sorted(gset),
                         "policy_correct": policy_correct, "guarantee_correct": guarantee_correct})
    # Balance answer positions without making the guarantee under test reveal the answer index.
    position_order = list(range(4))
    random.Random(f"{SEED}:{world['form']}:positions:{(index // 2) // 4}").shuffle(position_order)
    offset = position_order[(index // 2) % 4]
    profiles = profiles[-offset:] + profiles[:-offset] if offset else profiles
    options, option_records = [], {}
    for profile in profiles:
        label = ("Implementations: " + (", ".join(profile["policies"]) or "none")
                 + "; claims: " + (", ".join(profile["guarantees"]) or "none") + ".")
        options.append(label)
        option_records[label] = profile
    correct = options[offset]
    question = (
        "An engineer must select compliant implementations, and an auditor must list claims "
        "that the request itself establishes. Evaluate these two decisions separately, then choose "
        "the record containing BOTH complete lists. A procedure being permitted does not make its "
        "extra properties a promise of the request.\n\nCandidate implementations (each returns once):\n"
        + "\n".join(f"{p['label']}: {p['text']}" for p in policies)
        + "\n\nAuditor's possible claims:\n"
        + "\n".join(f"{g['label']}: {g['text']}" for g in guarantees)
    )
    return {
        "id": world["id"], "english": world["english"], "ainglish": world["ainglish"],
        "question": question, "options": options, "answer": correct,
        "settlement_stratum": world["form"], "domain": world["domain"],
        "frame_family": world["frame_family"], "member_count": world["n"],
        "probe_contract": {
            "kind": "joint-cartesian-two-probe-v1", "option_records": option_records,
            "policies": policies, "guarantees": guarantees,
            "policy_contrast": next(p["kind"] for p in policies if p["label"] == toggled),
            "guarantee_contrast": contrasted_guarantee["key"],
            "policy_gold": sorted(allowed), "guarantee_gold": sorted(true_guarantees),
        },
        "semantic_world": {key: world[key] for key in ("form", "domain", "n", "members", "outsider", "scores", "criterion", "set_ref")},
    }

def generate(count=144):
    if count < 144 or count % 12:
        raise ValueError("Use at least 144 worlds, balanced across two forms and six domains")
    per_cell = count // 12
    items = []
    # Interleave forms/domains so changed sample sizes never change earlier world IDs/contents.
    for local_index in range(per_cell):
        for domain_index in range(6):
            for form in FORMS:
                index = len(items)
                items.append(make_item(make_world(index, form, domain_index, local_index), index))
    return items

def probe_scores(item, answer):
    record = item["probe_contract"]["option_records"].get(answer)
    if record is None:
        return {"joint": False, "implementation": False, "guarantees": False,
                "unrecognised": True, "policy_bits": None, "guarantee_bits": None}
    p = item["probe_contract"]
    pset, gset = set(record["policies"]), set(record["guarantees"])
    return {"joint": pset == set(p["policy_gold"]) and gset == set(p["guarantee_gold"]),
            "implementation": pset == set(p["policy_gold"]), "guarantees": gset == set(p["guarantee_gold"]),
            "unrecognised": False,
            "policy_bits": {row["kind"]: row["label"] in pset for row in p["policies"]},
            "guarantee_bits": {row["key"]: row["label"] in gset for row in p["guarantees"]}}

def summarize(items):
    return {
        "status": "DRAFT_NOT_APPROVED_FOR_INFERENCE",
        "real_scenarios": len(items), "items_sha256": digest(items),
        "forms": dict(Counter(x["settlement_stratum"] for x in items)),
        "form_domain": dict(Counter(x["settlement_stratum"] + "/" + x["domain"] for x in items)),
        "member_counts": dict(sorted(Counter(x["member_count"] for x in items).items())),
        "answer_positions": dict(sorted(Counter(x["options"].index(x["answer"]) for x in items).items())),
        "policy_contrasts": dict(Counter(x["settlement_stratum"] + "/" + x["probe_contract"]["policy_contrast"] for x in items)),
        "guarantee_contrasts": dict(Counter(x["settlement_stratum"] + "/" + x["probe_contract"]["guarantee_contrast"] for x in items)),
        "frame_families": len({x["frame_family"] for x in items}),
        "sampling_warning": "Authored frame families are correlated; item count is not independent natural-language diversity.",
        "exposure_warning": "A forced choice reveals responses among the offered records, not unrestricted recall of every possible misconception.",
        "launch_gates": ["public author/acceptance decision", "independent semantic review", "precision design agreed",
                         "full prior-input freshness audit", "qualified exact reader roster", "final immutable freeze and live preflight/mint"],
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=144)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "draft")
    args = parser.parse_args()
    items = generate(args.count)
    args.out.mkdir(parents=True, exist_ok=True)
    artifact = {"kind": "ainglish.choose-any.review-draft.v1", "status": "DRAFT_NOT_APPROVED_FOR_INFERENCE",
                "items_sha256": digest(items), "items": items}
    (args.out / "items.json").write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
    (args.out / "coverage.json").write_text(json.dumps(summarize(items), indent=2) + "\n")
    print(json.dumps(summarize(items), indent=2))

if __name__ == "__main__":
    main()
