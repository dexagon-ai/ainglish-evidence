"""Frozen answer-bearing pairs for three realistic token-delta replications.

This module deliberately does not import or call a tokenizer.  The source is
published before any attempt is minted and before any tokenizer resource is
loaded.
"""

from __future__ import annotations


TARGETS = {
    "idempotent": {
        "slug": "idempotent-no-retry-say-whether-re-running-an-action-is-safe",
        "title": "idempotent / no-retry",
        "replicates_hash": "48a5bc7484ce4b21f892a5859cc1e67380c374ae3e75ba4650c8d0ece1b49c4d",
        "forms": ["idempotent", "no-retry"],
        "pairs": [
            {
                "item_id": "idempotent/content-cache",
                "form": "idempotent",
                "english": "Persist the job result under its content hash. Repeating this action after an uncertain response is permitted because it cannot change the final state beyond the first execution.",
                "ainglish": "Persist the job result under its content hash, idempotent.",
            },
            {
                "item_id": "idempotent/timezone",
                "form": "idempotent",
                "english": "Set the account timezone to UTC. Repeating this action after an uncertain response is permitted because it cannot change the final state beyond the first execution.",
                "ainglish": "Set the account timezone to UTC, idempotent.",
            },
            {
                "item_id": "idempotent/label",
                "form": "idempotent",
                "english": "Ensure that the incident has the urgent label. Repeating this action after an uncertain response is permitted because it cannot change the final state beyond the first execution.",
                "ainglish": "Ensure that the incident has the urgent label, idempotent.",
            },
            {
                "item_id": "idempotent/blob",
                "form": "idempotent",
                "english": "Store block 61 under its checksum. Repeating this action after an uncertain response is permitted because it cannot change the final state beyond the first execution.",
                "ainglish": "Store block 61 under its checksum, idempotent.",
            },
            {
                "item_id": "idempotent/routing",
                "form": "idempotent",
                "english": "Replace the routing table with version 9. Repeating this action after an uncertain response is permitted because it cannot change the final state beyond the first execution.",
                "ainglish": "Replace the routing table with version 9, idempotent.",
            },
            {
                "item_id": "idempotent/cache-delete",
                "form": "idempotent",
                "english": "Delete cache entry 83. Repeating this action after an uncertain response is permitted because it cannot change the final state beyond the first execution.",
                "ainglish": "Delete cache entry 83, idempotent.",
            },
            {
                "item_id": "idempotent/policy",
                "form": "idempotent",
                "english": "Set the workspace policy to read-only. Repeating this action after an uncertain response is permitted because it cannot change the final state beyond the first execution.",
                "ainglish": "Set the workspace policy to read-only, idempotent.",
            },
            {
                "item_id": "idempotent/membership",
                "form": "idempotent",
                "english": "Reconcile the team membership to Alice and Bo. Repeating this action after an uncertain response is permitted because it cannot change the final state beyond the first execution.",
                "ainglish": "Reconcile the team membership to Alice and Bo, idempotent.",
            },
            {
                "item_id": "no-retry/payout",
                "form": "no-retry",
                "english": "Issue the nonrefundable payout for invoice 413. Run this action exactly once; if completion is uncertain, verify or escalate before acting again because repetition would materially change the outcome.",
                "ainglish": "Issue the nonrefundable payout for invoice 413, no-retry.",
            },
            {
                "item_id": "no-retry/counter",
                "form": "no-retry",
                "english": "Increment the external sequence counter. Run this action exactly once; if completion is uncertain, verify or escalate before acting again because repetition would materially change the outcome.",
                "ainglish": "Increment the external sequence counter, no-retry.",
            },
            {
                "item_id": "no-retry/recovery-code",
                "form": "no-retry",
                "english": "Consume recovery code Delta-7. Run this action exactly once; if completion is uncertain, verify or escalate before acting again because repetition would materially change the outcome.",
                "ainglish": "Consume recovery code Delta-7, no-retry.",
            },
            {
                "item_id": "no-retry/parcel",
                "form": "no-retry",
                "english": "Dispatch the physical parcel to the consignee. Run this action exactly once; if completion is uncertain, verify or escalate before acting again because repetition would materially change the outcome.",
                "ainglish": "Dispatch the physical parcel to the consignee, no-retry.",
            },
            {
                "item_id": "no-retry/charge",
                "form": "no-retry",
                "english": "Append the monthly service charge to the ledger. Run this action exactly once; if completion is uncertain, verify or escalate before acting again because repetition would materially change the outcome.",
                "ainglish": "Append the monthly service charge to the ledger, no-retry.",
            },
            {
                "item_id": "no-retry/key-rotation",
                "form": "no-retry",
                "english": "Rotate the signing key and invalidate its active sessions. Run this action exactly once; if completion is uncertain, verify or escalate before acting again because repetition would materially change the outcome.",
                "ainglish": "Rotate the signing key and invalidate its active sessions, no-retry.",
            },
            {
                "item_id": "no-retry/launch",
                "form": "no-retry",
                "english": "Send the launch command to controller Aster. Run this action exactly once; if completion is uncertain, verify or escalate before acting again because repetition would materially change the outcome.",
                "ainglish": "Send the launch command to controller Aster, no-retry.",
            },
            {
                "item_id": "no-retry/voucher",
                "form": "no-retry",
                "english": "Redeem the one-use vendor voucher. Run this action exactly once; if completion is uncertain, verify or escalate before acting again because repetition would materially change the outcome.",
                "ainglish": "Redeem the one-use vendor voucher, no-retry.",
            },
        ],
    },
    "parallel": {
        "slug": "in-parallel-in-sequence-say-whether-listed-actions-may-overl-2",
        "title": "in-parallel / in-sequence",
        "replicates_hash": "7e6f2f3da5a84a2c5e178f2231d2e251bac2216acf1be161f54ce4a190e0fff3",
        "forms": ["in-parallel", "in-sequence"],
        "pairs": [
            {
                "item_id": "in-parallel/indexes",
                "form": "in-parallel",
                "english": "Validate the artifact index and validate the symbol index without waiting for either earlier-listed validation to reach a terminal outcome; their intervals should overlap and the written order creates no precedence.",
                "ainglish": "Validate the artifact index; validate the symbol index, in-parallel.",
            },
            {
                "item_id": "in-parallel/regions",
                "form": "in-parallel",
                "english": "Query the east replica and query the west replica without waiting for either earlier-listed query to reach a terminal outcome; their intervals should overlap and the written order creates no precedence.",
                "ainglish": "Query the east replica; query the west replica, in-parallel.",
            },
            {
                "item_id": "in-parallel/prewarm",
                "form": "in-parallel",
                "english": "Prewarm the package cache and prewarm the search index without waiting for either earlier-listed operation to reach a terminal outcome; their intervals should overlap and the written order creates no precedence.",
                "ainglish": "Prewarm the package cache; prewarm the search index, in-parallel.",
            },
            {
                "item_id": "in-parallel/sensors",
                "form": "in-parallel",
                "english": "Poll the pressure sensor and poll the temperature sensor without waiting for either earlier-listed poll to reach a terminal outcome; their intervals should overlap and the written order creates no precedence.",
                "ainglish": "Poll the pressure sensor; poll the temperature sensor, in-parallel.",
            },
            {
                "item_id": "in-parallel/builds",
                "form": "in-parallel",
                "english": "Build the client package and build the server package without waiting for either earlier-listed build to reach a terminal outcome; their intervals should overlap and the written order creates no precedence.",
                "ainglish": "Build the client package; build the server package, in-parallel.",
            },
            {
                "item_id": "in-parallel/mirrors",
                "form": "in-parallel",
                "english": "Fetch the north mirror and fetch the south mirror without waiting for either earlier-listed fetch to reach a terminal outcome; their intervals should overlap and the written order creates no precedence.",
                "ainglish": "Fetch the north mirror; fetch the south mirror, in-parallel.",
            },
            {
                "item_id": "in-parallel/audits",
                "form": "in-parallel",
                "english": "Audit the access log and audit the billing log without waiting for either earlier-listed audit to reach a terminal outcome; their intervals should overlap and the written order creates no precedence.",
                "ainglish": "Audit the access log; audit the billing log, in-parallel.",
            },
            {
                "item_id": "in-parallel/three-observations",
                "form": "in-parallel",
                "english": "Sample the inlet, sample the outlet, and tail the controller log without waiting for any earlier-listed observation to reach a terminal outcome; their intervals should overlap and the written order creates no precedence.",
                "ainglish": "Sample the inlet; sample the outlet; tail the controller log, in-parallel.",
            },
            {
                "item_id": "in-sequence/credential",
                "form": "in-sequence",
                "english": "Revoke the temporary credential, wait until revocation reaches success or failure, and only then rotate its signing secret; whether failure prevents rotation is a separate unstated condition.",
                "ainglish": "Revoke the temporary credential; rotate its signing secret, in-sequence.",
            },
            {
                "item_id": "in-sequence/archive",
                "form": "in-sequence",
                "english": "Snapshot the archive, wait until the snapshot reaches success or failure, and only then purge expired segments; whether failure prevents purging is a separate unstated condition.",
                "ainglish": "Snapshot the archive; purge expired segments, in-sequence.",
            },
            {
                "item_id": "in-sequence/queue",
                "form": "in-sequence",
                "english": "Drain the work queue, wait until draining reaches success or failure, and only then change its schema; whether failure prevents the change is a separate unstated condition.",
                "ainglish": "Drain the work queue; change its schema, in-sequence.",
            },
            {
                "item_id": "in-sequence/migration",
                "form": "in-sequence",
                "english": "Apply migration 17, wait until it reaches success or failure, and only then start the workers; whether failure prevents startup is a separate unstated condition.",
                "ainglish": "Apply migration 17; start the workers, in-sequence.",
            },
            {
                "item_id": "in-sequence/backup",
                "form": "in-sequence",
                "english": "Finish the database backup, wait until it reaches success or failure, and only then compact the journal; whether failure prevents compaction is a separate unstated condition.",
                "ainglish": "Finish the database backup; compact the journal, in-sequence.",
            },
            {
                "item_id": "in-sequence/certificate",
                "form": "in-sequence",
                "english": "Install the renewed certificate, wait until installation reaches success or failure, and only then reload the gateway; whether failure prevents reload is a separate unstated condition.",
                "ainglish": "Install the renewed certificate; reload the gateway, in-sequence.",
            },
            {
                "item_id": "in-sequence/export",
                "form": "in-sequence",
                "english": "Seal the export bundle, wait until sealing reaches success or failure, and only then publish its checksum; whether failure prevents publication is a separate unstated condition.",
                "ainglish": "Seal the export bundle; publish its checksum, in-sequence.",
            },
            {
                "item_id": "in-sequence/three-actions",
                "form": "in-sequence",
                "english": "Stop intake, wait until it reaches success or failure, then drain workers, wait until that reaches success or failure, and only then replace the broker; each failure condition remains separately unstated.",
                "ainglish": "Stop intake; drain workers; replace the broker, in-sequence.",
            },
        ],
    },
    "behalf": {
        "slug": "on-behalf-of-principal-mark-envoy-written-messages",
        "title": "on-behalf-of(<principal>)",
        "replicates_hash": "ccbf51cbea924265869fa6cd0ff0d78ca9990a5dda10bb34ea94b8a231cb990e",
        "forms": ["on-behalf-of"],
        "pairs": [
            {
                "item_id": "behalf/aurora-invoice",
                "form": "on-behalf-of",
                "english": "Approve invoice 413. This message was written by the posting handle on behalf of Aurora; Aurora owns its content only after countersigning in Aurora's own voice, and no obligation binds Aurora before that ratification.",
                "ainglish": "Approve invoice 413. on-behalf-of(Aurora)",
            },
            {
                "item_id": "behalf/borealis-release",
                "form": "on-behalf-of",
                "english": "Release build 81. This message was written by the posting handle on behalf of Borealis; Borealis owns its content only after countersigning in Borealis's own voice, and no obligation binds Borealis before that ratification.",
                "ainglish": "Release build 81. on-behalf-of(Borealis)",
            },
            {
                "item_id": "behalf/cedar-window",
                "form": "on-behalf-of",
                "english": "Reserve the Tuesday maintenance window. This message was written by the posting handle on behalf of Cedar; Cedar owns its content only after countersigning in Cedar's own voice, and no obligation binds Cedar before that ratification.",
                "ainglish": "Reserve the Tuesday maintenance window. on-behalf-of(Cedar)",
            },
            {
                "item_id": "behalf/delta-policy",
                "form": "on-behalf-of",
                "english": "Adopt policy revision 6. This message was written by the posting handle on behalf of Delta; Delta owns its content only after countersigning in Delta's own voice, and no obligation binds Delta before that ratification.",
                "ainglish": "Adopt policy revision 6. on-behalf-of(Delta)",
            },
            {
                "item_id": "behalf/eider-archive",
                "form": "on-behalf-of",
                "english": "Archive the completed case. This message was written by the posting handle on behalf of Eider; Eider owns its content only after countersigning in Eider's own voice, and no obligation binds Eider before that ratification.",
                "ainglish": "Archive the completed case. on-behalf-of(Eider)",
            },
            {
                "item_id": "behalf/fjord-budget",
                "form": "on-behalf-of",
                "english": "Accept the revised budget. This message was written by the posting handle on behalf of Fjord; Fjord owns its content only after countersigning in Fjord's own voice, and no obligation binds Fjord before that ratification.",
                "ainglish": "Accept the revised budget. on-behalf-of(Fjord)",
            },
            {
                "item_id": "behalf/garnet-order",
                "form": "on-behalf-of",
                "english": "Cancel purchase order 52. This message was written by the posting handle on behalf of Garnet; Garnet owns its content only after countersigning in Garnet's own voice, and no obligation binds Garnet before that ratification.",
                "ainglish": "Cancel purchase order 52. on-behalf-of(Garnet)",
            },
            {
                "item_id": "behalf/harbor-domain",
                "form": "on-behalf-of",
                "english": "Transfer the example.net domain. This message was written by the posting handle on behalf of Harbor; Harbor owns its content only after countersigning in Harbor's own voice, and no obligation binds Harbor before that ratification.",
                "ainglish": "Transfer the example.net domain. on-behalf-of(Harbor)",
            },
            {
                "item_id": "behalf/indigo-audit",
                "form": "on-behalf-of",
                "english": "Publish the audit response. This message was written by the posting handle on behalf of Indigo; Indigo owns its content only after countersigning in Indigo's own voice, and no obligation binds Indigo before that ratification.",
                "ainglish": "Publish the audit response. on-behalf-of(Indigo)",
            },
            {
                "item_id": "behalf/juniper-renewal",
                "form": "on-behalf-of",
                "english": "Renew the annual subscription. This message was written by the posting handle on behalf of Juniper; Juniper owns its content only after countersigning in Juniper's own voice, and no obligation binds Juniper before that ratification.",
                "ainglish": "Renew the annual subscription. on-behalf-of(Juniper)",
            },
            {
                "item_id": "behalf/kepler-notice",
                "form": "on-behalf-of",
                "english": "Send the breach notice. This message was written by the posting handle on behalf of Kepler; Kepler owns its content only after countersigning in Kepler's own voice, and no obligation binds Kepler before that ratification.",
                "ainglish": "Send the breach notice. on-behalf-of(Kepler)",
            },
            {
                "item_id": "behalf/linden-record",
                "form": "on-behalf-of",
                "english": "Correct the public record. This message was written by the posting handle on behalf of Linden; Linden owns its content only after countersigning in Linden's own voice, and no obligation binds Linden before that ratification.",
                "ainglish": "Correct the public record. on-behalf-of(Linden)",
            },
            {
                "item_id": "behalf/maple-license",
                "form": "on-behalf-of",
                "english": "Grant the dataset licence. This message was written by the posting handle on behalf of Maple; Maple owns its content only after countersigning in Maple's own voice, and no obligation binds Maple before that ratification.",
                "ainglish": "Grant the dataset licence. on-behalf-of(Maple)",
            },
            {
                "item_id": "behalf/nimbus-route",
                "form": "on-behalf-of",
                "english": "Approve the emergency route. This message was written by the posting handle on behalf of Nimbus; Nimbus owns its content only after countersigning in Nimbus's own voice, and no obligation binds Nimbus before that ratification.",
                "ainglish": "Approve the emergency route. on-behalf-of(Nimbus)",
            },
            {
                "item_id": "behalf/orchid-settlement",
                "form": "on-behalf-of",
                "english": "Accept the settlement terms. This message was written by the posting handle on behalf of Orchid; Orchid owns its content only after countersigning in Orchid's own voice, and no obligation binds Orchid before that ratification.",
                "ainglish": "Accept the settlement terms. on-behalf-of(Orchid)",
            },
            {
                "item_id": "behalf/pelican-access",
                "form": "on-behalf-of",
                "english": "Revoke the contractor's access. This message was written by the posting handle on behalf of Pelican; Pelican owns its content only after countersigning in Pelican's own voice, and no obligation binds Pelican before that ratification.",
                "ainglish": "Revoke the contractor's access. on-behalf-of(Pelican)",
            },
        ],
    },
}
