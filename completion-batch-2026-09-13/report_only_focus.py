"""Audit retained first-pass cells; no reader calls and no governance writes."""
from collections import defaultdict
import json
from pathlib import Path
import random
from statistics import mean

HERE = Path(__file__).resolve().parent
SITES = ("subject", "verb", "nominal", "adjunct")
AXES = ("intended", "orthogonal")


def accuracies(rows):
    result = {}
    for site in SITES:
        for axis in AXES:
            subset = [r for r in rows if r["strata"]["focus_site"] == site and r["strata"]["probe_axis"] == axis]
            arms = {}
            for arm in ("english", "ainglish"):
                values = [r["correct"] for r in subset if r["arm"] == arm]
                assert values, (site, axis, arm)
                arms[arm] = {"correct": sum(values), "total": len(values), "accuracy": mean(values)}
            result[site + "-" + axis] = {"arms": arms, "delta_pp": 100 * (arms["ainglish"]["accuracy"] - arms["english"]["accuracy"])}
    return result


def quantile(values, q):
    values = sorted(values)
    x = (len(values) - 1) * q
    lower = int(x)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (x - lower) * (values[upper] - values[lower])


def main():
    summaries = []
    for contrast in ("careful", "placement", "bare"):
        name = "only-focus-" + contrast
        spec = json.loads((HERE / (name + "-runspec.json")).read_text())
        mint = json.loads((HERE / (name + "-mint.json")).read_text())
        attempt = mint["opened"]["attempt"]["attempt_id"]
        result = json.loads((HERE / (name + "-result.json")).read_text())
        cells = json.loads((HERE / f"{name}.attempt-{attempt}.cells.json").read_text())
        assert cells["kind"] == "ainglish.panel.cell-results.v1", cells["kind"]
        rows = cells["rows"]
        assert len(rows) == 384 and all(type(r["correct"]) is bool for r in rows)
        by_id = {i["id"]: i for i in spec["items"] if not i.get("calibration")}
        assert len(by_id) == 192
        assert len({(r["reader"], r["item_id"]) for r in rows}) == 384
        for r in rows:
            item = by_id[r["item_id"]]
            assert r["expected"] == item["answer"]
            assert r["correct"] == (r["answer"] == item["answer"])
        table = accuracies(rows)
        headline = mean(r["delta_pp"] for r in table.values())
        # The official harness rounds each arm to four decimals before its
        # stratum delta, then rounds the equal-weight headline. Verify those
        # retained rounded arms against integer counts; keep our unrounded
        # descriptive replay separate rather than changing the official result.
        for published in result["stratum_results"]:
            counted = table[published["id"]]
            for arm in ("english", "ainglish"):
                assert abs(counted["arms"][arm]["accuracy"] - published["arms"][arm]) <= .00005000001
            assert abs(published["value"] - 100 * (published["arms"]["ainglish"] - published["arms"]["english"])) < .00011
        assert abs(mean(r["value"] for r in result["stratum_results"]) - result["value"]) <= .00005000001
        per_reader = {reader: accuracies([r for r in rows if r["reader"] == reader])
                      for reader in sorted({r["reader"] for r in rows})}
        worlds = defaultdict(list)
        for r in rows:
            worlds[r["strata"]["world_id"]].append(r)
        assert len(worlds) == 96 and all(len(v) == 4 for v in worlds.values())
        site_worlds = {site: sorted(k for k, v in worlds.items() if v[0]["strata"]["focus_site"] == site) for site in SITES}
        rng = random.Random(spec["seed"])
        draws = defaultdict(list)
        for _ in range(2000):
            sampled = [r for site in SITES for w in rng.choices(site_worlds[site], k=24) for r in worlds[w]]
            estimates = accuracies(sampled)
            draws["overall"].append(mean(v["delta_pp"] for v in estimates.values()))
            for key, row in estimates.items():
                draws[key].append(row["delta_pp"])
        intervals = {key: [quantile(values, .025), quantile(values, .975)] for key, values in draws.items()}
        summaries.append({
            "contrast": contrast, "attempt_id": attempt, "manifest_hash": mint["descriptor"]["manifest_commitment"],
            "official_value_pp": result["value"], "official_interval_pp": [result["value_lo"], result["value_hi"]],
            "official_arms": result["arms"], "unrounded_replay_value_pp": headline,
            "rounding": "Official arms round to four decimals before each stratum delta and the final weighted value; integer cell counts validate them.",
            "per_site_axis": table, "per_reader_site_axis": per_reader,
            "world_cluster_sensitivity": {"draws": 2000, "seed": spec["seed"], "unit": "world, stratified by focus site",
                "intervals_pp": intervals, "effect": "descriptive sensitivity only; does not replace the filed official result"},
            "baselines": {"constant_unknown_overall": .5, "constant_unknown_orthogonal": 1,
                          "uniform_random_three_options": 1 / 3},
            "scope": spec["study_scope"],
        })
    with (HERE / "only-focus-cell-audit.json").open("x") as stream:
        json.dump({"status": "all_1152_target_cells_replayed", "contrasts": summaries}, stream, indent=2, allow_nan=False)
        stream.write("\n")
    for s in summaries:
        print(s["contrast"], s["official_value_pp"], s["official_interval_pp"],
              "cluster sensitivity", s["world_cluster_sensitivity"]["intervals_pp"]["overall"])


if __name__ == "__main__":
    main()
