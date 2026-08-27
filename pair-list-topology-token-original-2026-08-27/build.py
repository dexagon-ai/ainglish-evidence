#!/usr/bin/env python3
"""Freeze a balanced price carrier without loading any tokenizer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

PAIR_BY_ORDER = [
    ("Asha and Bram review patches X and Y, pair-by-order.", "Asha reviews patch X and Bram reviews patch Y; neither reviews the other listed patch."),
    ("Cora, Deepak, and Elin translate documents D1, D2, and D3, pair-by-order.", "Cora translates D1, Deepak translates D2, and Elin translates D3; none translates another listed document."),
    ("Fara, Gus, Hana, and Ivo inspect machines M1, M2, M3, and M4, pair-by-order.", "Fara inspects M1, Gus inspects M2, Hana inspects M3, and Ivo inspects M4; none inspects another listed machine."),
    ("Jia and Kofi monitor regions North and South, pair-by-order.", "Jia monitors North and Kofi monitors South; neither monitors the other listed region."),
    ("Lina, Marek, and Noor test builds B7, B8, and B9, pair-by-order.", "Lina tests B7, Marek tests B8, and Noor tests B9; none tests another listed build."),
    ("Omar and Pia audit ledgers Red and Blue, pair-by-order.", "Omar audits Red and Pia audits Blue; neither audits the other listed ledger."),
    ("Quin, Rina, Sol, and Tavi index shards S1, S2, S3, and S4, pair-by-order.", "Quin indexes S1, Rina indexes S2, Sol indexes S3, and Tavi indexes S4; none indexes another listed shard."),
    ("Uma, Vik, and Wren edit chapters 2, 4, and 6, pair-by-order.", "Uma edits chapter 2, Vik edits chapter 4, and Wren edits chapter 6; none edits another listed chapter."),
    ("Xena and Yusuf service queues Alpha and Beta, pair-by-order.", "Xena services Alpha and Yusuf services Beta; neither services the other listed queue."),
    ("Zara, Abel, and Bina calibrate sensors P, Q, and R, pair-by-order.", "Zara calibrates P, Abel calibrates Q, and Bina calibrates R; none calibrates another listed sensor."),
    ("Chen, Daria, Emil, and Freya certify releases 10, 11, 12, and 13, pair-by-order.", "Chen certifies release 10, Daria certifies release 11, Emil certifies release 12, and Freya certifies release 13; none certifies another listed release."),
    ("Gita and Hugo route parcels K and L, pair-by-order.", "Gita routes parcel K and Hugo routes parcel L; neither routes the other listed parcel."),
    ("Imani, Jules, and Kira validate reports R1, R2, and R3, pair-by-order.", "Imani validates R1, Jules validates R2, and Kira validates R3; none validates another listed report."),
    ("Leo and Mina back up volumes East and West, pair-by-order.", "Leo backs up East and Mina backs up West; neither backs up the other listed volume."),
    ("Nia, Oleg, Priya, and Rafi observe channels C1, C2, C3, and C4, pair-by-order.", "Nia observes C1, Oleg observes C2, Priya observes C3, and Rafi observes C4; none observes another listed channel."),
    ("Sana, Teo, and Uri reconcile accounts A2, A5, and A8, pair-by-order.", "Sana reconciles A2, Teo reconciles A5, and Uri reconciles A8; none reconciles another listed account."),
]

EVERY_COMBINATION = [
    ("Asha and Bram review patches X and Y, every-combination.", "Asha and Bram each review patches X and Y."),
    ("Cora, Deepak, and Elin translate documents D1, D2, and D3, every-combination.", "Cora, Deepak, and Elin each translate documents D1, D2, and D3."),
    ("Fara, Gus, Hana, and Ivo inspect machines M1, M2, M3, and M4, every-combination.", "Fara, Gus, Hana, and Ivo each inspect machines M1, M2, M3, and M4."),
    ("Jia and Kofi monitor regions North and South, every-combination.", "Jia and Kofi each monitor North and South."),
    ("Lina, Marek, and Noor test builds B7, B8, and B9, every-combination.", "Lina, Marek, and Noor each test builds B7, B8, and B9."),
    ("Omar and Pia audit ledgers Red and Blue, every-combination.", "Omar and Pia each audit ledgers Red and Blue."),
    ("Quin, Rina, Sol, and Tavi index shards S1, S2, S3, and S4, every-combination.", "Quin, Rina, Sol, and Tavi each index shards S1, S2, S3, and S4."),
    ("Uma, Vik, and Wren edit chapters 2, 4, and 6, every-combination.", "Uma, Vik, and Wren each edit chapters 2, 4, and 6."),
    ("Xena and Yusuf service queues Alpha and Beta, every-combination.", "Xena and Yusuf each service queues Alpha and Beta."),
    ("Zara, Abel, and Bina calibrate sensors P, Q, and R, every-combination.", "Zara, Abel, and Bina each calibrate sensors P, Q, and R."),
    ("Chen, Daria, Emil, and Freya certify releases 10, 11, 12, and 13, every-combination.", "Chen, Daria, Emil, and Freya each certify releases 10, 11, 12, and 13."),
    ("Gita and Hugo route parcels K and L, every-combination.", "Gita and Hugo each route parcels K and L."),
    ("Imani, Jules, and Kira validate reports R1, R2, and R3, every-combination.", "Imani, Jules, and Kira each validate reports R1, R2, and R3."),
    ("Leo and Mina back up volumes East and West, every-combination.", "Leo and Mina each back up volumes East and West."),
    ("Nia, Oleg, Priya, and Rafi observe channels C1, C2, C3, and C4, every-combination.", "Nia, Oleg, Priya, and Rafi each observe channels C1, C2, C3, and C4."),
    ("Sana, Teo, and Uri reconcile accounts A2, A5, and A8, every-combination.", "Sana, Teo, and Uri each reconcile accounts A2, A5, and A8."),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    rows = []
    for index, (ainglish, english) in enumerate(PAIR_BY_ORDER, 1):
        rows.append({"item_id": f"pbo-{index:02d}", "form": "pair-by-order", "ainglish": ainglish, "english": english})
    for index, (ainglish, english) in enumerate(EVERY_COMBINATION, 1):
        rows.append({"item_id": f"eco-{index:02d}", "form": "every-combination", "ainglish": ainglish, "english": english})
    forms = ("pair-by-order", "every-combination")
    counts = {form: sum(row["form"] == form for row in rows) for form in forms}
    if len(rows) != 32 or len(rows) & (len(rows) - 1) or counts != {form: 16 for form in forms}:
        raise SystemExit("REFUSING: pair-count or form-balance gate")
    if len({(row["ainglish"], row["english"]) for row in rows}) != 32:
        raise SystemExit("REFUSING: complete pairs are not unique")
    packet = {
        "kind": "ainglish.pair-list-topology-token-items.v1",
        "proposal_slug": "pair-by-order-every-combination-match-two-lists-in-order-or-",
        "metric": "token_delta",
        "forms": list(forms),
        "form_counts": counts,
        "comparison": "registered topology marker versus the shortest complete careful-English wording that fixes every relation between the two named lists",
        "acceptance": {"least_favourable_balanced_mean_at_most": 0},
        "evidentiary_limit": "price prerequisite only; token count cannot establish argument-boundary recovery or comprehension",
        "test_set": rows,
    }
    packet["items_sha256"] = hashlib.sha256(canonical(rows)).hexdigest()
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "token-items.json"
    if target.exists():
        raise SystemExit("REFUSING: token-items.json already exists")
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(rows), "form_counts": counts, "items_sha256": packet["items_sha256"], "content_sha256": packet["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
