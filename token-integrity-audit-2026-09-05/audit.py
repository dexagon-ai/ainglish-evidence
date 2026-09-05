"""Read-only reproduction of filed token results. Never submits a measurement.

No model or tokenizer downloads: the three reference encodings must be cached.
Public reports contain only public evidence, never private moderation payloads.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
from unittest.mock import patch

from ainglish.client import AinglishClient, manifest_commitment
from ainglish.measure import token_delta


SUPPORTED = {"cl100k_base", "o200k_base", "p50k_base"}


def pairs_from(manifest):
    carrier = manifest.get("test_set", manifest.get("pairs"))
    legacy = manifest.get("pairs")
    if isinstance(carrier, str) and isinstance(legacy, list):
        carrier = legacy
    if isinstance(carrier, dict):
        carrier = carrier.get("pairs")
    if not isinstance(carrier, list) or not carrier:
        raise ValueError("no supported inline complete-pair carrier")
    pairs = []
    for item in carrier:
        if isinstance(item, dict):
            pair = [item.get("english", item.get("baseline")), item.get("ainglish")]
        else:
            pair = item
        if not isinstance(pair, (list, tuple)) or len(pair) != 2 or not all(
            isinstance(text, str) for text in pair
        ):
            raise ValueError("invalid complete pair")
        pairs.append(list(pair))
    if isinstance(legacy, list) and isinstance(manifest.get("test_set"), list):
        other = pairs_from({"test_set": legacy})
        if sorted(pairs) != sorted(other):
            raise ValueError("contradictory complete pair carriers")
    return pairs


def reproduce(client, measurement_hash, indexed_row=None, cache=None):
    row = client.measurement(measurement_hash) if indexed_row is None else dict(indexed_row)
    if indexed_row is None:
        manifest = row["manifest"]
    else:
        # Hashes identify manifests, not unique submission rows. Preserve the cursor row's
        # author, result and attempt even when an original and build check share a hash.
        attempt_id = row.get("attempt_id")
        if not attempt_id:
            raise ValueError("indexed row has no exact attempt identity")
        attempt = client.attempt(attempt_id)
        try:
            manifest = client.attempt_manifest(attempt_id)
        except Exception as exc:
            if getattr(exc, "status", None) != 404:
                raise
            artifact = client.measurement(measurement_hash)
            manifest = artifact["manifest"]
        row["proposal"] = {"slug": attempt["proposal"]}
        row["attempt"] = attempt
    if cache is not None:
        cache.mkdir(exist_ok=True, parents=True)
        (cache / (row.get("attempt_id") or measurement_hash)).with_suffix(".json").write_text(
            json.dumps({"row": row, "manifest": manifest}, indent=2, ensure_ascii=False) + "\n")
    result = {
        "manifest_hash": row["manifest_hash"], "attempt_id": row.get("attempt_id"),
        "proposal": row.get("proposal"), "submitter": row.get("submitter"),
        "filed_value": row["value"], "filed_per_member": row.get("per_member"),
        "evidence_state": row.get("evidence_state"), "retraction": row.get("retraction"),
        "is_replication": row.get("is_replication"),
        "replicates_hash": row.get("replicates_hash"),
        "counts_toward_verdict": row.get("counts_toward_verdict"),
        "backfilled": (row.get("attempt") or {}).get("backfilled"),
        "runtime": {"ainglish": version("ainglish"), "tiktoken": version("tiktoken")},
    }
    try:
        result["committed_manifest_recomputed"] = manifest_commitment(manifest)
    except ValueError as exc:
        result.update(status="not_reproduced", reason="historical canonicalization not verified: " + str(exc))
        return result
    if result["committed_manifest_recomputed"] != row["manifest_hash"]:
        result.update(status="not_reproduced", reason="exact commitment not verified; a served legacy projection is not necessarily the stored manifest")
        return result
    models = manifest.get("models")
    if not isinstance(models, list) or not models or not all(
        isinstance(name, str) and name in SUPPORTED for name in models
    ) or len(set(models)) != len(models):
        result.update(status="not_reproduced", reason="unsupported or ambiguous tokenizer roster")
        return result
    provenance = manifest.get("tokenizer_provenance") or manifest.get("environment") or {}
    declared_version = (provenance.get("library_version") or provenance.get("version")) if isinstance(provenance, dict) else None
    result["declared_tokenizer_version"] = declared_version
    try:
        pairs = pairs_from(manifest)
        with patch("tiktoken.load.read_file", side_effect=RuntimeError("uncached tokenizer: downloads disabled")):
            derived = token_delta(pairs, models)
    except (ValueError, RuntimeError) as exc:
        result.update(status="not_reproduced", reason=str(exc))
        return result
    result["pair_count"] = len(pairs)
    strata = manifest.get("settlement_strata")
    if strata:
        if not isinstance(strata, list) or not strata or len({x.get("id") for x in strata}) != len(strata):
            result.update(status="not_reproduced", reason="unsupported or duplicate strata")
            return result
        carrier = manifest.get("test_set", manifest.get("pairs"))
        if isinstance(carrier, dict):
            carrier = carrier.get("pairs")
        if not all(isinstance(x, dict) and x.get("stratum") in {s["id"] for s in strata} for x in carrier):
            result.update(status="not_reproduced", reason="missing or unknown stratum assignment")
            return result
        weights = {s["id"]: Fraction(str(s["weight"])) for s in strata}
        if any(w <= 0 for w in weights.values()):
            raise ValueError("stratum weights must be positive")
        total = sum(weights.values())
        for name, member in derived["by_tokenizer"].items():
            cells = {}
            for ident in weights:
                values = [v for x, v in zip(carrier, member["per_pair"]) if x["stratum"] == ident]
                if not values:
                    raise ValueError("empty declared stratum")
                cells[ident] = Fraction(sum(values), len(values))
            member["strata_exact"] = {k: str(v) for k, v in cells.items()}
            member["mean_exact"] = str(sum(weights[k] * v / total for k, v in cells.items()))
            # Replay the SDK's actual IEEE-754 sum and tie break, while retaining exact rational
            # means separately. Two mathematically tied members can round a last bit apart.
            member["mean"] = sum(float(weights[k] / total) * float(v) for k, v in cells.items())
        name = max(models, key=lambda name: derived["by_tokenizer"][name]["mean"])
        derived.update(floor=derived["by_tokenizer"][name]["mean"], floor_tokenizer=name)
    result["derived"] = derived
    result["exact_means"] = {
        name: member.get("mean_exact", str(Fraction(sum(member["per_pair"]), len(pairs))))
        for name, member in derived["by_tokenizer"].items()
    }
    result["headline_difference"] = row["value"] - derived["floor"]
    # Historical non-dyadic rows may round to four decimals. This is a conservative audit
    # tolerance, not the register's replication tolerance and never an admission decision.
    result["audit_rounding_tolerance"] = 0.00005
    result["member_values_declared"] = len(row.get("per_member") or [])
    result["bounds_verified"] = False
    result["headline_matches"] = math.isclose(row["value"], derived["floor"], rel_tol=0, abs_tol=0.00005)
    result["member_mismatches"] = []
    for member in row.get("per_member") or []:
        if member.get("model") not in derived["by_tokenizer"]:
            result["member_mismatches"].append({"model": member.get("model"), "reason": "outside declared roster"})
        elif not math.isclose(member["value"], derived["by_tokenizer"][member["model"]]["mean"], rel_tol=0, abs_tol=0.00005):
            result["member_mismatches"].append({"model": member["model"], "filed": member["value"], "derived": derived["by_tokenizer"][member["model"]]["mean"]})
    result["stratum_mismatches"] = []
    if strata and row.get("stratum_results"):
        expected = derived["by_tokenizer"][derived["floor_tokenizer"]]["strata_exact"]
        for cell in row["stratum_results"]:
            if cell.get("id") not in expected or not math.isclose(cell["value"], float(Fraction(expected[cell["id"]])), rel_tol=0, abs_tol=0.00005):
                result["stratum_mismatches"].append(cell)
    result["status"] = "matches" if result["headline_matches"] and not result["member_mismatches"] and not result["stratum_mismatches"] else "mismatch"
    if result["status"] == "mismatch" and not result["stratum_mismatches"]:
        # The older reference harness printed three decimals. Label that separately instead of
        # treating it as misconduct or extending the arithmetic tolerance for modern filings.
        deltas = [abs(result["headline_difference"])] + [abs(x["filed"]-x["derived"])
                  for x in result["member_mismatches"] if "filed" in x]
        if max(deltas) <= 0.000500000001 and all("filed" in x for x in result["member_mismatches"]):
            result["status"] = "coarse_rounding_only"
    result["claim_boundary"] = "Same-input arithmetic reproduction only; not independent settlement, semantic adequacy, or a language verdict."
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hashes", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output", required=True)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    client = AinglishClient(use_env=False)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    hashes = args.hashes
    indexed = {}
    sweep = []
    if args.all:
        hashes = []
        for page in client.measurement_pages(metric="token_delta"):
            sweep.append({k: page[k] for k in ["sweep", "total", "count", "has_more", "next"]})
            for row in page["measurements"]:
                key = row.get("attempt_id")
                if not key or key in indexed:
                    raise ValueError("missing or duplicate exact row identity in sweep")
                indexed[key] = row
                hashes.append(key)
    results = []
    for target in hashes:
        try:
            source = indexed.get(target)
            result = reproduce(client, source["manifest_hash"] if source else target, source, args.cache)
        except Exception as exc:
            source = indexed.get(target) or {}
            result = {"manifest_hash": source.get("manifest_hash", target), "attempt_id": source.get("attempt_id"),
                      "submitter": source.get("submitter"), "status": "not_reproduced", "reason": type(exc).__name__ + ": " + str(exc)[:300]}
        results.append(result)
        encoded = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode()
        (output / (target + ".json")).write_bytes(encoded)
        print(json.dumps({k: result.get(k) for k in ["manifest_hash", "status", "filed_value", "pair_count", "headline_difference", "reason"]}), flush=True)
    report = {"kind": "ainglish.token-integrity-audit.v1", "at": datetime.now(timezone.utc).isoformat(), "sweep": sweep, "count": len(results), "results": results}
    (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
