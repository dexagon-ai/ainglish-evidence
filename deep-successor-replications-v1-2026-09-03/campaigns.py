"""Wholly fresh complete-pair carriers for two Deep Seeker successor originals."""


PART_CHOSEN_CAPPED = [
    {"stratum": "part-chosen", "english": "I examined the 57 cases that the risk-score-decile rule selected from the 561 filed cases; that rule determined which cases entered the examination.", "ainglish": "part-chosen(risk-score-decile): I examined 57 of the 561 filed cases."},
    {"stratum": "part-chosen", "english": "I verified the 41 objects that the hash-prefix-3c rule selected from the 707 stored objects; that rule determined which objects entered verification.", "ainglish": "part-chosen(hash-prefix-3c): I verified 41 of the 707 stored objects."},
    {"stratum": "part-chosen", "english": "I checked the 63 licences that the June-renewal rule selected from the 418 active licences; that rule determined which licences entered the check.", "ainglish": "part-chosen(june-renewal): I checked 63 of the 418 active licences."},
    {"stratum": "part-chosen", "english": "I decoded the 88 packets that seeded lottery 204 selected from the 900 captured packets; the lottery determined which packets entered decoding.", "ainglish": "part-chosen(seeded-lottery-204): I decoded 88 of the 900 captured packets."},
    {"stratum": "part-chosen", "english": "I visited the 52 depots that the north-zone rule selected from the 319 listed depots; that rule determined which depots entered the visit.", "ainglish": "part-chosen(north-zone): I visited 52 of the 319 listed depots."},
    {"stratum": "part-chosen", "english": "I reconciled the 76 accounts that the suffix-X rule selected from the 602 open accounts; that rule determined which accounts entered reconciliation.", "ainglish": "part-chosen(suffix-x): I reconciled 76 of the 602 open accounts."},
    {"stratum": "part-chosen", "english": "I assessed the 64 claims that stratified-sample-v9 selected from the 512 settled claims; that rule determined which claims entered assessment.", "ainglish": "part-chosen(stratified-sample-v9): I assessed 64 of the 512 settled claims."},
    {"stratum": "part-chosen", "english": "I labelled the 39 images that the low-confidence rule selected from the 285 queued images; that rule determined which images entered labelling.", "ainglish": "part-chosen(low-confidence): I labelled 39 of the 285 queued images."},
    {"stratum": "part-capped", "english": "I resolved 150 of the 694 tickets; the pager API stopped at its 150-ticket limit, so I could not resolve the remaining tickets.", "ainglish": "part-capped(pager-api-150): I resolved 150 of the 694 tickets."},
    {"stratum": "part-capped", "english": "I searched 82 of the 431 archives; the forty-five-minute scan budget expired, so I could not search the remaining archives.", "ainglish": "part-capped(scan-budget-45m): I searched 82 of the 431 archives."},
    {"stratum": "part-capped", "english": "I inspected 47 of the 260 sites; my access covered only the eastern zone, so I could not inspect the remaining sites.", "ainglish": "part-capped(access-east): I inspected 47 of the 260 sites."},
    {"stratum": "part-capped", "english": "I reconstructed 69 of the 344 traces; the twelve-gigabyte memory ceiling stopped reconstruction, so I could not process the remainder.", "ainglish": "part-capped(memory-12gb): I reconstructed 69 of the 344 traces."},
    {"stratum": "part-capped", "english": "I reviewed 84 of the 506 messages; the service retained only twenty-one days, so I could not review the older messages.", "ainglish": "part-capped(retention-21d): I reviewed 84 of the 506 messages."},
    {"stratum": "part-capped", "english": "I compared 750 of the 1,936 rows; the export ended at its 750-row ceiling, so I could not compare the remaining rows.", "ainglish": "part-capped(export-750): I compared 750 of the 1,936 rows."},
    {"stratum": "part-capped", "english": "I tested 200 of the 1,108 endpoints; the rate limiter stopped the run at 200 checks, so I could not test the remaining endpoints.", "ainglish": "part-capped(rate-limit-200): I tested 200 of the 1,108 endpoints."},
    {"stratum": "part-capped", "english": "I read 58 of the 247 meters; the field unit exhausted its battery, so I could not read the remaining meters.", "ainglish": "part-capped(battery-stop): I read 58 of the 247 meters."},
]


SNAPSHOT_LIVE_VIEW = [
    {"stratum": "send-snapshot", "english": "Send Leto an independent fixed copy of the incident map at revision r23; later edits or revoked source access cannot alter or withdraw that copy.", "ainglish": "send-snapshot(incident-map@r23, to=Leto)."},
    {"stratum": "send-snapshot", "english": "Send the audit team an independent fixed copy of the inventory as of 2026-09-02; later changes to the canonical inventory cannot alter or withdraw that copy.", "ainglish": "send-snapshot(inventory@2026-09-02, to=audit-team)."},
    {"stratum": "send-snapshot", "english": "Send Vela an independent fixed copy of policy version 31; later policy revisions or access revocation cannot alter or withdraw that copy.", "ainglish": "send-snapshot(policy@v31, to=Vela)."},
    {"stratum": "send-snapshot", "english": "Send the archive desk an independent fixed copy of the index at digest sha256-7b2d; later index edits cannot alter or withdraw that copy.", "ainglish": "send-snapshot(index@sha256-7b2d, to=archive-desk)."},
    {"stratum": "send-snapshot", "english": "Did Neri send legal an independent fixed copy of contract revision c9 that later source changes cannot alter or withdraw?", "ainglish": "Did Neri send-snapshot(contract@c9, to=legal)?"},
    {"stratum": "send-snapshot", "english": "Do not send operations an independent fixed copy of the current rota; operations must continue reading the changing canonical rota.", "ainglish": "Do not send-snapshot(rota@current, to=operations)."},
    {"stratum": "send-snapshot", "english": "Mara requested an independent fixed copy of blueprint issue 14 for procurement; later blueprint edits or access revocation cannot alter or withdraw it.", "ainglish": "Mara requested send-snapshot(blueprint@issue-14, to=procurement)."},
    {"stratum": "send-snapshot", "english": "Send the regulator an independent fixed copy of the emissions report at filing f6; later source corrections cannot alter or withdraw that copy.", "ainglish": "send-snapshot(emissions-report@f6, to=regulator)."},
    {"stratum": "grant-live-view", "english": "Grant Leto revocable read-only access to the canonical incident map, showing its current contents on each successful read; do not send an independent fixed copy.", "ainglish": "grant-live-view(incident-map, to=Leto)."},
    {"stratum": "grant-live-view", "english": "Grant the audit team revocable read-only access to the canonical inventory, showing its current contents on each successful read; do not send an independent fixed copy.", "ainglish": "grant-live-view(inventory, to=audit-team)."},
    {"stratum": "grant-live-view", "english": "Grant Vela revocable read-only access to the canonical policy, showing its current contents on each successful read; do not send an independent fixed copy.", "ainglish": "grant-live-view(policy, to=Vela)."},
    {"stratum": "grant-live-view", "english": "Grant the archive desk revocable read-only access to the canonical index, showing its current contents on each successful read; do not send an independent fixed copy.", "ainglish": "grant-live-view(index, to=archive-desk)."},
    {"stratum": "grant-live-view", "english": "Did Neri grant legal revocable read-only access to the canonical contract, showing current contents without sending a fixed copy?", "ainglish": "Did Neri grant-live-view(contract, to=legal)?"},
    {"stratum": "grant-live-view", "english": "Do not grant operations revocable read-only access to the canonical rota, and do not expose that live object to operations.", "ainglish": "Do not grant-live-view(rota, to=operations)."},
    {"stratum": "grant-live-view", "english": "Mara requested revocable read-only access for procurement to the canonical blueprint, showing current contents without sending a fixed copy.", "ainglish": "Mara requested grant-live-view(blueprint, to=procurement)."},
    {"stratum": "grant-live-view", "english": "Grant the regulator revocable read-only access to the canonical emissions report, showing its current contents on each successful read; do not send an independent fixed copy.", "ainglish": "grant-live-view(emissions-report, to=regulator)."},
]


CAMPAIGNS = [
    {
        "name": "part-chosen-part-capped",
        "slug": "part-chosen-rule-part-capped-limiter-was-the-edge-of-the-set",
        "target_attempt_id": "8dbf38ab-f6db-4a80-848a-ecc32fb2cdab",
        "target_hash": "13a722dd4d8b0206a42ff6450c5de1fea05a0f828d14254c61889bd7af894e83",
        "test_set": PART_CHOSEN_CAPPED,
    },
    {
        "name": "send-snapshot-grant-live-view",
        "slug": "send-snapshot-version-ref-to-recipient-grant-live-view",
        "target_attempt_id": "99cd4e55-b664-4db6-92c6-d6a7525b89ec",
        "target_hash": "74365dc61028e7b0f0590faf4537bdcb779fdbf8997d7eba736a7e65b24fedc5",
        "test_set": SNAPSHOT_LIVE_VIEW,
    },
]
