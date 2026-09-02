"""Frozen, fresh bare-``may not`` pairs for a token dispute replication."""


def pair(item_id: str, form: str, english: str, ainglish: str) -> dict[str, str]:
    return {
        "item_id": item_id,
        "form": form,
        "english": english,
        "ainglish": ainglish,
    }


TEST_SET = [
    pair(
        "prohibition-archive-lift",
        "may-not-as-prohibition",
        "The archive lift may not carry visitors after closing time.",
        "The archive lift may-not-as-prohibition carry visitors after closing time.",
    ),
    pair(
        "prohibition-audit-key",
        "may-not-as-prohibition",
        "The audit key may not sign a production release.",
        "The audit key may-not-as-prohibition sign a production release.",
    ),
    pair(
        "prohibition-supplier-console",
        "may-not-as-prohibition",
        "A supplier account may not open the payroll console.",
        "A supplier account may-not-as-prohibition open the payroll console.",
    ),
    pair(
        "prohibition-drone-corridor",
        "may-not-as-prohibition",
        "The survey drone may not enter the hospital corridor.",
        "The survey drone may-not-as-prohibition enter the hospital corridor.",
    ),
    pair(
        "prohibition-cache-export",
        "may-not-as-prohibition",
        "The cache worker may not export unredacted records.",
        "The cache worker may-not-as-prohibition export unredacted records.",
    ),
    pair(
        "prohibition-night-shift",
        "may-not-as-prohibition",
        "A night-shift badge may not unlock the research vault.",
        "A night-shift badge may-not-as-prohibition unlock the research vault.",
    ),
    pair(
        "prohibition-review-bot",
        "may-not-as-prohibition",
        "The review bot may not approve its own patch.",
        "The review bot may-not-as-prohibition approve its own patch.",
    ),
    pair(
        "prohibition-courier-ramp",
        "may-not-as-prohibition",
        "The courier van may not use the emergency ramp.",
        "The courier van may-not-as-prohibition use the emergency ramp.",
    ),
    pair(
        "possibility-replica-sync",
        "may-not-as-possibility",
        "The eastern replica may not finish synchronizing before dawn.",
        "The eastern replica may-not-as-possibility finish synchronizing before dawn.",
    ),
    pair(
        "possibility-forecast-refresh",
        "may-not-as-possibility",
        "The coastal forecast may not refresh before the ferry departs.",
        "The coastal forecast may-not-as-possibility refresh before the ferry departs.",
    ),
    pair(
        "possibility-specimen-arrival",
        "may-not-as-possibility",
        "The frozen specimen may not arrive before the laboratory closes.",
        "The frozen specimen may-not-as-possibility arrive before the laboratory closes.",
    ),
    pair(
        "possibility-index-rebuild",
        "may-not-as-possibility",
        "The catalogue index may not rebuild within the maintenance window.",
        "The catalogue index may-not-as-possibility rebuild within the maintenance window.",
    ),
    pair(
        "possibility-appeal-decision",
        "may-not-as-possibility",
        "The appeal decision may not reach the applicant this week.",
        "The appeal decision may-not-as-possibility reach the applicant this week.",
    ),
    pair(
        "possibility-sensor-recover",
        "may-not-as-possibility",
        "The tunnel sensor may not recover after the next restart.",
        "The tunnel sensor may-not-as-possibility recover after the next restart.",
    ),
    pair(
        "possibility-invoice-clear",
        "may-not-as-possibility",
        "The overseas invoice may not clear before the quarter ends.",
        "The overseas invoice may-not-as-possibility clear before the quarter ends.",
    ),
    pair(
        "possibility-balloon-land",
        "may-not-as-possibility",
        "The weather balloon may not land inside the recovery zone.",
        "The weather balloon may-not-as-possibility land inside the recovery zone.",
    ),
]
