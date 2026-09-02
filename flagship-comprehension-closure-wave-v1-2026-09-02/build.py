#!/usr/bin/env python3
"""Build five frozen, careful-English comprehension carriers without inference."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_NEXT = ROOT.parent / "next-weekday-comprehension-carrier-v1-2026-08-30"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(items: list[dict]) -> str:
    return sha256(canonical(items)).hexdigest()


def joined(values: list[str]) -> str:
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return ", ".join(values[:-1]) + f", and {values[-1]}"


def choices(answer: str, distractors: list[str], index: int) -> list[str]:
    values = []
    for value in [answer, *distractors, "zero", "one", "the number is not specified", "none of these"]:
        if value not in values:
            values.append(value)
        if len(values) == 4:
            break
    assert len(values) == 4 and len(set(values)) == 4 and answer in values
    shift = index % 4
    return values[shift:] + values[:shift]


def calibrations(prefix: str) -> list[dict]:
    rows = []
    nouns = [
        ("amber token", "locker 7"), ("blue key", "locker 12"),
        ("cedar card", "drawer 4"), ("dune badge", "cabinet 9"),
        ("elm seal", "vault 3"), ("flint pass", "locker 15"),
        ("granite tag", "drawer 8"), ("hazel chip", "cabinet 2"),
        ("indigo note", "vault 11"), ("jade disk", "locker 5"),
        ("kelp token", "drawer 14"), ("linen key", "cabinet 6"),
        ("maple card", "vault 13"), ("nickel badge", "locker 10"),
        ("ochre seal", "drawer 1"), ("pearl pass", "cabinet 16"),
    ]
    for i, (thing, location) in enumerate(nouns):
        alternatives = ["the dispatch desk", "the archive room", "the location is not stated"]
        rows.append({
            "id": f"{prefix}-cal-{i + 1:02d}",
            "calibration": True,
            "english": f"A sealed inventory note mentions the {thing}, but gives no location.",
            "ainglish": f"A sealed inventory note states that the {thing} is in {location}.",
            "question": f"Where does the note state that the {thing} is?",
            "options": choices(location, alternatives, i),
            "answer": location,
            "probe": "construct-free explicit-location planted effect",
        })
    return rows


def pair_items() -> list[dict]:
    people = [
        ["Ari", "Bela"], ["Cato", "Dina", "Eli"],
        ["Faye", "Gus", "Hana", "Ivo"], ["Jae", "Kira"],
        ["Lio", "Mina", "Noor"], ["Oren", "Pia", "Quin", "Ravi"],
        ["Sana", "Teo"], ["Uma", "Vik", "Wren"],
    ]
    objects = [
        ["patch A", "patch B"], ["queue red", "queue blue", "queue gold"],
        ["probe 1", "probe 2", "probe 3", "probe 4"], ["ledger east", "ledger west"],
        ["service alpha", "service beta", "service gamma"], ["shard K", "shard L", "shard M", "shard N"],
        ["manual 7", "manual 9"], ["dataset cedar", "dataset birch", "dataset maple"],
    ]
    relations = [
        ("review", "reviews", "review"), ("monitor", "monitors", "monitoring"),
        ("calibrate", "calibrates", "calibration"), ("audit", "audits", "audit"),
        ("inspect", "inspects", "inspection"), ("index", "indexes", "indexing"),
        ("translate", "translates", "translation"), ("replicate", "replicates", "replication"),
    ]
    rows = []
    for i in range(32):
        actors = people[i % len(people)]
        targets = objects[i % len(objects)]
        verb, third, noun = relations[i % len(relations)]
        # pair-by-order requires equal finite lists.
        n = min(len(actors), len(targets))
        actors_p = actors[:n]
        targets_p = targets[:n]
        clauses = [f"{actor} {third} {target}" for actor, target in zip(actors_p, targets_p)]
        answer = str(n)
        rows.append({
            "id": f"pair-topology-pair-{i + 1:02d}",
            "english": f"In assignment set {i + 1}, {joined(clauses)}: exactly {n} position-matched assignments and no crossed links.",
            "ainglish": f"In assignment set {i + 1}, {joined(actors_p)} {verb} {joined(targets_p)}, pair-by-order.",
            "question": f"How many actor-target {noun} assignments does the instruction assert?",
            "options": choices(answer, [str(n * n), "zero", "the number is not specified"], i),
            "answer": answer,
            "form": "pair-by-order",
            "settlement_stratum": "pair-by-order",
            "strata": {"actors": n, "targets": n, "expected_relations": n},
        })
        actors_e = actors
        targets_e = objects[(i + 3) % len(objects)]
        total = len(actors_e) * len(targets_e)
        answer = str(total)
        rows.append({
            "id": f"pair-topology-every-{i + 1:02d}",
            "english": f"In assignment set {i + 1}, {joined(actors_e)} each {verb} every one of {joined(targets_e)}: all {total} actor-target assignments occur.",
            "ainglish": f"In assignment set {i + 1}, {joined(actors_e)} {verb} {joined(targets_e)}, every-combination.",
            "question": f"How many actor-target {noun} assignments does the instruction assert?",
            "options": choices(answer, [str(len(actors_e)), str(len(targets_e)), "the number is not specified"], i + 1),
            "answer": answer,
            "form": "every-combination",
            "settlement_stratum": "every-combination",
            "strata": {"actors": len(actors_e), "targets": len(targets_e), "expected_relations": total},
        })
    return rows + calibrations("pair-topology")


def must_items() -> list[dict]:
    cases = [
        ("the signer", "be Alice", "is Alice", "Alice is not the signer", "the release rule"),
        ("the gateway", "reject unsigned requests", "rejects unsigned requests", "an unsigned request was accepted", "the security policy"),
        ("the archive", "retain the receipt", "retains the receipt", "the receipt is missing", "the retention specification"),
        ("the worker", "use the approved image", "uses the approved image", "an unapproved image was used", "the deployment instruction"),
        ("the report", "include the checksum", "includes the checksum", "the checksum is absent", "the reporting standard"),
        ("the reviewer", "be independent", "is independent", "the reviewer is linked to the author", "the review rule"),
        ("the key", "remain offline", "remains offline", "the key was connected", "the custody policy"),
        ("the request", "carry a nonce", "carries a nonce", "the nonce is absent", "the protocol"),
        ("the build", "finish before noon", "finishes before noon", "the build finished after noon", "the release schedule"),
        ("the dataset", "exclude personal records", "excludes personal records", "a personal record is present", "the data policy"),
        ("the ballot", "remain open for one day", "remains open for one day", "the ballot closed early", "the governance rule"),
        ("the replica", "match the digest", "matches the digest", "the digest differs", "the integrity requirement"),
        ("the operator", "record every abort", "records every abort", "an abort was not recorded", "the audit instruction"),
        ("the client", "refuse an unknown mode", "refuses an unknown mode", "an unknown mode was accepted", "the fail-closed contract"),
        ("the package", "include the licence", "includes the licence", "the licence is absent", "the publication requirement"),
        ("the runner", "mint before inference", "mints before inference", "inference began before minting", "the measurement protocol"),
    ]
    rows = []
    for i in range(32):
        subject, proposition, finite, contrary, basis = cases[i % len(cases)]
        suffix = "" if i < 16 else f" in test case {i + 1}"
        rule_answer = "an applicable requirement was breached"
        inference_answer = "the stated inference was mistaken"
        distractors = ["a requirement was created by the evidence", "both consequences necessarily follow", "neither consequence follows"]
        rows.append({
            "id": f"must-force-rule-{i + 1:02d}",
            "english": f"{basis.capitalize()} requires {subject} to {proposition}{suffix}; this states a duty, not a conclusion that the proposition currently holds.",
            "ainglish": f"{subject.capitalize()} must-as-rule {proposition}{suffix}.",
            "question": f"Suppose {contrary}. Which consequence follows from the message?",
            "options": choices(rule_answer, distractors, i),
            "answer": rule_answer,
            "form": "must-as-rule",
            "settlement_stratum": "must-as-rule",
            "strata": {"basis": basis, "probe": "false-proposition consequence"},
        })
        rows.append({
            "id": f"must-force-inference-{i + 1:02d}",
            "english": f"The available evidence supports the conclusion that {subject} {finite}{suffix}; this reports an inference and creates no duty.",
            "ainglish": f"{subject.capitalize()} must-as-inference {proposition}{suffix}; the available evidence points to that conclusion.",
            "question": f"Suppose {contrary}. Which consequence follows from the message?",
            "options": choices(inference_answer, ["an applicable requirement was breached", "a new duty was created", "both consequences necessarily follow"], i + 1),
            "answer": inference_answer,
            "form": "must-as-inference",
            "settlement_stratum": "must-as-inference",
            "strata": {"basis": "available evidence", "probe": "false-proposition consequence"},
        })
    return rows + calibrations("must-force")


def retry_items() -> list[dict]:
    actions = [
        "Fetch report A", "Validate archive B", "Query replica C", "Upload bundle D",
        "Index shard E", "Rotate key F", "Render page G", "Check endpoint H",
    ]
    rows = []
    for i in range(32):
        action = f"{actions[i % len(actions)]} for job reference {i + 1}"
        extra = i % 8
        total = (i % 8) + 1
        max_extra = extra + 1
        extra_word = "execution" if extra == 1 else "executions"
        max_word = "execution" if max_extra == 1 else "executions"
        total_word = "execution" if total == 1 else "executions"
        rows.append({
            "id": f"retry-basis-extra-{i + 1:02d}",
            "english": f"Make at most one initial execution of “{action}” and, if success is not established, at most {extra} additional {extra_word}: at most {max_extra} {max_word} altogether.",
            "ainglish": f"{action}, extra-retries({extra}).",
            "question": "What is the maximum total number of executions permitted, counting the initial execution?",
            "options": choices(str(max_extra), [str(extra), str(max_extra + 1), "the maximum is not specified"], i),
            "answer": str(max_extra),
            "form": "extra-retries",
            "settlement_stratum": "extra-retries",
            "strata": {"n": extra, "maximum_executions": max_extra},
        })
        rows.append({
            "id": f"retry-basis-total-{i + 1:02d}",
            "english": f"Make at most {total} {total_word} of “{action}” altogether, including the first execution.",
            "ainglish": f"{action}, total-attempts({total}).",
            "question": "What is the maximum total number of executions permitted, counting the initial execution?",
            "options": choices(str(total), [str(total + 1), str(max(0, total - 1)), "the maximum is not specified"], i + 1),
            "answer": str(total),
            "form": "total-attempts",
            "settlement_stratum": "total-attempts",
            "strata": {"n": total, "maximum_executions": total},
        })
    return rows + calibrations("retry-basis")


def retention_items() -> list[dict]:
    sets = [
        ("grant", ["Atlas access", "Beacon access", "Cedar access"]),
        ("publish", ["the policy", "the schema", "the examples"]),
        ("download", ["mirror A", "mirror B", "mirror C"]),
        ("apply", ["account change red", "account change blue", "account change gold"]),
        ("re-index", ["partition 1", "partition 2", "partition 3"]),
        ("write", ["ledger X", "ledger Y", "ledger Z"]),
        ("deploy", ["service north", "service south", "service west"]),
        ("archive", ["record K", "record L", "record M"]),
    ]
    rows = []
    no_answer = "none of the successful effects may remain authoritative"
    yes_answer = "the successful effects remain authoritative"
    for i in range(32):
        verb, members = sets[i % len(sets)]
        action = f"For batch {i + 1}, {verb} {joined(members)}"
        failed = members[(i + 1) % 3]
        rows.append({
            "id": f"retention-policy-atomic-{i + 1:02d}",
            "english": f"{action}. If any member fails, leave none of the other member effects committed or safe to rely on as the terminal result.",
            "ainglish": f"{action}, all-or-nothing.",
            "question": f"Suppose one member ({failed}) fails after another member provisionally succeeds. What may remain authoritative at the terminal outcome?",
            "options": choices(no_answer, [yes_answer, "the whole set is treated as successful", "the retention policy is not specified"], i),
            "answer": no_answer,
            "form": "all-or-nothing",
            "settlement_stratum": "all-or-nothing",
            "strata": {"members": 3, "probe": "terminal successful-effect retention"},
        })
        rows.append({
            "id": f"retention-policy-partial-{i + 1:02d}",
            "english": f"{action}. If one member fails, keep every other member effect that succeeded and report the failed member separately.",
            "ainglish": f"{action}, keep-successes.",
            "question": f"Suppose one member ({failed}) fails after another member succeeds. What may remain authoritative at the terminal outcome?",
            "options": choices(yes_answer, [no_answer, "the whole set is treated as successful", "the retention policy is not specified"], i + 1),
            "answer": yes_answer,
            "form": "keep-successes",
            "settlement_stratum": "keep-successes",
            "strata": {"members": 3, "probe": "terminal successful-effect retention"},
        })
    return rows + calibrations("retention-policy")


def next_weekday_items() -> list[dict]:
    combined = []
    for name, form in (("items-next-up-careful.json", "next-up"), ("items-next-week-careful.json", "next-week")):
        payload = json.loads((SOURCE_NEXT / name).read_text(encoding="utf-8"))
        for item in payload["items"]:
            row = dict(item)
            if row.get("calibration"):
                continue
            row["options"] = [value.replace("(+-", "(-").replace("(+1 days)", "(+1 day)") for value in row["options"]]
            row["answer"] = row["answer"].replace("(+-", "(-").replace("(+1 days)", "(+1 day)")
            row["settlement_stratum"] = form
            combined.append(row)
    # Replace the older equal-arm format controls with target-independent planted-effect controls.
    return combined + calibrations("next-weekday")


def write(name: str, slug: str, construct: str, items: list[dict], strata: list[str], execution: str) -> dict:
    payload = {
        "kind": "dexagon.ainglish.flagship-comprehension-closure-carrier.v1",
        "proposal_revision": slug,
        "construct": construct,
        "comparison": "complete-careful-English mapping versus the registered compact form",
        "reader_calls": 0,
        "items": items,
    }
    path = ROOT / f"{name}.items.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    real = [row for row in items if not row.get("calibration")]
    cal = [row for row in items if row.get("calibration")]
    counts = Counter(row["settlement_stratum"] for row in real)
    return {
        "name": name,
        "slug": slug,
        "construct": construct,
        "file": path.name,
        "items_sha256": digest(items),
        "scientific_items": len(real),
        "calibration_items": len(cal),
        "settlement_strata": [{"id": value, "weight": 1} for value in strata],
        "stratum_counts": dict(sorted(counts.items())),
        "execution": execution,
    }


def main() -> None:
    campaigns = [
        write("pair-topology", "pair-by-order-every-combination-match-two-lists-in-order-or-", "pair-by-order / every-combination", pair_items(), ["pair-by-order", "every-combination"], "Dexagon may file an eligible original"),
        write("must-force", "must-as-rule-must-as-inference-does-must-impose-a-requiremen", "must-as-rule / must-as-inference", must_items(), ["must-as-rule", "must-as-inference"], "Dexagon may file an eligible original"),
        write("retry-basis", "extra-retries-n-total-attempts-n-does-three-retries-permit-t", "extra-retries / total-attempts", retry_items(), ["extra-retries", "total-attempts"], "Dexagon may file an eligible original"),
        write("retention-policy", "all-or-nothing-keep-successes-say-what-survives-when-part-of-2", "all-or-nothing / keep-successes", retention_items(), ["all-or-nothing", "keep-successes"], "handoff only: Dexagon is the proposer"),
        write("next-weekday", "next-up-day-date-next-week-day-date-weekstart-which-next-fri", "next-up / next-week", next_weekday_items(), ["next-up", "next-week"], "Dexagon may file an eligible original"),
    ]
    index = {
        "kind": "dexagon.ainglish.flagship-comprehension-closure-wave.v1",
        "model_calls": 0,
        "campaigns": {row["name"]: row for row in campaigns},
    }
    index["content_sha256"] = sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
