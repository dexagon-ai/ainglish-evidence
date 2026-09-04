#!/usr/bin/env python3
"""Build three fresh, answer-bearing comprehension replication handoffs."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def rotate(answer: str, alternatives: list[str], index: int) -> list[str]:
    choices = [answer, *alternatives]
    assert len(choices) == 4 and len(set(choices)) == 4
    offset = index % 4
    return choices[offset:] + choices[:offset]


def calibration(prefix: str) -> list[dict]:
    fixtures = [
        ("bronze ticket", "shelf 17"), ("cedar card", "locker 22"),
        ("denim seal", "drawer 19"), ("ebony badge", "vault 23"),
        ("fawn token", "shelf 24"), ("ginger key", "locker 18"),
        ("heather disk", "drawer 21"), ("ivory note", "vault 20"),
        ("juniper pass", "shelf 26"), ("khaki tag", "locker 29"),
        ("lilac stamp", "drawer 25"), ("marble chip", "vault 28"),
        ("navy slip", "shelf 31"), ("opal label", "locker 27"),
        ("plum marker", "drawer 30"), ("quartz token", "vault 32"),
    ]
    rows = []
    for index, (thing, place) in enumerate(fixtures):
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The record mentions the {thing}, but gives no storage location.",
            "ainglish": f"The record states that the {thing} is stored in {place}.",
            "question": f"Where does the record state that the {thing} is stored?",
            "options": rotate(place, ["the intake desk", "the archive hall", "no location is stated"], index),
            "answer": place,
            "probe": "construct-free explicit-location planted effect",
        })
    return rows


def dispatch_receipt() -> list[dict]:
    payloads = ["invoice Q", "patch R", "alert S", "bundle T", "report U", "manifest V", "notice W", "snapshot X"]
    transports = ["relay-amber", "queue-12", "bus-cedar", "outbox-9", "relay-slate", "queue-27", "bus-elm", "outbox-14"]
    witnesses = ["ack-88", "recipient-log", "agent-Mira", "signed-receipt", "ack-91", "mailbox-proof", "agent-Niko", "delivery-log"]
    complications = [
        "a later bounce remains possible", "no recipient acknowledgement exists yet",
        "the first route timed out and this is the retry", "the recipient is currently offline",
        "the queue reports success but the mailbox has not been checked", "the payload remains eligible for redelivery",
        "the sender's own dashboard says sent", "the transport has not supplied a receipt",
    ]
    rows = []
    for index in range(16):
        payload = payloads[index % len(payloads)]
        transport = transports[index % len(transports)]
        witness = witnesses[index % len(witnesses)]
        complication = complications[index % len(complications)]
        case = index + 101
        answer = "the transport accepted the payload for sending, but recipient receipt is not established"
        rows.append({
            "id": f"dispatch-rep-dispatched-{index + 1:02d}",
            "english": f"For case {case}, transport {transport} accepted {payload} for sending; {complication}, so this does not establish recipient receipt.",
            "ainglish": f"dispatched({transport}): {payload} for case {case}.",
            "question": "What may the case monitor conclude from this message alone?",
            "options": rotate(answer, ["the recipient definitely received the payload", "the transport rejected the payload", "neither transport acceptance nor receipt is established"], index),
            "answer": answer,
            "form": "dispatched",
            "settlement_stratum": "dispatched",
        })
        answer = "the named witness confirms that the recipient received the payload"
        rows.append({
            "id": f"dispatch-rep-delivered-{index + 1:02d}",
            "english": f"For case {case}, witness {witness} confirms that the recipient received {payload}, after any transport retries.",
            "ainglish": f"delivered({witness}): {payload} for case {case}.",
            "question": "What may the case monitor conclude from this message alone?",
            "options": rotate(answer, ["only transport acceptance is established", "the payload is still waiting in a queue", "no receipt witness is identified"], index + 1),
            "answer": answer,
            "form": "delivered",
            "settlement_stratum": "delivered",
        })
    return rows + calibration("dispatch-rep")


def quantity_multiplier() -> list[dict]:
    nouns = ["jobs", "samples", "packets", "workers", "records", "shards", "checks", "requests"]
    rows = []
    for index in range(16):
        case = index + 201
        noun = nouns[index % len(nouns)]
        factor = (2, 3, 4, 5)[index % 4]
        baseline = (7, 9, 11, 13, 6, 8, 12, 14)[index % 8]
        result = factor * baseline
        answer = f"{result} {noun}"
        rows.append({
            "id": f"quantity-rep-increase-{index + 1:02d}",
            "english": f"In case {case}, lane E contains exactly {factor} times as many {noun} as lane D. Lane D contains {baseline} {noun}.",
            "ainglish": f"In case {case}, lane E contains {factor} times as many {noun} as lane D. Lane D contains {baseline} {noun}.",
            "question": f"How many {noun} does lane E contain in case {case}?",
            "options": rotate(answer, [f"{baseline + factor} {noun}", f"{result + baseline} {noun}", "the quantity is not determined"], index),
            "answer": answer,
            "form": "increase-conformant",
            "settlement_stratum": "increase",
        })
        divisor = (2, 3, 4, 5)[index % 4]
        quotient = (5, 7, 8, 9, 11, 12, 13, 15)[index % 8]
        larger = divisor * quotient
        answer = f"{quotient} {noun}"
        rows.append({
            "id": f"quantity-rep-decrease-{index + 1:02d}",
            "english": f"In case {case}, lane F contains exactly one-{divisor}th as many {noun} as lane G. Lane G contains {larger} {noun}.",
            "ainglish": f"In case {case}, lane F contains one-{divisor}th as many {noun} as lane G. Lane G contains {larger} {noun}.",
            "question": f"How many {noun} does lane F contain in case {case}?",
            "options": rotate(answer, [f"{larger * divisor} {noun}", f"{larger - divisor} {noun}", "the quantity is not determined"], index + 1),
            "answer": answer,
            "form": "decrease-conformant",
            "settlement_stratum": "decrease",
        })
    return rows + calibration("quantity-rep")


def replacement_roles() -> list[dict]:
    domains = ["worker", "mirror", "credential", "policy", "parser", "pump", "dataset", "reviewer"]
    slots = ["night shift", "primary route", "active signer", "default rule", "build lane", "cooling loop", "training slot", "approval seat"]
    rows = []
    for index in range(16):
        domain = domains[index % len(domains)]
        slot = slots[index % len(slots)]
        old = f"{domain}-departing-{index + 41}"
        new = f"{domain}-incoming-{index + 73}"
        prefix = f"In the {slot}, remove {old} from the operative role and put {new} into that same role instead."
        marked = f"For the {slot}, replace(old={old}, new={new})."
        answer = new
        rows.append({
            "id": f"replacement-rep-incoming-{index + 1:02d}",
            "english": prefix,
            "ainglish": marked,
            "question": "Which reference occupies the named role after this replacement is completed?",
            "options": rotate(answer, [old, "both references", "the incoming reference is not specified"], index),
            "answer": answer,
            "form": "replace-old-new",
            "settlement_stratum": "incoming-reference",
        })
        answer = old
        rows.append({
            "id": f"replacement-rep-departing-{index + 1:02d}",
            "english": prefix,
            "ainglish": marked,
            "question": "Which reference leaves the named operative role?",
            "options": rotate(answer, [new, "both references", "the departing reference is not specified"], index + 1),
            "answer": answer,
            "form": "replace-old-new",
            "settlement_stratum": "departing-reference",
        })
    return rows + calibration("replacement-rep")


def write(name: str, slug: str, public_id: str, construct: str, target: str, strata: list[str], items: list[dict]) -> dict:
    science = [row for row in items if not row.get("calibration")]
    controls = [row for row in items if row.get("calibration")]
    payload = {
        "kind": "dexagon.ainglish.comprehension-replication-handoff.v1",
        "proposal_revision": slug,
        "proposal_public_id": public_id,
        "construct": construct,
        "replicates_hash": target,
        "metric": "comprehension_accuracy_delta",
        "comparison": "registered compact form minus complete careful-English mapping",
        "training_asymmetry": "Current readers have ordinary-English training and are not assumed to have seen Ainglish; this is a present zero-shot transparency test.",
        "items": items,
    }
    path = ROOT / f"{name}.items.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "file": path.name,
        "slug": slug,
        "public_id": public_id,
        "construct": construct,
        "replicates_hash": target,
        "items_sha256": sha256(canonical(items)).hexdigest(),
        "scientific_items": len(science),
        "calibration_items": len(controls),
        "settlement_strata": [{"id": value, "weight": 1} for value in strata],
        "stratum_counts": dict(sorted(Counter(row["settlement_stratum"] for row in science).items())),
    }


def main() -> None:
    campaigns = {
        "dispatch-receipt": write(
            "dispatch-receipt", "dispatched-transport-delivered-witness-say-which-transit-eve", "a-94wc58sz8ks3ce4y",
            "dispatched / delivered", "39a511cf82362e44c1ebb56eb945f615c245d50e1f65a0aa62dc0c91c45e5ff3",
            ["dispatched", "delivered"], dispatch_receipt(),
        ),
        "quantity-multiplier": write(
            "quantity-multiplier", "multiply-the-quantity-a-multiplier-attaches-to-the-2", "a-cjgt374hndvt1jqa",
            "multiply-the-quantity", "acf09cd6e0565044712929be4ecc9fed599f0064a2e7aedb236d243125757777",
            ["increase", "decrease"], quantity_multiplier(),
        ),
        "replacement-roles": write(
            "replacement-roles", "replace-old-departing-ref-new-incoming-ref", "a-f34mb0zf8xp2pkwm",
            "replace(old, new)", "c43ed0b19e3b852a167854dd644672a33c1d8abb03e2649cbd1bb4fd25531a6d",
            ["incoming-reference", "departing-reference"], replacement_roles(),
        ),
    }
    index = {
        "kind": "dexagon.ainglish.comprehension-replication-handoff-index.v1",
        "created_at": "2026-09-04",
        "model_calls": 0,
        "independence": "A different authenticated principal must freshly receive and execute the target; this repository publication alone is not a replication.",
        "campaigns": campaigns,
    }
    index["content_sha256"] = sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
