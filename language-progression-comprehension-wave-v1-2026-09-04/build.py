#!/usr/bin/env python3
"""Build six complete-careful-English progression carriers without reader calls."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def rotate(answer: str, distractors: list[str], index: int) -> list[str]:
    values = [answer, *distractors]
    assert len(values) == 4 and len(set(values)) == 4
    offset = index % 4
    return values[offset:] + values[:offset]


def calibration(prefix: str) -> list[dict]:
    things = [
        ("amber pass", "locker 3"), ("birch token", "drawer 8"),
        ("cobalt key", "cabinet 2"), ("dune card", "vault 11"),
        ("elm badge", "locker 14"), ("flint seal", "drawer 5"),
        ("granite disk", "cabinet 9"), ("hazel note", "vault 4"),
        ("indigo pass", "locker 12"), ("jade token", "drawer 1"),
        ("kelp key", "cabinet 15"), ("linen card", "vault 7"),
        ("maple badge", "locker 6"), ("nickel seal", "drawer 13"),
        ("ochre disk", "cabinet 10"), ("pearl note", "vault 16"),
    ]
    rows = []
    for index, (thing, location) in enumerate(things):
        answer = location
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"An inventory message names the {thing}, but does not state its location.",
            "ainglish": f"An inventory message states that the {thing} is in {location}.",
            "question": f"Where does the message state that the {thing} is?",
            "options": rotate(answer, ["the dispatch desk", "the archive room", "no location is stated"], index),
            "answer": answer,
            "probe": "construct-free explicit-location planted effect",
        })
    return rows


def delivery_items() -> list[dict]:
    transports = ["queue-red", "relay-blue", "mailbox-7", "bus-copper"]
    witnesses = ["receipt-41", "agent-Lio", "destination-log", "signed-ack"]
    payloads = ["report A", "patch B", "notice C", "bundle D"]
    rows = []
    for index in range(16):
        payload, transport, witness = payloads[index % 4], transports[index % 4], witnesses[index % 4]
        suffix = f" for transfer {index + 1}"
        answer = "the transport accepted the payload for sending; receipt is not established"
        rows.append({
            "id": f"delivery-dispatched-{index + 1:02d}",
            "english": f"{payload} was accepted by transport {transport} for sending{suffix}; this does not establish that the destination received it.",
            "ainglish": f"dispatched({transport}): {payload}{suffix}.",
            "question": "What does the message establish?",
            "options": rotate(answer, ["the destination received the payload", "the payload was rejected before sending", "both dispatch and receipt are unknown"], index),
            "answer": answer,
            "form": "dispatched",
            "settlement_stratum": "dispatched",
        })
        answer = "the named witness confirms that the destination received the payload"
        rows.append({
            "id": f"delivery-delivered-{index + 1:02d}",
            "english": f"Witness {witness} confirms that the destination received {payload}{suffix}.",
            "ainglish": f"delivered({witness}): {payload}{suffix}.",
            "question": "What does the message establish?",
            "options": rotate(answer, ["a transport accepted the payload but receipt is unknown", "the payload remains queued", "no witness to receipt is named"], index + 1),
            "answer": answer,
            "form": "delivered",
            "settlement_stratum": "delivered",
        })
    return rows + calibration("delivery")


def multiplier_items() -> list[dict]:
    nouns = ["workers", "requests", "shards", "records"]
    rows = []
    for index in range(16):
        factor = 2 + index % 4
        baseline = 3 + index % 5
        noun = nouns[index % 4]
        result = factor * baseline
        answer = f"{result} {noun}"
        rows.append({
            "id": f"multiplier-increase-{index + 1:02d}",
            "english": f"Batch B contains exactly {factor} times as many {noun} as batch A. Batch A contains {baseline} {noun}.",
            "ainglish": f"quantity(B.{noun}) = {factor}× quantity(A.{noun}); quantity(A.{noun}) = {baseline}.",
            "question": f"How many {noun} are in batch B?",
            "options": rotate(answer, [f"{factor + baseline} {noun}", f"{result + factor} {noun}", "the quantity is not specified"], index),
            "answer": answer,
            "form": "N-times-the-quantity",
            "settlement_stratum": "increase",
        })
        divisor = 2 + index % 3
        larger = divisor * (4 + index % 5)
        result = larger // divisor
        answer = f"{result} {noun}"
        rows.append({
            "id": f"multiplier-decrease-{index + 1:02d}",
            "english": f"Batch C contains exactly one-{divisor}th as many {noun} as batch D. Batch D contains {larger} {noun}.",
            "ainglish": f"quantity(C.{noun}) = quantity(D.{noun})/{divisor}; quantity(D.{noun}) = {larger}.",
            "question": f"How many {noun} are in batch C?",
            "options": rotate(answer, [f"{larger * divisor} {noun}", f"{larger - divisor} {noun}", "the quantity is not specified"], index + 1),
            "answer": answer,
            "form": "one-Nth-the-quantity",
            "settlement_stratum": "decrease",
        })
    return rows + calibration("multiplier")


def selection_items() -> list[dict]:
    sets = ["reviewers", "mirrors", "candidate routes", "available workers"]
    refs = ["review-pool", "mirror-set", "route-set", "worker-pool"]
    rows = []
    for index in range(16):
        members, ref = sets[index % 4], refs[index % 4]
        answer = "any selection method is allowed; equal probability is not required"
        rows.append({
            "id": f"selection-any-{index + 1:02d}",
            "english": f"Choose one member of the {members} in {ref} by any permitted selection method; the instruction does not require random or equal-probability selection.",
            "ainglish": f"choose-any({ref}).",
            "question": "Which selection rule is required?",
            "options": rotate(answer, ["every member must have equal probability", "the first member must be chosen", "every member must be selected"], index),
            "answer": answer,
            "form": "choose-any",
            "settlement_stratum": "choose-any",
        })
        answer = "every member must have equal probability of being selected"
        rows.append({
            "id": f"selection-uniform-{index + 1:02d}",
            "english": f"Randomly draw one member from the {members} in {ref}, giving every member equal probability of selection.",
            "ainglish": f"draw-uniform({ref}).",
            "question": "Which selection rule is required?",
            "options": rotate(answer, ["any non-random method is allowed", "the first member must be chosen", "all members must be selected"], index + 1),
            "answer": answer,
            "form": "draw-uniform",
            "settlement_stratum": "draw-uniform",
        })
    return rows + calibration("selection")


def intention_items() -> list[dict]:
    acts = ["deleted cache A", "paused worker B", "sent notice C", "restarted service D"]
    agents = ["Ari", "Bela", "Cato", "Dina"]
    rows = []
    for index in range(16):
        act, agent = acts[index % 4], agents[index % 4]
        answer = "the act was deliberate and intended"
        rows.append({
            "id": f"intention-purpose-{index + 1:02d}",
            "english": f"{agent} deliberately and intentionally {act} during case {index + 1}.",
            "ainglish": f"{agent} {act} on-purpose during case {index + 1}.",
            "question": "What does the message say about the actor's intention?",
            "options": rotate(answer, ["the act was unintentional", "the actor's intention is unknown", "another person caused the act"], index),
            "answer": answer,
            "form": "on-purpose",
            "settlement_stratum": "on-purpose",
        })
        answer = "the act was unintentional"
        rows.append({
            "id": f"intention-accident-{index + 1:02d}",
            "english": f"{agent} unintentionally {act} during case {index + 1}; it was an accident.",
            "ainglish": f"{agent} {act} by-accident during case {index + 1}.",
            "question": "What does the message say about the actor's intention?",
            "options": rotate(answer, ["the act was deliberate and intended", "the actor's intention is unknown", "another person caused the act"], index + 1),
            "answer": answer,
            "form": "by-accident",
            "settlement_stratum": "by-accident",
        })
    return rows + calibration("intention")


def replacement_items() -> list[dict]:
    nouns = ["worker", "mirror", "key", "policy"]
    rows = []
    for index in range(16):
        noun = nouns[index % 4]
        old, new = f"{noun}-old-{index + 1}", f"{noun}-new-{index + 1}"
        answer = new
        rows.append({
            "id": f"replacement-incoming-{index + 1:02d}",
            "english": f"Remove departing {old} from the active slot and put incoming {new} in its place.",
            "ainglish": f"replace(old={old}, new={new}).",
            "question": "Which reference occupies the active slot after the replacement?",
            "options": rotate(answer, [old, "both references", "the active reference is not specified"], index),
            "answer": answer,
            "form": "replace-old-new",
            "settlement_stratum": "incoming-reference",
        })
        answer = old
        rows.append({
            "id": f"replacement-departing-{index + 1:02d}",
            "english": f"Remove departing {old} from the active slot and put incoming {new} in its place.",
            "ainglish": f"replace(old={old}, new={new}).",
            "question": "Which reference is the departing value removed from the active slot?",
            "options": rotate(answer, [new, "both references", "the departing reference is not specified"], index + 1),
            "answer": answer,
            "form": "replace-old-new",
            "settlement_stratum": "departing-reference",
        })
    return rows + calibration("replacement")


def availability_items() -> list[dict]:
    offers = ["support hour", "audit slot", "export job", "review pass"]
    resources = ["GPU lane", "worker slot", "archive mirror", "test tenant"]
    scopes = ["project-alpha", "team-copper", "account-7", "batch-delta"]
    rows = []
    for index in range(16):
        scope = scopes[index % 4]
        answer = "there is no charge within the named billing scope; current allocation is not established"
        rows.append({
            "id": f"availability-charge-{index + 1:02d}",
            "english": f"The {offers[index % 4]} carries no price or fee within billing scope {scope}; this does not state that capacity is allocated now.",
            "ainglish": f"{offers[index % 4]} is no-charge({scope}).",
            "question": "What does the message establish?",
            "options": rotate(answer, ["capacity is allocated now", "the offer has a charge", "both price and allocation are unknown"], index),
            "answer": answer,
            "form": "no-charge",
            "settlement_stratum": "no-charge",
        })
        answer = "the resource is allocated or obtainable now within the named scope; price is not established"
        rows.append({
            "id": f"availability-now-{index + 1:02d}",
            "english": f"The {resources[index % 4]} is allocated or obtainable now within allocation scope {scope}; this does not state whether it has a price.",
            "ainglish": f"{resources[index % 4]} is available-now({scope}).",
            "question": "What does the message establish?",
            "options": rotate(answer, ["there is no charge", "the resource is unavailable", "both price and allocation are unknown"], index + 1),
            "answer": answer,
            "form": "available-now",
            "settlement_stratum": "available-now",
        })
    return rows + calibration("availability")


def write(name: str, public_id: str, slug: str, construct: str, items: list[dict], strata: list[str]) -> dict:
    payload = {
        "kind": "dexagon.ainglish.language-progression-comprehension-carrier.v1",
        "proposal_revision": slug,
        "proposal_public_id": public_id,
        "construct": construct,
        "comparison": "complete-careful-English mapping versus the registered compact form",
        "reader_calls": 0,
        "items": items,
    }
    path = ROOT / f"{name}.items.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    science = [row for row in items if not row.get("calibration")]
    controls = [row for row in items if row.get("calibration")]
    return {
        "name": name,
        "public_id": public_id,
        "slug": slug,
        "construct": construct,
        "file": path.name,
        "items_sha256": sha256(canonical(items)).hexdigest(),
        "scientific_items": len(science),
        "calibration_items": len(controls),
        "settlement_strata": [{"id": value, "weight": 1} for value in strata],
        "stratum_counts": dict(sorted(Counter(row["settlement_stratum"] for row in science).items())),
        "execution": "Dexagon may file an eligible original only after a fresh authenticated live-state and proposer check",
    }


def main() -> None:
    campaigns = [
        write("dispatch-receipt", "a-94wc58sz8ks3ce4y", "dispatched-transport-delivered-witness-say-which-transit-eve", "dispatched / delivered", delivery_items(), ["dispatched", "delivered"]),
        write("quantity-multiplier", "a-cjgt374hndvt1jqa", "multiply-the-quantity-a-multiplier-attaches-to-the-2", "multiply-the-quantity", multiplier_items(), ["increase", "decrease"]),
        write("selection-method", "a-ppyzdf5qk6z67aty", "choose-any-set-ref-draw-uniform-set-ref", "choose-any / draw-uniform", selection_items(), ["choose-any", "draw-uniform"]),
        write("actor-intention", "a-kwn7gx5nstn1cnyn", "on-purpose-by-accident", "on-purpose / by-accident", intention_items(), ["on-purpose", "by-accident"]),
        write("replacement-roles", "a-f34mb0zf8xp2pkwm", "replace-old-departing-ref-new-incoming-ref", "replace(old, new)", replacement_items(), ["incoming-reference", "departing-reference"]),
        write("price-allocation", "a-yc4193gwc2e87zkn", "offer-is-no-charge-billing-scope-resource-is-available-now", "no-charge / available-now", availability_items(), ["no-charge", "available-now"]),
    ]
    index = {
        "kind": "dexagon.ainglish.language-progression-comprehension-wave.v1",
        "model_calls": 0,
        "comparability": "Every scientific English arm states the complete careful meaning; bare ambiguity is not used to inflate the scalar.",
        "training_asymmetry": "Present readers have ordinary-English training and are not assumed to have seen Ainglish. Results measure current zero-shot transparency, not future post-training efficiency.",
        "campaigns": {row["name"]: row for row in campaigns},
    }
    index["content_sha256"] = sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"campaigns": len(campaigns), "content_sha256": index["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
