#!/usr/bin/env python3
"""Build Dexagon's fresh claim-tag comprehension set without model calls.

The set is generated from fixed, hand-auditable records. It deliberately does not read Reticuli's
item artifact: only the registered claim-tag semantics and public aggregate design were consulted.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


OUT = Path(__file__).with_name("claim_tag_items_72660a14.json")
CONFIDENCE_OPTIONS = ["about 10%", "about 40%", "about 70%", "about 90%"]

CONFIDENCE = [
    ("mirror-digest", "The mirror digest matches the primary artifact", "0.9", "about 90%",
     "a byte-for-byte comparison produces a different digest"),
    ("queue-cutoff", "The queue will drain before the maintenance cutoff", "0.7", "about 70%",
     "a queued job remains when the cutoff arrives"),
    ("race-patch", "The patch removes the dispatch race", "0.4", "about 40%",
     "the race reproduces under the pinned stress schedule"),
    ("backup-complete", "The backup contains every committed ledger entry", "0.9", "about 90%",
     "a committed entry is absent from a restored copy"),
    ("report-coverage", "The report covers every eligible deployment", "0.1", "about 10%",
     "an eligible deployment is missing from the report"),
    ("service-recovery", "The service will recover without operator intervention", "0.7", "about 70%",
     "an operator action is required before health checks pass"),
    ("key-propagation", "The rotated key has reached every verifier", "0.4", "about 40%",
     "a live verifier still accepts only the retired key"),
    ("parser-roundtrip", "The parser preserves the message losslessly", "0.9", "about 90%",
     "serialising the parsed message changes a semantic field"),
    ("cache-stale", "The cache entry is stale", "0.1", "about 10%",
     "the entry version equals the authoritative version"),
    ("migration-reversible", "The migration can be reversed without data loss", "0.4", "about 40%",
     "a rollback loses a row present before migration"),
    ("webhook-duplicate", "The webhook retry produced a duplicate delivery", "0.7", "about 70%",
     "the receiver log contains only one delivery identifier"),
    ("release-signature", "The release signature was produced by the release bot", "0.9", "about 90%",
     "the signature verifies under a key never held by the release bot"),
    ("dataset-leakage", "The evaluation dataset is free of training leakage", "0.1", "about 10%",
     "a verbatim evaluation item appears in the training snapshot"),
    ("memory-fix", "The allocator change fixes the memory regression", "0.7", "about 70%",
     "the pinned workload still exceeds the old peak allocation"),
    ("timezone-normalised", "Every timestamp was normalised to UTC", "0.4", "about 40%",
     "a stored timestamp retains a non-UTC offset"),
    ("quorum-holds", "The quorum remains valid after the membership change", "0.9", "about 90%",
     "the surviving signers fall below the declared threshold"),
]

FALSIFIERS = [
    ("index-complete", "The index contains every accepted record", "0.8",
     "an accepted record identifier is absent from a full index scan",
     ["an indexed record is returned twice by pagination", "the scan completes faster than yesterday", "No rejecting outcome was stated"]),
    ("exactly-once", "Each task changes external state exactly once", "0.7",
     "one task identifier produces two externally visible state changes",
     ["two different task identifiers change the same table", "a task is retried before succeeding", "No rejecting outcome was stated"]),
    ("latency-budget", "The endpoint stays within its latency budget", "0.6",
     "the pinned load test reports p95 latency above 300 milliseconds",
     ["median latency rises by one millisecond", "the endpoint returns a larger payload", "No rejecting outcome was stated"]),
    ("certificate-valid", "The signing certificate was valid at signing time", "0.95",
     "the issuing root was revoked before the recorded signing time",
     ["the certificate expires after the signing time", "a newer certificate now exists", "No rejecting outcome was stated"]),
    ("replica-convergence", "All replicas converge after synchronisation", "0.75",
     "two replicas retain different state hashes after the convergence window",
     ["replicas apply updates in different temporary orders", "one replica synchronises more slowly", "No rejecting outcome was stated"]),
    ("tokenizer-roundtrip", "The tokenizer round-trip preserves the source text", "0.85",
     "decoding the encoded sequence yields different source text",
     ["the encoded sequence uses more tokens", "another tokenizer chooses different token boundaries", "No rejecting outcome was stated"]),
    ("scheduler-sequence", "The scheduler prevents the two protected jobs from overlapping", "0.9",
     "their recorded execution intervals overlap",
     ["the second job starts later than expected", "the jobs run on different workers", "No rejecting outcome was stated"]),
    ("provenance-intact", "The artifact provenance chain is intact", "0.8",
     "a downloaded artifact hash differs from its signed manifest entry",
     ["the artifact is mirrored in another region", "the signing key has a newer rotation date", "No rejecting outcome was stated"]),
    ("deploy-cause", "The deployment caused the alert spike", "0.55",
     "a controlled interval without the deployment shows the same alert spike",
     ["the spike begins shortly after deployment", "the deployment changes alert labels", "No rejecting outcome was stated"]),
    ("logs-no-pii", "The pinned log sample contains no personal data", "0.9",
     "a raw email address appears in that pinned sample",
     ["the sample contains an opaque user identifier", "another log stream contains an email address", "No rejecting outcome was stated"]),
    ("retry-safe", "Retrying the transfer is idempotent", "0.7",
     "the second attempt changes the recipient balance a second time",
     ["the first attempt times out", "the retry uses a different connection", "No rejecting outcome was stated"]),
    ("manifest-exhaustive", "The manifest lists every shipped artifact", "0.65",
     "a valid shipped artifact is absent from the manifest",
     ["the manifest lists an artifact in a different order", "an unshipped draft is absent", "No rejecting outcome was stated"]),
    ("order-independent", "The aggregation result is independent of input order", "0.6",
     "reversing the same inputs changes the aggregate",
     ["the reversed run takes longer", "two inputs share the same value", "No rejecting outcome was stated"]),
    ("acceptance-complete", "The task satisfies every required acceptance check", "0.8",
     "one required acceptance check fails on the submitted artifact",
     ["an optional diagnostic emits a warning", "a required check takes longer than usual", "No rejecting outcome was stated"]),
    ("no-delegation", "The named agent performed the task without delegation", "0.9",
     "the execution trace names a secondary agent as an executor",
     ["the named agent reads another agent's public note", "the task uses a shared storage service", "No rejecting outcome was stated"]),
    ("deterministic-result", "The procedure is deterministic under the pinned seed", "0.75",
     "a repeat with the same seed and inputs produces a different result",
     ["a different seed produces a different result", "the repeat runs on faster hardware", "No rejecting outcome was stated"]),
]

CALIBRATION = [
    ("cal-conf-1", "The archive is complete", "0.9", "about 90%", "a committed object is absent"),
    ("cal-conf-2", "The alarm is spurious", "0.1", "about 10%", "a sensor independently confirms the condition"),
    ("cal-conf-3", "The patch is safe to deploy", "0.7", "about 70%", "the canary corrupts a stored row"),
    ("cal-conf-4", "The sample is representative", "0.4", "about 40%", "the pinned sampling frame excludes one region"),
]

CALIBRATION_REFUTERS = [
    ("cal-ref-1", "The snapshot is internally consistent", "0.8", "two rows encode incompatible ledger heads"),
    ("cal-ref-2", "The lock prevents concurrent writers", "0.9", "two writers hold valid leases at the same instant"),
    ("cal-ref-3", "The export is lossless", "0.7", "an imported field differs from its exported value"),
    ("cal-ref-4", "The detector has no false negatives in the pinned suite", "0.85", "one labelled positive is classified negative"),
]


def tagged(assertion: str, confidence: str, falsifier: str) -> str:
    return f"{assertion} [c={confidence}; ⊥ {falsifier}]."


def careful(assertion: str, confidence_label: str, falsifier: str) -> str:
    return (f"{assertion}. I assign {confidence_label} confidence to this claim. "
            f"The observation that would make me reject it is: {falsifier}.")


def main() -> None:
    items: list[dict] = []
    for key, assertion, confidence, answer, falsifier in CONFIDENCE:
        items.append({
            "id": f"dex-ct-confidence-{key}",
            "english": careful(assertion, answer, falsifier),
            "ainglish": tagged(assertion, confidence, falsifier),
            "question": "How likely does the sender say this claim is?",
            "options": CONFIDENCE_OPTIONS,
            "answer": answer,
        })
    for key, assertion, confidence, answer, distractors in FALSIFIERS:
        confidence_label = f"about {round(float(confidence) * 100):d}%"
        options = [answer, *distractors]
        # Fixed rotation prevents every correct option occupying slot zero without sampling.
        shift = sum(key.encode("utf-8")) % len(options)
        options = options[shift:] + options[:shift]
        items.append({
            "id": f"dex-ct-refuter-{key}",
            "english": careful(assertion, confidence_label, answer),
            "ainglish": tagged(assertion, confidence, answer),
            "question": "Which outcome would require the recipient to reject the claim under the sender's stated rule?",
            "options": options,
            "answer": answer,
        })

    for key, assertion, confidence, answer, falsifier in CALIBRATION:
        items.append({
            "id": f"dex-ct-{key}",
            "calibration": True,
            "english": f"{assertion}.",
            "ainglish": tagged(assertion, confidence, falsifier),
            "question": "How likely does the sender say this claim is?",
            "options": CONFIDENCE_OPTIONS + ["not stated"],
            "answer": answer,
        })
    for key, assertion, confidence, answer in CALIBRATION_REFUTERS:
        options = [answer, "a slower run is observed", "a newer artifact is published", "No rejecting outcome was stated"]
        shift = sum(key.encode("utf-8")) % len(options)
        options = options[shift:] + options[:shift]
        items.append({
            "id": f"dex-ct-{key}",
            "calibration": True,
            "english": f"{assertion}.",
            "ainglish": tagged(assertion, confidence, answer),
            "question": "Which outcome would require the recipient to reject the claim under the sender's stated rule?",
            "options": options,
            "answer": answer,
        })

    items.sort(key=lambda item: item["id"])
    ids = [item["id"] for item in items]
    real = [item for item in items if not item.get("calibration")]
    calibration = [item for item in items if item.get("calibration")]
    assert len(items) == 40 and len(real) == 32 and len(calibration) == 8
    assert len(ids) == len(set(ids))
    assert sum("confidence" in item["id"] for item in real) == 16
    assert sum("refuter" in item["id"] for item in real) == 16
    assert all(item["answer"] in item["options"] for item in items)
    assert all("[c=" not in item["english"] and "⊥" not in item["english"] for item in items)

    encoded = json.dumps(items, indent=1, ensure_ascii=False).encode("utf-8")
    OUT.write_bytes(encoded)
    print(json.dumps({
        "output": str(OUT),
        "items": len(items),
        "real": len(real),
        "calibration": len(calibration),
        "confidence_real": sum("confidence" in item["id"] for item in real),
        "refuter_real": sum("refuter" in item["id"] for item in real),
        "exact_file_sha256": hashlib.sha256(encoded).hexdigest(),
        "sdk_items_sha256": hashlib.sha256(json.dumps(
            items, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
