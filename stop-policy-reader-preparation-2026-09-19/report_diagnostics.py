"""Count predeclared learnability subsets without changing the official SDK result.

The inputs are retained SDK scientific cell-result rows, not regenerated answers.
This diagnostic is not a measurement-submission command.
"""
import json
import random
from collections import defaultdict
from pathlib import Path


def summarize(items, readers, rows):
    real = {item["id"]: item for item in items if not item.get("calibration")}
    expected = {(ident, reader, arm) for ident in real for reader in readers for arm in ("english", "ainglish")}
    indexed = {}
    for row in rows:
        key = (row["item_id"], row["reader"], row["arm"])
        if key not in expected or key in indexed:
            raise ValueError("unexpected or duplicate retained scientific cell")
        indexed[key] = row
        if row["expected"] != real[row["item_id"]]["answer"]:
            raise ValueError("retained cell gold differs from the frozen input")
        actual = row.get("answer")
        if actual:
            correct = actual.casefold() == row["expected"].casefold()
            if row.get("correct") is not correct:
                raise ValueError("retained grade differs from the retained parsed answer")

    def count(arm, selected_items, selected_readers=readers):
        keys = [(ident, reader, arm) for ident in selected_items for reader in selected_readers]
        live = [indexed[key] for key in keys if key in indexed and indexed[key].get("answer")]
        correct = sum(row["correct"] is True for row in live)
        complete = len(live) == len(keys)
        return {"correct": correct, "scored": len(live), "planned": len(keys),
                "complete": complete, "accuracy": correct / len(live) if live else None,
                "at_least_95_percent_on_complete_bank": complete and correct * 100 >= 95 * len(keys)}

    out = {"kind": "stop-policy-learnability-subset-diagnostics.v1",
           "not_an_independent_replication": True, "observed_rows": len(rows), "planned_rows": len(expected),
           "overall": {"cold": count("english", real), "entry": count("ainglish", real)},
           "by_form": {}, "by_reader": {}, "by_family": {}}
    required = [out["overall"]["entry"]]
    for form in ("finish-started", "interrupt-started"):
        chosen = [ident for ident, item in real.items() if item["tested_form"] == form]
        critical = [ident for ident in chosen if real[ident]["form_changes_answer"]]
        out["by_form"][form] = {
            "cold": count("english", chosen), "entry": count("ainglish", chosen),
            "policy_changing_cold": count("english", critical),
            "policy_changing_entry": count("ainglish", critical),
        }
        required += [out["by_form"][form]["entry"], out["by_form"][form]["policy_changing_entry"]]
    for reader in readers:
        out["by_reader"][reader] = {"cold": count("english", real, [reader]), "entry": count("ainglish", real, [reader])}
    for family in sorted({item["family"] for item in real.values()}):
        chosen = [ident for ident, item in real.items() if item["family"] == family]
        out["by_family"][family] = {"cold": count("english", chosen), "entry": count("ainglish", chosen)}
    out["author_bank_readability_requirement_met"] = all(c["at_least_95_percent_on_complete_bank"] for c in required)
    out["boundary"] = (
        "Observed finite-bank accuracy on a fixed roster, not a population guarantee, "
        "careful-English comparison, independent confirmation, ratification or automatic readiness override. "
        "SDK learnability has no settlement_strata; these predeclared per-form/subset checks remain explicit."
    )

    # Paired-world resampling preserves both form variants of each incident. This
    # is a supplementary fixed-reader sensitivity interval, not the official SDK
    # item-bootstrap and not a new settlement result. Perfect empirical data can
    # yield [1,1]; that is NEVER proof of perfect population comprehension.
    if len(indexed) == len(expected) and all(r.get("answer") for r in rows):
        def interval(selected, label):
            world_values = defaultdict(list)
            for (ident, reader, arm), row in indexed.items():
                if arm == "ainglish" and ident in selected:
                    world_values[real[ident]["world_id"]].append(int(row["correct"] is True))
            world_ids = sorted(world_values)
            world_means = {key: sum(values) / len(values) for key, values in world_values.items()}
            rng = random.Random("stop-policy-world-bootstrap-20260919-v1:" + label)
            draws = sorted(sum(world_means[rng.choice(world_ids)] for _ in world_ids) / len(world_ids) for _ in range(2000))
            return {
                "unit": "world, retaining the selected form variants and fixed two-reader roster",
                "worlds": len(world_ids), "draws": 2000,
                "quantile_rule": "sorted zero-based floor((draws-1)*q), q=0.025,0.975",
                "lo": draws[int((len(draws) - 1) * .025)], "hi": draws[int((len(draws) - 1) * .975)],
                "not_population_or_settlement_interval": True,
            }
        out["paired_world_sensitivity"] = interval(set(real), "overall")
        for form, values in out["by_form"].items():
            chosen = {ident for ident, item in real.items() if item["tested_form"] == form}
            critical = {ident for ident in chosen if real[ident]["form_changes_answer"]}
            values["world_sensitivity"] = interval(chosen, form)
            values["policy_changing_world_sensitivity"] = interval(critical, form + ":critical")
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cell_rows_json", help="JSON array of retained SDK scientific rows")
    args = parser.parse_args()
    spec = json.loads((Path(__file__).parent / "learnability-preparation.json").read_text())
    rows = json.loads(Path(args.cell_rows_json).read_text())
    print(json.dumps(summarize(spec["items"], [ep["name"] for ep in spec["panel"]], rows), indent=2))
