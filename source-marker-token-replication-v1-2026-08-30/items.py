"""Frozen answer-bearing pairs for the source-marker token replication.

This module deliberately does not import or call a tokenizer. The source must be
public before the attempt is minted and before any tokenizer resource is loaded.
"""

from __future__ import annotations


SLUG = "observed-reported-by-inferred-from-mark-where-a-claim-came-f"
TITLE = "observed / reported(<by>) / inferred(<from>)"
REPLICATES_HASH = "59f0283e97dde22feed922086dc18f514eddbf9455f18e06166d471e99a68bc7"
FORMS = ["observed", "reported", "inferred"]

PAIRS = [
    {
        "item_id": "observed/migration",
        "form": "observed",
        "english": "I directly ran migration 24 on staging and saw it fail at the foreign-key step; I can produce the run receipt.",
        "ainglish": "observed: migration 24 failed at the foreign-key step on staging.",
    },
    {
        "item_id": "observed/temperature",
        "form": "observed",
        "english": "I directly read 82 degrees Celsius from rack sensor B7; I can produce the sensor receipt.",
        "ainglish": "observed: rack sensor B7 read 82 degrees Celsius.",
    },
    {
        "item_id": "observed/checksum",
        "form": "observed",
        "english": "I directly computed the restored archive checksum and saw that it differed from the signed manifest; I can produce the command receipt.",
        "ainglish": "observed: the restored archive checksum differed from the signed manifest.",
    },
    {
        "item_id": "observed/rate-limit",
        "form": "observed",
        "english": "I directly sent request 771 and received HTTP 429 with a 30-second retry value; I can produce the response receipt.",
        "ainglish": "observed: request 771 returned HTTP 429 with retry-after=30s.",
    },
    {
        "item_id": "observed/robot",
        "form": "observed",
        "english": "I directly watched robot arm K halt before placing the third component; I can produce the controller trace.",
        "ainglish": "observed: robot arm K halted before placing component three.",
    },
    {
        "item_id": "observed/export",
        "form": "observed",
        "english": "I directly opened the completed invoice export and counted 412 data rows; I can produce the export receipt.",
        "ainglish": "observed: the completed invoice export contained 412 data rows.",
    },
    {
        "item_id": "reported/monitor",
        "form": "reported",
        "english": "Monitor-bot reports that the west replica is twelve minutes behind; I have not independently verified that claim.",
        "ainglish": "reported(monitor-bot): the west replica is twelve minutes behind.",
    },
    {
        "item_id": "reported/priya",
        "form": "reported",
        "english": "Priya reports that the supplier accepted the revised delivery date; I have not independently verified that claim.",
        "ainglish": "reported(Priya): the supplier accepted the revised delivery date.",
    },
    {
        "item_id": "reported/vendor",
        "form": "reported",
        "english": "The storage vendor reports that yesterday's missing snapshots are recoverable; I have not independently verified that claim.",
        "ainglish": "reported(storage-vendor): yesterday's missing snapshots are recoverable.",
    },
    {
        "item_id": "reported/audit-team",
        "form": "reported",
        "english": "The audit team reports that every sampled payment had two approvals; I have not independently verified that claim.",
        "ainglish": "reported(audit-team): every sampled payment had two approvals.",
    },
    {
        "item_id": "reported/operator",
        "form": "reported",
        "english": "The satellite operator reports that the antenna is back inside its thermal limit; I have not independently verified that claim.",
        "ainglish": "reported(satellite-operator): the antenna is back inside its thermal limit.",
    },
    {
        "item_id": "inferred/worker",
        "form": "inferred",
        "english": "I conclude from the heartbeat gap and the reassigned lease, without directly observing the process, that worker 14 stopped.",
        "ainglish": "inferred(heartbeat gap plus reassigned lease): worker 14 stopped.",
    },
    {
        "item_id": "inferred/cache",
        "form": "inferred",
        "english": "I conclude from the unchanged origin count and lower response latency, without directly observing cache state, that the edge cache served the request.",
        "ainglish": "inferred(unchanged origin count plus lower latency): the edge cache served the request.",
    },
    {
        "item_id": "inferred/key",
        "form": "inferred",
        "english": "I conclude from the new signer fingerprint and rejected old sessions, without directly observing the rotation, that the signing key changed.",
        "ainglish": "inferred(new signer fingerprint plus rejected old sessions): the signing key changed.",
    },
    {
        "item_id": "inferred/drain",
        "form": "inferred",
        "english": "I conclude from zero queue depth and stable completion counters, without directly inspecting every task, that the batch drained.",
        "ainglish": "inferred(zero queue depth plus stable completion counters): the batch drained.",
    },
    {
        "item_id": "inferred/failover",
        "form": "inferred",
        "english": "I conclude from the changed leader epoch and uninterrupted writes, without directly observing the election, that failover completed.",
        "ainglish": "inferred(changed leader epoch plus uninterrupted writes): failover completed.",
    },
]
