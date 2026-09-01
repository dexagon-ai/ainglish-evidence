"""Frozen fresh-input corpus for the as_of(t) / until(t) token replication."""


def pair(item_id: str, form: str, english: str, ainglish: str) -> dict[str, str]:
    return {
        "item_id": item_id,
        "form": form,
        "english": english,
        "ainglish": ainglish,
    }


TEST_SET = [
    pair(
        "asof-dns-failover",
        "as_of",
        "The DNS failover path answered from both regions, and the supporting probe was current as of 2026-09-01T04:20Z.",
        "The DNS failover path answered from both regions as_of(2026-09-01T04:20Z).",
    ),
    pair(
        "asof-accessibility-captions",
        "as_of",
        "Every training video had accessibility captions, and the supporting inventory was current as of 2026-08-31T16:40Z.",
        "Every training video had accessibility captions as_of(2026-08-31T16:40Z).",
    ),
    pair(
        "asof-cold-storage",
        "as_of",
        "The cold-storage catalogue contained no orphaned objects, and the supporting audit was current as of 2026-08-30T11:05Z.",
        "The cold-storage catalogue contained no orphaned objects as_of(2026-08-30T11:05Z).",
    ),
    pair(
        "asof-fire-doors",
        "as_of",
        "All fire doors passed inspection, and the supporting inspection record was current as of 2026-08-27T14:30Z.",
        "All fire doors passed inspection as_of(2026-08-27T14:30Z).",
    ),
    pair(
        "asof-translation-memory",
        "as_of",
        "The translation memory contained every approved locale, and the supporting export was current as of 2026-08-29T19:25Z.",
        "The translation memory contained every approved locale as_of(2026-08-29T19:25Z).",
    ),
    pair(
        "asof-supplier-register",
        "as_of",
        "The supplier register named an owner for every exception, and the supporting review was current as of 2026-08-28T08:55Z.",
        "The supplier register named an owner for every exception as_of(2026-08-28T08:55Z).",
    ),
    pair(
        "asof-telemetry-gap",
        "as_of",
        "The telemetry stream had no missing intervals, and the supporting comparison was current as of 2026-08-31T23:35Z.",
        "The telemetry stream had no missing intervals as_of(2026-08-31T23:35Z).",
    ),
    pair(
        "asof-consent-notices",
        "as_of",
        "The consent notices matched the approved wording, and the supporting sample was current as of 2026-08-26T10:15Z.",
        "The consent notices matched the approved wording as_of(2026-08-26T10:15Z).",
    ),
    pair(
        "until-firewall-exception",
        "until",
        "The temporary firewall exception is only licensed through 2026-09-03T18:00Z; after that time the claim is expired, not an undated green.",
        "The temporary firewall exception applies until(2026-09-03T18:00Z).",
    ),
    pair(
        "until-courier-quote",
        "until",
        "The courier price quotation is only licensed through 2026-09-08T12:00Z; after that time the claim is expired, not an undated green.",
        "The courier price quotation stands until(2026-09-08T12:00Z).",
    ),
    pair(
        "until-emergency-badge",
        "until",
        "The emergency access badge is only licensed through 2026-09-04T07:30Z; after that time the claim is expired, not an undated green.",
        "The emergency access badge is valid until(2026-09-04T07:30Z).",
    ),
    pair(
        "until-venue-reservation",
        "until",
        "The venue reservation is only licensed through 2026-09-22T17:00Z; after that time the claim is expired, not an undated green.",
        "The venue reservation holds until(2026-09-22T17:00Z).",
    ),
    pair(
        "until-data-export",
        "until",
        "The one-time data export approval is only licensed through 2026-09-06T21:45Z; after that time the claim is expired, not an undated green.",
        "The one-time data export approval applies until(2026-09-06T21:45Z).",
    ),
    pair(
        "until-warranty-extension",
        "until",
        "The warranty extension is only licensed through 2026-11-30T23:59Z; after that time the claim is expired, not an undated green.",
        "The warranty extension stands until(2026-11-30T23:59Z).",
    ),
    pair(
        "until-visitor-network",
        "until",
        "The visitor network account is only licensed through 2026-09-02T20:00Z; after that time the claim is expired, not an undated green.",
        "The visitor network account is active until(2026-09-02T20:00Z).",
    ),
    pair(
        "until-research-embargo",
        "until",
        "The research embargo is only licensed through 2026-10-14T09:00Z; after that time the claim is expired, not an undated green.",
        "The research embargo remains until(2026-10-14T09:00Z).",
    ),
]
