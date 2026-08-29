#!/usr/bin/env python3
"""Freeze full-comparator carriers for six progression rows and one flagship gap."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Callable


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from evidence_factory.design import EvidenceDesign  # noqa: E402


YES_NO_UNKNOWN = ["yes", "no", "not stated"]
NAMES = [
    "Amina", "Bela", "Chen", "Dara", "Eli", "Farah", "Gia", "Haru", "Inez", "Joon",
    "Kavi", "Lina", "Miro", "Nia", "Oren", "Priya", "Quin", "Ravi", "Sela", "Tari",
    "Uma", "Vera", "Wynn", "Xara", "Yuki", "Zane", "Anik", "Bria", "Cato", "Demi",
]
GROUPS = [
    "reviewers", "operators", "curators", "inspectors", "maintainers", "analysts",
    "dispatchers", "auditors", "archivists", "coordinators", "stewards", "technicians",
]
OBJECTS = [
    "harbour ledger", "wildfire route map", "museum loan file", "satellite pointing table",
    "accessibility report", "water-quality dashboard", "cold-chain log", "ferry manifest",
    "court index bundle", "quarantine certificate", "grid restoration schedule",
    "shelter roster", "telescope calibration sheet", "trial codebook", "seed-vault inventory",
    "aircraft load sheet", "floodgate plan", "radio licence dossier", "field coordinate map",
    "quota table", "release checklist", "incident record", "backup catalogue", "model card",
    "safety bulletin", "procurement schedule", "translation memory", "service runbook",
    "ballot receipt", "dependency lockfile",
]
ACTIONS = [
    "approved", "inspected", "verified", "signed", "published", "archived", "reconciled",
    "opened", "sealed", "restored", "exported", "reviewed", "transmitted", "validated",
    "indexed", "tested", "delivered", "rotated", "replayed", "annotated",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_frozen(path: Path, value: object) -> None:
    rendered = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != rendered:
        raise SystemExit(f"REFUSING: frozen artifact drift: {path.name}")
    if not path.exists():
        path.write_text(rendered, encoding="utf-8")


def safe(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def placed(options: list[str], answer: str, position: int) -> list[str]:
    assert answer in options and len(set(options)) == len(options)
    rest = [option for option in options if option != answer]
    result = rest[:]
    result.insert(position % len(options), answer)
    return result


def calibration_rows(prefix: str, offset: int) -> list[dict]:
    rows = []
    for index in range(12):
        bay = 120 + offset + index
        answer = f"bay {bay}"
        options = [answer, f"bay {bay + 1}", "dispatch", "not stated"]
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The control memo marks parcel {offset + index + 1} with zep({bay}), but gives no rule for zep.",
            "ainglish": f"Control rule: zep(N) means the marked parcel is stored in bay N. The control memo marks parcel {offset + index + 1} with zep({bay}).",
            "question": "Where does the supplied control rule place the parcel?",
            "options": placed(options, answer, index),
            "answer": answer,
            "calibration_construct": "target-independent zep location marker",
            "calibration_scope": "target-independent",
        })
    return rows


def probe(
    seam: str,
    question: str,
    options: list[str],
    answer: str,
) -> dict:
    return {"seam": seam, "question": question, "options": options, "answer": answer}


def they_number(form: str, index: int, case: int) -> dict:
    scenario = index // 4
    person = NAMES[scenario % len(NAMES)]
    group = GROUPS[(scenario * 5 + 2) % len(GROUPS)]
    obj = OBJECTS[(scenario * 7 + 3) % len(OBJECTS)]
    action = ACTIONS[(scenario * 3 + 4) % len(ACTIONS)]
    context = f"Case {case}: {person} briefed the {group} beside the {obj}; either antecedent remains a live subject of the next clause."
    clause = f"They {action} record {case}."
    marked = f"{context} {form} {action} record {case}."
    bare = f"{context} {clause}"
    if form == "they-one":
        careful = f"{context} The pronoun denotes exactly one actor, without specifying gender or identity; that one actor {action} record {case}. This does not say every {group[:-1] if group.endswith('s') else group} acted or that anyone acted collectively."
        count, at_least_two, one_suffices = "exactly one", "no", "yes"
    else:
        careful = f"{context} The pronoun denotes two or more actors; those actors {action} record {case}. This does not say every member of the {group} acted, that they were unanimous, or that they acted collectively."
        count, at_least_two, one_suffices = "two or more", "yes", "no"
    return {
        "ainglish": marked,
        "careful": careful,
        "bare": bare,
        "probes": [
            probe("referent-number", "How many actors does the subject pronoun denote?", ["exactly one", "two or more", "not stated"], count),
            probe("lower-bound", "Does the sentence establish that at least two actors performed the action?", YES_NO_UNKNOWN, at_least_two),
            probe("single-sufficiency", "Could exactly one actor satisfy the subject-number claim in this sentence?", YES_NO_UNKNOWN, one_suffices),
            probe("all-members-nonclaim", "Does the sentence establish that every member of the salient group performed the action?", YES_NO_UNKNOWN, "not stated"),
        ],
        "metadata": {"antecedent_order": "singular-then-plural", "subject_type": ["human", "agent", "entity"][scenario % 3]},
    }


ENUMERATION_DOMAINS = [
    ("retryable status codes", "408", "429", "503"),
    ("accepted export formats", "CSV", "Parquet", "JSON"),
    ("admitted hosts", "iris.example", "larch.example", "cedar.example"),
    ("allowlisted principals", "agent-a", "agent-b", "agent-c"),
    ("granted permissions", "read", "comment", "deploy"),
    ("supported dependencies", "atlas", "birch", "coral"),
    ("valid tags", "stable", "reviewed", "urgent"),
    ("billable fee classes", "storage", "egress", "priority"),
]


def enumeration(form: str, index: int, case: int) -> dict:
    scenario = index // 4
    kind, first, second, unlisted = ENUMERATION_DOMAINS[scenario % len(ENUMERATION_DOMAINS)]
    scope = f"revision R{case}"
    listed = f"{first}, {second}"
    marked = f"Case {case}: Under {scope}, the {kind} are {listed}, {form}."
    bare = f"Case {case}: Under {scope}, the {kind} are {listed}."
    if form == "among-others":
        careful = f"Case {case}: Under {scope}, {first} and {second} are claimed members of the {kind}; this is not claimed to be a complete list, so unlisted same-kind candidates are neither admitted nor excluded by this message. Listed membership does not warrant that a member works."
        unlisted_answer, whole_answer = "not claimed either way", "not stated"
    else:
        careful = f"Case {case}: Under {scope}, {first} and {second}, and no other items of the same kind in that scope, are claimed members of the {kind}. Listed membership does not warrant that a member works."
        unlisted_answer, whole_answer = "claimed excluded", "yes"
    return {
        "ainglish": marked,
        "careful": careful,
        "bare": bare,
        "probes": [
            probe("unlisted-consequence", f"Per the message, what is claimed about using {unlisted}?", ["claimed admitted", "claimed excluded", "not claimed either way"], unlisted_answer),
            probe("listed-membership", f"Per the message, what is claimed about using {first}?", ["claimed admitted", "claimed excluded", "not claimed either way"], "claimed admitted"),
            probe("closure-bit", "Does the message establish that no unlisted same-kind item is admitted within the stated scope?", YES_NO_UNKNOWN, whole_answer),
            probe("health-nonclaim", f"Does the message establish that {second} works correctly?", YES_NO_UNKNOWN, "not stated"),
        ],
        "metadata": {"domain": kind, "scope": scope, "listed": [first, second], "unlisted": unlisted},
    }


ROLES = ["reviewer", "operator", "curator", "inspector", "maintainer", "analyst", "steward", "technician"]


def role_cardinality(form: str, index: int, case: int) -> dict:
    scenario = index // 4
    role = ROLES[scenario % len(ROLES)]
    obj = OBJECTS[(scenario * 5 + 1) % len(OBJECTS)]
    count = scenario % 3
    observation = {
        0: f"After the deadline, no distinct {role} had signed the {obj}.",
        1: f"After the deadline, one distinct {role} had signed the {obj} twice.",
        2: f"After the deadline, two distinct {role}s had each signed the {obj}.",
    }[count]
    bare_rule = f"A {role} must sign the {obj}."
    marked_rule = f"{form}({role}): must sign the {obj}."
    if form == "one-or-more":
        careful_rule = f"At least one distinct {role} must sign the {obj}; additional qualifying principals are permitted, and repeated signatures by one principal do not increase the principal count."
        satisfied = "yes" if count >= 1 else "no"
        extra = "yes"
    else:
        careful_rule = f"One and only one distinct {role} must sign the {obj}; zero or two-or-more qualifying principals violates the requirement, and repeated signatures by one principal do not increase the principal count."
        satisfied = "yes" if count == 1 else "no"
        extra = "no"
    prefix = f"Case {case}: {observation}"
    return {
        "ainglish": f"{prefix} Requirement: {marked_rule}",
        "careful": f"{prefix} Requirement: {careful_rule}",
        "bare": f"{prefix} Requirement: {bare_rule}",
        "probes": [
            probe("satisfaction", "Given the observed distinct-principal count, is the requirement satisfied?", YES_NO_UNKNOWN, satisfied),
            probe("additional-principal", "Does the requirement permit an additional qualifying principal beyond the first?", YES_NO_UNKNOWN, extra),
            probe("duplicate-performance", "Do two performances by the same principal count as two distinct qualifying principals?", YES_NO_UNKNOWN, "no"),
            probe("independence-nonclaim", "Does the role-count expression itself require decision independence between qualifying principals?", YES_NO_UNKNOWN, "not stated"),
        ],
        "metadata": {"role": role, "observed_distinct_principals": count, "voice": ["active", "passive"][scenario % 2]},
    }


CHANGE_EVENTS = [
    ("open", "opened", "gate", "open"), ("seal", "sealed", "hatch", "sealed"),
    ("empty", "emptied", "tank", "empty"), ("fill", "filled", "reservoir", "full"),
    ("unlock", "unlocked", "cabinet", "unlocked"), ("close", "closed", "bridge", "closed"),
    ("darken", "darkened", "room", "dark"), ("widen", "widened", "channel", "wide"),
]
FORCES = ["affirmative", "negated", "question", "directive"]


def repetition(form: str, index: int, case: int) -> dict:
    actor = NAMES[(index * 3 + 1) % len(NAMES)]
    base, past, noun, state = CHANGE_EVENTS[(index * 5 + 2) % len(CHANGE_EVENTS)]
    ref = f"{noun}-{case}"
    force = FORCES[(index // 16) % 4]
    if force == "affirmative":
        clause = f"{actor} {past} {ref}"
        bare_clause = f"{actor} {past} {ref} again"
        current = "occurred"
    elif force == "negated":
        clause = f"{actor} did not {base} {ref}"
        bare_clause = f"{clause} again"
        current = "did not occur"
    elif force == "question":
        clause = f"did {actor} {base} {ref}?"
        bare_clause = clause[:-1] + " again?"
        current = "not stated whether it occurred"
    else:
        clause = f"{base} {ref}"
        bare_clause = f"{clause} again"
        current = "requested, not asserted"
    if form == "repeat-event":
        marked = f"Case {case}: repeat-event: {clause}." if not clause.endswith("?") else f"Case {case}: repeat-event: {clause}"
        careful = f"Case {case}: The sentence backgrounds a matching earlier {past} event with the same resolved actor and object; its current clause is {force} and therefore the current event is {current}."
        basis = "matching earlier event by the resolved actor"
    else:
        marked = f"Case {case}: restore-state({state}({ref})): {clause}." if not clause.endswith("?") else f"Case {case}: restore-state({state}({ref})): {clause}"
        careful = f"Case {case}: The sentence backgrounds that {ref} was previously in the result state {state}, without establishing an earlier matching event or its actor; its current clause is {force} and therefore the current event is {current}."
        basis = "earlier result state without an established matching event"
    bare = f"Case {case}: {bare_clause}." if not bare_clause.endswith("?") else f"Case {case}: {bare_clause}"
    answers = [
        f"{basis}; current event occurred",
        f"{basis}; current event did not occur",
        f"{basis}; current occurrence is not stated",
        f"{basis}; current event is requested, not asserted",
    ]
    answer = {
        "affirmative": answers[0], "negated": answers[1], "question": answers[2], "directive": answers[3]
    }[force]
    other_basis = "earlier result state without an established matching event" if form == "repeat-event" else "matching earlier event by the resolved actor"
    distractors = [
        answer,
        answer.replace(basis, other_basis),
        f"{basis}; current occurrence is not stated" if force != "question" else f"{basis}; current event occurred",
        "no earlier condition is established; current event occurred",
    ]
    return {
        "ainglish": marked,
        "careful": careful,
        "bare": bare,
        "probes": [probe("basis-and-force", "Which earlier condition and current-event status does the sentence establish?", distractors, answer)],
        "metadata": {"force": force, "predicate_family": state, "actor": actor, "result_state": state},
    }


def restore_validity(index: int, case: int) -> dict:
    actor = NAMES[index % len(NAMES)]
    _base, past, noun, state = CHANGE_EVENTS[(index * 3) % len(CHANGE_EVENTS)]
    ref = f"{noun}-{case}"
    class_id = index % 4
    if class_id == 0:
        marked = f"restore-state({state}({ref})): {actor} {past} {ref}."
        careful = f"The named state {state}({ref}) is explicit, uniquely resolved, and entailed as the result of {actor}'s change-of-state event."
        answer = "licensed"
    elif class_id == 1:
        marked = f"restore-state: {actor} {past} {ref}."
        careful = "The restoration qualifier omits its mandatory explicit result-state argument."
        answer = "invalid: missing result state"
    elif class_id == 2:
        marked = f"restore-state(healthy({ref})): {actor} repaired {ref}."
        careful = f"Healthy({ref}) is not entailed as the unique result of the broad predicate repaired."
        answer = "invalid: state not entailed"
    else:
        marked = f"restore-state(ready({ref})): {actor} processed {ref}."
        careful = f"Processed does not uniquely resolve ready({ref}) as its one result state."
        answer = "invalid: ambiguous result"
    options = ["licensed", "invalid: missing result state", "invalid: state not entailed", "invalid: ambiguous result"]
    return {
        "ainglish": f"Case {case}: {marked}",
        "careful": f"Case {case}: {careful}",
        "bare": f"Case {case}: {actor} {past} {ref} again.",
        "probes": [probe("state-argument-validity", "Is this restoration-state use licensed by the declared rule?", options, answer)],
        "metadata": {"validity_class": class_id, "result_state": state},
    }


TEST_DOMAINS = [
    ("software build", "unit suite", "all declared assertions"),
    ("backup archive", "restore drill", "checksum and restore criteria"),
    ("data pipeline", "validation suite", "schema and row-count criteria"),
    ("pressure vessel", "inspection protocol", "every declared safety limit"),
    ("expense ledger", "audit procedure", "all declared audit criteria"),
    ("model release", "evaluation card", "every named acceptance threshold"),
]


def test_outcome(form: str, index: int, case: int) -> dict:
    scenario = index // 3
    subject, procedure, criteria = TEST_DOMAINS[scenario % len(TEST_DOMAINS)]
    test_ref = f"T-{case}"
    preface = f"Case {case}: {test_ref} is the named {procedure} for the {subject}; its recoverable acceptance criteria are {criteria}."
    marked = f"{preface} The {subject} {form}({test_ref})."
    bare = f"{preface} The {subject} was tested with {test_ref}."
    if form == "test-run":
        careful = f"{preface} The named procedure {test_ref} ran on the {subject}; whether its declared criteria passed remains unstated, and no broader fitness is claimed."
        passed = "not stated"
    else:
        careful = f"{preface} The named procedure {test_ref} ran on the {subject} and every acceptance criterion declared for that run was satisfied; no broader fitness is claimed."
        passed = "yes"
    return {
        "ainglish": marked,
        "careful": careful,
        "bare": bare,
        "probes": [
            probe("execution", "Does the statement establish that the named procedure executed?", YES_NO_UNKNOWN, "yes"),
            probe("declared-outcome", "Does the statement establish that every declared acceptance criterion was satisfied?", YES_NO_UNKNOWN, passed),
            probe("broader-fitness", "Does the statement establish fitness outside the named procedure?", YES_NO_UNKNOWN, "not stated"),
        ],
        "metadata": {"domain": subject, "test_ref": test_ref, "criteria_recoverable": True},
    }


ACK_DOMAINS = ["policy", "contract", "design review", "incident handoff", "safety instruction", "work schedule"]


def acknowledgement(form: str, index: int, case: int) -> dict:
    scenario = index // 4
    principal = NAMES[(scenario * 7 + 3) % len(NAMES)]
    domain = ACK_DOMAINS[scenario % len(ACK_DOMAINS)]
    ref = f"R-{case}:{domain.replace(' ', '-')}"
    preface = f"Case {case}: {ref} uniquely identifies one bounded {domain} message."
    marked = f"{preface} {principal} {form}({ref})."
    bare = f"{preface} {principal} acknowledged {ref}."
    if form == "ack-as-receipt":
        careful = f"{preface} {principal} deliberately signalled receipt and identification of {ref}; agreement and disagreement are both unstated, as are authority, compliance, truth, promise, and implementation."
        agreement, disagreement = "not stated", "not stated"
    else:
        careful = f"{preface} {principal} deliberately signalled substantive agreement with the complete content bounded by {ref}, which also establishes receipt; disagreement with that same bounded content is not signalled, while authority, legal effect, truth, promise, compliance, and implementation remain unstated."
        agreement, disagreement = "yes", "no"
    nonclaim = ["authority", "a promise to comply", "truth of the message", "implementation"][scenario % 4]
    return {
        "ainglish": marked,
        "careful": careful,
        "bare": bare,
        "probes": [
            probe("receipt", "Did the principal explicitly signal receipt and identification of the exact reference?", YES_NO_UNKNOWN, "yes"),
            probe("agreement", "Did the principal explicitly signal substantive agreement with the referenced content?", YES_NO_UNKNOWN, agreement),
            probe("disagreement-nonclaim", "Did the principal explicitly signal disagreement with the complete referenced content?", YES_NO_UNKNOWN, disagreement),
            probe("downstream-nonclaim", f"Does the statement by itself establish {nonclaim}?", YES_NO_UNKNOWN, "not stated"),
        ],
        "metadata": {"domain": domain, "principal": principal, "reference": ref, "nonclaim": nonclaim},
    }


TEXT_VARIANTS = [
    "exact", "transport-equivalent", "wrapper-only", "case-change", "punctuation-change", "space-change",
    "normalization-change", "spelling-correction", "redaction", "ellipsis", "inserted-comment", "wrong-reference",
]
MEANING_VARIANTS = [
    "exact-stable-context", "faithful-paraphrase", "active-passive", "clause-order", "speaker-change",
    "time-change", "negation-flip", "modality-weaken", "quantifier-change", "exception-drop",
    "literal-change", "lossy-summary",
]


def preservation(form: str, index: int, case: int) -> dict:
    ref = f"span-{case}@v1"
    obj = OBJECTS[index % len(OBJECTS)]
    source = f"Agent {NAMES[index % len(NAMES)]} must retain every {obj} entry through 18:00; exception code X-{case} and label Café remain literal."
    if form == "text-fixed":
        variant = TEXT_VARIANTS[index % len(TEXT_VARIANTS)]
        candidate = source
        valid = variant in {"exact", "transport-equivalent", "wrapper-only"}
        if variant == "transport-equivalent":
            # The item contains the decoded value. Metadata below records that its wire spelling
            # may use JSON escapes; recursive interpretation of a visible backslash is forbidden.
            candidate = source
        elif variant == "wrapper-only":
            candidate = f"QUOTE[{source}]"
        elif variant == "case-change":
            candidate = source.replace("Agent", "agent")
        elif variant == "punctuation-change":
            candidate = source.replace("18:00;", "18:00,")
        elif variant == "space-change":
            candidate = source.replace("every ", "every  ")
        elif variant == "normalization-change":
            candidate = source.replace("Café", "Cafe\u0301")
        elif variant == "spelling-correction":
            candidate = source.replace("retain", "preserve")
        elif variant == "redaction":
            candidate = source.replace(f"X-{case}", "[REDACTED]")
        elif variant == "ellipsis":
            candidate = source.split(";")[0] + "…"
        elif variant == "inserted-comment":
            candidate = source.replace("entry", "entry [verified]")
        elif variant == "wrong-reference":
            candidate = source.replace(f"X-{case}", f"X-{case + 1}")
        marked_rule = f"Publish candidate C-{case}, text-fixed({ref})."
        careful_rule = f"Publish C-{case} by reproducing the exact decoded Unicode scalar sequence inside immutable reference {ref}; every character, case, punctuation, space, line break, spelling, and normalization form is load-bearing, while a wrapper outside a recoverable boundary or transport encoding that decodes identically is allowed."
    else:
        variant = MEANING_VARIANTS[index % len(MEANING_VARIANTS)]
        candidate = source
        valid = variant in {"exact-stable-context", "faithful-paraphrase", "active-passive", "clause-order"}
        if variant == "faithful-paraphrase":
            candidate = source.replace("must retain every", "is required to keep all")
        elif variant == "active-passive":
            candidate = f"Every {obj} entry is required by Agent {NAMES[index % len(NAMES)]} to be retained through 18:00; exception code X-{case} remains literal."
        elif variant == "clause-order":
            candidate = f"Exception code X-{case} remains literal; through 18:00, Agent {NAMES[index % len(NAMES)]} must retain every {obj} entry."
        elif variant == "speaker-change":
            candidate = source + " [now attributed to a different authority]"
        elif variant == "time-change":
            candidate = source.replace("18:00", "19:00")
        elif variant == "negation-flip":
            candidate = source.replace("must retain", "must not retain")
        elif variant == "modality-weaken":
            candidate = source.replace("must retain", "should retain")
        elif variant == "quantifier-change":
            candidate = source.replace("every", "some")
        elif variant == "exception-drop":
            candidate = source.split(";")[0] + "."
        elif variant == "literal-change":
            candidate = source.replace(f"X-{case}", f"X-{case + 1}")
        elif variant == "lossy-summary":
            candidate = f"Agent {NAMES[index % len(NAMES)]} should keep the records for a while."
        marked_rule = f"Transform {ref} into candidate C-{case}, meaning-fixed({ref})."
        careful_rule = f"Candidate C-{case} may reword immutable reference {ref}, but it must preserve all truth conditions, force, scope, exceptions, attribution, time bounds, and every opaque literal without resolving ambiguity or adding commentary."
    prefix = f"Case {case}: Source {ref}: “{source}” Candidate C-{case}: “{candidate}”"
    return {
        "ainglish": f"{prefix} Action: {marked_rule}",
        "careful": f"{prefix} Action: {careful_rule}",
        "bare": f"{prefix} Action: Transform {ref} into candidate C-{case} as requested.",
        "probes": [probe("preservation-validity", "Does the candidate satisfy the declared preservation requirement for the uniquely resolved reference?", ["yes", "no", "invalid reference", "not enough information"], "yes" if valid else "no")],
        "metadata": {"variant": variant, "valid": valid, "reference": ref},
    }


def preservation_conjunction(index: int, case: int) -> dict:
    ref = f"joint-span-{case}@v1"
    source = f"Operator {NAMES[index % len(NAMES)]} must retain all seals until 17:00; literal J-{case}."
    category = ["both", "text only", "meaning only", "neither"][index % 4]
    if category == "both":
        candidate = source
        context = "same speaker, time, attribution, and quotation boundary"
    elif category == "text only":
        candidate = source
        context = "identical characters, but attributed to a different speaker as a live instruction"
    elif category == "meaning only":
        candidate = source.replace("must retain all", "is required to keep every")
        context = "same speaker, time, attribution, and force"
    else:
        candidate = source.replace("must retain all", "may discard some").replace(f"J-{case}", f"J-{case + 1}")
        context = "same container but changed force and literal"
    prefix = f"Case {case}: Source {ref}: “{source}” Candidate: “{candidate}” Candidate context: {context}."
    return {
        "ainglish": f"{prefix} Action: publish the candidate, text-fixed({ref}), meaning-fixed({ref}).",
        "careful": f"{prefix} Action: publish only if the candidate preserves both the exact decoded text of {ref} and its complete contextual meaning and every literal.",
        "bare": f"{prefix} Action: publish the candidate.",
        "probes": [probe("joint-invariant-set", "Which declared invariants does the candidate satisfy?", ["both", "text only", "meaning only", "neither"], category)],
        "metadata": {"category": category, "reference": ref},
    }


Renderer = Callable[[str, int, int], dict]


SPECS = {
    "they-number": {
        "slug": "they-one-they-many-say-whether-they-is-one-actor-or-several",
        "forms": ["they-one", "they-many"],
        "real_per_form": 64,
        "renderer": they_number,
        "population": "128 fresh operational items, 64 per form, with one singular and one plural antecedent candidate both semantically live; four directly scored number and nonclaim seams have 16 contexts per form",
        "decision": "each form: marked minus balanced bare >= 0.20 on number consequences, marked minus complete careful English >= -0.05, every false gender, identity, unanimity, all-member, and collectivity inference <= 0.05",
        "replication_target": "92b77fdcc4b1529f6446f1c9756b80cc08acad1c4433bf845e0a95c98b9693b0",
    },
    "enumeration-closure": {
        "slug": "among-others-and-no-others-is-the-list-the-whole-list-2",
        "forms": ["among-others", "and-no-others"],
        "real_per_form": 100,
        "renderer": enumeration,
        "population": "200 meaning-matched operational enumeration items, 100 per form, crossing eight stated kinds and scopes with paired hidden completeness intentions",
        "decision": "each form separately: marked non-inferior to complete careful English within 0.05 and materially better than balanced bare lists on unlisted-candidate consequences; listed-member health overread is separately bounded",
    },
    "role-cardinality": {
        "slug": "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
        "forms": ["one-or-more", "exactly-one"],
        "real_per_form": 64,
        "renderer": role_cardinality,
        "population": "128 form-separated role/action/count items, 64 per form, balancing zero, one, and two distinct qualifying principals plus repeated action by one principal; four directly scored seams have 16 contexts per form",
        "decision": "each form separately: marked minus careful >= -0.05; on two-principal cells marked minus bare >= 0.20; cross-pole inference <= 0.05",
    },
    "repetition-restoration": {
        "slug": "repeat-event-restore-state",
        "forms": ["repeat-event", "restore-state"],
        "real_per_form": 64,
        "renderer": repetition,
        "population": "128 force-balanced fresh items: 64 per form and 16 affirmative, negated, question, and directive items per form; each joint answer recovers earlier basis and current force",
        "decision": "every form by force cell is non-inferior to complete force-matched careful English within 0.05; restore prior-actor over-inference <= 0.10; current-event assertion errors <= 0.05",
    },
    "test-outcome": {
        "slug": "test-run-t-test-passed-t-did-tested-mean-the-check-happened-",
        "forms": ["test-run", "test-passed"],
        "real_per_form": 48,
        "renderer": test_outcome,
        "population": "96 form-balanced named-test items across software, backups, pipelines, inspections, audits, and model evaluations with recoverable criteria",
        "decision": "each form separately: marked minus careful >= -0.05, marked materially improves pass-state recovery over bare tested, and broader-fitness overread remains <= 0.05",
    },
    "acknowledgement-force": {
        "slug": "p-ack-as-receipt-r-p-ack-as-agreement-r",
        "forms": ["ack-as-receipt", "ack-as-agreement"],
        "real_per_form": 80,
        "renderer": acknowledgement,
        "population": "160 form-balanced exchanges with exact bounded references across six operational domains and independently scored receipt, agreement, disagreement, and downstream nonclaim probes",
        "decision": "each form separately: marked exact receipt/agreement recovery minus bare >= 0.20, marked minus careful >= -0.05, and each false disagreement, authority, compliance, truth, promise, or implementation inference <= 0.05",
    },
    "preservation-invariant": {
        "slug": "text-fixed-ref-meaning-fixed-ref-declare-which-invariants-a-",
        "forms": ["text-fixed", "meaning-fixed"],
        "real_per_form": 120,
        "renderer": preservation,
        "population": "240 qualifier items, 120 per form, with immutable source spans, context, candidate outputs, transport equivalence, exact-text changes, faithful paraphrases, force/scope changes, opaque literals, and wrong references; plus a 40-item conjunction diagnostic",
        "decision": "each qualifier separately: marked minus full careful mapping >= -0.05 with exact invariant and violation recovery; conjunction reports both, text-only, meaning-only, and neither without pooling",
    },
}


def campaign_items(spec_key: str, form: str, role: str, offset: int) -> list[dict]:
    spec = SPECS[spec_key]
    renderer: Renderer = spec["renderer"]
    real_target = int(spec["real_per_form"])
    rendered_rows = []
    context_index = 0
    while len(rendered_rows) < real_target:
        case = 700_000 + offset + context_index
        rendered = renderer(form, context_index, case)
        probe_index = context_index % len(rendered["probes"])
        detail = rendered["probes"][probe_index]
        item_index = len(rendered_rows)
        comparator = rendered["careful"] if role == "claim_carrier" else rendered["bare"]
        # Balance answer position inside each semantic seam, not merely in the pooled campaign.
        position = context_index // len(rendered["probes"]) + probe_index
        rendered_rows.append({
            "id": f"{safe(spec_key)}-{safe(form)}-{safe(role)}-{item_index + 1:03d}",
            "english": comparator,
            "ainglish": rendered["ainglish"],
            "question": detail["question"],
            "options": placed(detail["options"], detail["answer"], position),
            "answer": detail["answer"],
            "form": form,
            "semantic_seam": detail["seam"],
            "settlement_stratum": f"{form}.{detail['seam']}",
            "context_id": f"{safe(spec_key)}-{role}-{case}",
            "comparator_kind": "complete-careful-english-v1" if role == "claim_carrier" else "balanced-bare-english-v1",
            "metadata": rendered["metadata"],
        })
        context_index += 1
    prefix = f"{safe(spec_key)}-{safe(form)}-{safe(role)}"
    return calibration_rows(prefix, 5_000_000 + offset) + rendered_rows


def diagnostic_items(spec_key: str, name: str, real_target: int, offset: int) -> list[dict]:
    rows = []
    for index in range(real_target):
        case = 900_000 + offset + index
        if name == "restore-validity":
            rendered = restore_validity(index, case)
            form = "restore-state"
            comparator_kind = "complete-validity-rule-v1"
        elif name == "preservation-conjunction":
            rendered = preservation_conjunction(index, case)
            form = "text-fixed"
            comparator_kind = "complete-conjunction-rule-v1"
        else:  # pragma: no cover - builder-owned closed set
            raise AssertionError(name)
        detail = rendered["probes"][0]
        rows.append({
            "id": f"{safe(spec_key)}-{safe(name)}-{index + 1:03d}",
            "english": rendered["careful"],
            "ainglish": rendered["ainglish"],
            "question": detail["question"],
            "options": placed(detail["options"], detail["answer"], index),
            "answer": detail["answer"],
            "form": form,
            "semantic_seam": detail["seam"],
            "settlement_stratum": f"{form}.{detail['seam']}",
            "context_id": f"{safe(spec_key)}-{safe(name)}-{case}",
            "comparator_kind": comparator_kind,
            "metadata": rendered["metadata"],
        })
    return calibration_rows(f"{safe(spec_key)}-{safe(name)}", 6_000_000 + offset) + rows


def seal_design(spec_key: str, campaigns: dict[str, dict]) -> dict:
    spec = SPECS[spec_key]
    value = {
        "kind": "ainglish.reader-evidence-design.v1",
        "slug": spec["slug"],
        "proposal_revision": spec["slug"],
        "population": spec["population"],
        "forms": spec["forms"],
        "estimand": "per-form comprehension_accuracy_delta with complete careful-English non-inferiority as the claim carrier; balanced bare English is separately frozen and reported only as a diagnostic",
        "decision_rule": spec["decision"],
        "training_data_interpretation": {
            "present_zero_shot": "Current readers were exposed to English in training and are not assumed to have seen Ainglish; zero-shot results measure present surface transparency under that asymmetry.",
            "future_efficiency": "Ainglish-aware future training and tokenizers may change both comprehension and cost. That prospective benefit is a hypothesis, not a reinterpretation of present adverse evidence.",
            "token_boundary": "Current token price is reported separately and cannot establish comprehension. A preregistered adverse token prerequisite remains adverse even when the future-training rationale remains plausible.",
        },
        "quality_gates": {
            "mint_before_reader_spend": True,
            "calibration_both_arms": True,
            "retain_all_admissible_outcomes": True,
            "no_scientific_cell_retry": True,
            "complete_pair_identity": True,
            "qualified_reader_lineages_min": 2,
            "reader_gate_status_at_freeze": "closed: Qwen v10-general was adverse on reference resolution; no two-lineage common-holdout roster exists",
            "zero_transport_truncations": True,
            "report_forms_and_strata_separately": True,
        },
        "campaigns": campaigns,
        "activation": "bind exact qualified reader editions, freeze a runspec, publish it, then mint the Ainglish attempt before any scientific or calibration reader call",
        "model_calls": 0,
        "governance_writes": 0,
    }
    if spec.get("replication_target"):
        value["replication"] = {
            "replicates_hash": spec["replication_target"],
            "boundary": "the balanced-bare campaign preserves the filed original's primary comparator on wholly fresh inputs; careful-English non-inferiority remains a separately frozen claim-carrier campaign and must not be inferred from replication settlement",
        }
    value["content_sha256"] = digest(value)
    return value


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    index_outputs = {}
    file_counter = 0
    for spec_index, (spec_key, spec) in enumerate(SPECS.items()):
        campaigns = {}
        output_files = []
        for form_index, form in enumerate(spec["forms"]):
            for role_index, role in enumerate(("claim_carrier", "bare_diagnostic")):
                offset = spec_index * 100_000 + form_index * 20_000 + role_index * 8_000
                rows = campaign_items(spec_key, form, role, offset)
                filename = f"{safe(spec_key)}--{safe(form)}--{'claim' if role == 'claim_carrier' else 'bare'}.items.json"
                path = ROOT / filename
                write_frozen(path, rows)
                campaign_name = f"{safe(form)}-{'vs-careful' if role == 'claim_carrier' else 'vs-bare'}"
                campaigns[campaign_name] = {
                    "role": role,
                    "form": form,
                    "metric": "comprehension_accuracy_delta",
                    "comparator": {
                        "kind": "complete-careful-english-v1" if role == "claim_carrier" else "balanced-bare-english-v1",
                        "description": "Full registered meaning, including material nonclaims." if role == "claim_carrier" else "Ambiguous ordinary-English surface balanced across both intended readings; diagnostic only.",
                    },
                    "items": filename,
                    "items_sha256": file_digest(path),
                    "planned_sample": {"real_items": len(rows) - 12, "calibration_items": 12},
                    "settlement": "form and semantic seams remain separately visible; no pooled rescue",
                }
                output_files.append({"file": filename, "sha256": file_digest(path), "real_items": len(rows) - 12})
                file_counter += 1
        if spec_key == "repetition-restoration":
            filename = "repetition-restoration--restore-validity.items.json"
            rows = diagnostic_items(spec_key, "restore-validity", 32, 678_000)
            path = ROOT / filename
            write_frozen(path, rows)
            campaigns["restore-state-validity"] = {
                "role": "learnability_diagnostic",
                "form": "restore-state",
                "metric": "comprehension_accuracy_delta",
                "comparator": {"kind": "complete-validity-rule-v1"},
                "items": filename,
                "items_sha256": file_digest(path),
                "planned_sample": {"real_items": 32, "calibration_items": 12},
            }
            output_files.append({"file": filename, "sha256": file_digest(path), "real_items": 32})
            file_counter += 1
        if spec_key == "preservation-invariant":
            filename = "preservation-invariant--conjunction.items.json"
            rows = diagnostic_items(spec_key, "preservation-conjunction", 40, 789_000)
            path = ROOT / filename
            write_frozen(path, rows)
            campaigns["text-and-meaning-conjunction"] = {
                "role": "learnability_diagnostic",
                "form": "text-fixed",
                "metric": "comprehension_accuracy_delta",
                "comparator": {"kind": "complete-conjunction-rule-v1"},
                "items": filename,
                "items_sha256": file_digest(path),
                "planned_sample": {"real_items": 40, "calibration_items": 12},
            }
            output_files.append({"file": filename, "sha256": file_digest(path), "real_items": 40})
            file_counter += 1
        design = seal_design(spec_key, campaigns)
        design_path = ROOT / f"{safe(spec_key)}.design.json"
        write_frozen(design_path, design)
        EvidenceDesign.load(design_path)
        index_outputs[spec_key] = {
            "slug": spec["slug"],
            "forms": spec["forms"],
            "design": design_path.name,
            "design_sha256": design["content_sha256"],
            "files": output_files,
            "reader_gate": "closed",
        }
    flagship_gaps = {
        "we-including-you / we-excluding-you": {
            "slug": "we-including-you-we-excluding-you-clusivity-mark-whether-we--4",
            "carrier": "../clusivity-recertification-carrier-v1-2026-08-29/zero-shot.json",
            "secondary": "../clusivity-recertification-carrier-v1-2026-08-29/definition-conditioned.json",
            "status": "full bare, careful, and marked carrier frozen; reader gate closed",
        },
        "you-one / you-all": {
            "slug": "you-one-you-all-say-whether-you-addresses-one-recipient-or-t",
            "carrier": "../flagship-modern-carriers-v2-2026-08-27/addressee.template.json",
            "status": "complete-careful carrier frozen; reader gate closed",
        },
        "fact-not-known / choice-not-made": {
            "slug": "fact-not-known-choice-not-made-distinguish-missing-evidence-",
            "carrier": "../flagship-modern-carriers-v2-2026-08-27/uncertainty.template.json",
            "status": "complete-careful carrier frozen; reader gate closed",
        },
        "no-delegation / one-hop-delegation-allowed": {
            "slug": "no-delegation-one-hop-delegation-allowed-state-whether-a-tas",
            "carrier": "../flagship-modern-carriers-v2-2026-08-27/delegation.template.json",
            "status": "complete-careful carrier frozen; reader gate closed",
        },
        "text-fixed / meaning-fixed": {
            "slug": "text-fixed-ref-meaning-fixed-ref-declare-which-invariants-a-",
            "carrier": "preservation-invariant.design.json",
            "status": "new 120-per-form full-comparator carrier plus conjunction diagnostic frozen; reader gate closed",
        },
    }
    index = {
        "kind": "dexagon.ainglish.flagship-comprehension-wave-v3.index",
        "purpose": "six-item language progression wave plus closure of the missing text-fixed/meaning-fixed flagship carrier",
        "outputs": index_outputs,
        "ratified_flagship_gaps": flagship_gaps,
        "summary": {
            "designs": len(index_outputs),
            "item_files": file_counter,
            "real_items": sum(file["real_items"] for row in index_outputs.values() for file in row["files"]),
            "model_calls": 0,
            "governance_writes": 0,
        },
        "reader_gate": {
            "required": "at least two distinct base-model lineages passing one fresh common construct-free holdout",
            "current": "closed",
            "reason": "Qwen v10-general scored 60/64 overall but 5/8 reference resolution; the common-holdout gate is conjunctive and remains adverse",
            "remote_lane": "../remote-reader-qualification-v1-2026-08-29/README.md",
        },
        "content_sha256": "",
    }
    index["content_sha256"] = digest({key: value for key, value in index.items() if key != "content_sha256"})
    write_frozen(ROOT / "index.json", index)
    print(json.dumps(index["summary"] | {"content_sha256": index["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
