#!/usr/bin/env python3
"""Read-only integrity audit of the complete public Ainglish measurement corpus."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import urllib.request

from ainglish.client import AinglishClient, manifest_commitment


ROOT = Path(__file__).resolve().parent
BASE = "https://ainglish.org"
USER_AGENT = "Dexagon-Ainglish-integrity-audit/1.0"
MAX_BODY = 12 * 1024 * 1024


def fetch_json(url: str) -> object:
    return json.loads(fetch_bytes(url))


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read(MAX_BODY + 1)
    if len(body) > MAX_BODY:
        raise ValueError(f"response exceeds {MAX_BODY} bytes")
    return body


def canonical_items_sha256(items: object) -> str:
    wire = json.dumps(
        items, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(wire).hexdigest()


def close(a: object, b: object, tolerance: float = 0.011) -> bool:
    try:
        return math.isclose(float(a), float(b), rel_tol=0, abs_tol=tolerance)
    except (TypeError, ValueError):
        return False


def pair_rows(manifest: dict) -> list[dict] | None:
    rows = manifest.get("test_set")
    if isinstance(rows, list):
        return rows
    rows = manifest.get("items")
    if isinstance(rows, list):
        return rows
    return None


def issue(severity: str, code: str, row: dict, detail: str) -> dict:
    return {
        "severity": severity,
        "code": code,
        "manifest_hash": row.get("manifest_hash"),
        "metric": row.get("metric"),
        "proposal": (row.get("proposal") or {}).get("public_id"),
        "proposal_slug": (row.get("proposal") or {}).get("slug"),
        "submitter": (row.get("submitter") or {}).get("name"),
        "evidence_state": row.get("evidence_state"),
        "detail": detail,
    }


def audit_one(summary: dict) -> tuple[dict | None, list[dict]]:
    manifest_hash = summary["manifest_hash"]
    problems: list[dict] = []
    try:
        row = fetch_json(f"{BASE}/api/v1/measurements/{manifest_hash}")
    except Exception as exc:
        return None, [issue("definite", "measurement_dereference_failed", summary, repr(exc))]
    if not isinstance(row, dict):
        return None, [issue("definite", "measurement_not_object", summary, type(row).__name__)]
    manifest = row.get("manifest")
    if not isinstance(manifest, dict):
        problems.append(issue("definite", "manifest_missing", row, "detail has no manifest object"))
        return row, problems

    attempt = row.get("attempt") or {}
    try:
        computed = manifest_commitment(manifest)
    except ValueError as exc:
        # Some historical manifests contain decimals the current cross-runtime commitment helper
        # now refuses.  Inability to recompute under the *new* portability rule is not evidence
        # that their stored commitment was wrong under the rule in force when filed.
        problems.append(issue(
            "audit_gap", "legacy_manifest_not_portable_to_current_hasher", row, str(exc),
        ))
    else:
        if computed != manifest_hash and attempt.get("manifest_storage") == "commitment_only":
            problems.append(issue(
                "audit_gap", "legacy_commitment_only_bytes_unrecoverable", row,
                f"current served view hashes to {computed}; original committed bytes were not stored",
            ))
        elif computed != manifest_hash:
            problems.append(issue(
                "definite", "manifest_commitment_mismatch", row,
                f"served manifest hashes to {computed}",
            ))
    pin = attempt.get("pin") or {}
    if pin.get("manifest_commitment") not in (None, manifest_hash):
        problems.append(issue(
            "definite", "attempt_pin_mismatch", row,
            f"attempt pins {pin.get('manifest_commitment')}",
        ))
    stored = attempt.get("manifest") or {}
    if stored.get("sha256") not in (None, manifest_hash):
        problems.append(issue(
            "definite", "stored_manifest_mismatch", row,
            f"attempt storage reports {stored.get('sha256')}",
        ))
    if attempt.get("measurement_ref") not in (None, manifest_hash):
        problems.append(issue(
            "definite", "attempt_measurement_ref_mismatch", row,
            f"attempt closes as {attempt.get('measurement_ref')}",
        ))

    rows = pair_rows(manifest)
    if rows is not None:
        pairs = [
            (item.get("english"), item.get("ainglish"))
            for item in rows if isinstance(item, dict)
            and isinstance(item.get("english"), str)
            and isinstance(item.get("ainglish"), str)
        ]
        duplicates = len(pairs) - len(set(pairs))
        if duplicates:
            problems.append(issue(
                "review", "duplicate_complete_pairs", row,
                f"{duplicates} repeated complete pair(s) inside one manifest",
            ))

    comparison = manifest.get("comparison_identity")
    if row.get("metric") == "token_delta" and not isinstance(comparison, dict):
        problems.append(issue(
            "legacy_gap", "comparison_identity_absent", row,
            "descriptive provenance gap; not evidence invalidity",
        ))

    if row.get("metric") == "token_delta":
        members = row.get("per_member") or []
        values = [m.get("value") for m in members if isinstance(m, dict)]
        if values and all(isinstance(value, (int, float)) for value in values):
            least_favourable = max(values)
            method = str(manifest.get("method", "")).casefold()
            explicitly_max = any(term in method for term in (
                "maximum tokenizer", "max tokenizer", "least-favourable",
                "least favourable", "report the maximum", "maximum mean",
            ))
            if not close(row.get("value"), least_favourable):
                problems.append(issue(
                    "definite" if explicitly_max else "legacy_gap",
                    "token_headline_not_roster_max", row,
                    f"reported {row.get('value')}; per-member maximum {least_favourable}; "
                    f"explicit_max_contract={explicitly_max}",
                ))
            lo, hi = min(values), max(values)
            if (row.get("value_lo") is not None and row.get("value_hi") is not None
                    and (not close(row["value_lo"], lo) or not close(row["value_hi"], hi))):
                problems.append(issue(
                    "review", "token_member_span_mismatch", row,
                    f"reported [{row.get('value_lo')}, {row.get('value_hi')}], member span [{lo}, {hi}]",
                ))

    return row, problems


def audit_tiktoken(row: dict) -> list[dict]:
    if row.get("metric") != "token_delta" or row.get("evidence_state") != "valid":
        return []
    manifest = row.get("manifest") or {}
    rows = manifest.get("test_set")
    if not isinstance(rows, list) or not rows:
        return []
    if any(not isinstance(item, dict) or not isinstance(item.get("english"), str)
           or not isinstance(item.get("ainglish"), str) for item in rows):
        return []
    members = row.get("per_member") or []
    if not members:
        return []
    try:
        import tiktoken
    except ImportError:
        return [issue("audit_gap", "tiktoken_unavailable", row, "local recomputation skipped")]
    known = set(tiktoken.list_encoding_names())
    problems = []
    for member in members:
        model = member.get("model")
        if model not in known:
            continue
        encoding = tiktoken.get_encoding(model)
        deltas = [
            len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"]))
            for item in rows
        ]
        computed = sum(deltas) / len(deltas)
        if not close(member.get("value"), computed):
            problems.append(issue(
                "definite", "token_member_recompute_mismatch", row,
                f"{model}: reported {member.get('value')}, recomputed {computed:.8f} over {len(rows)} pairs",
            ))
    return problems


def source_url(manifest: dict) -> str | None:
    source = manifest.get("source") or {}
    if isinstance(source.get("url"), str):
        return source["url"]
    if all(isinstance(source.get(key), str) for key in ("repository", "commit", "path")):
        return (
            f"https://raw.githubusercontent.com/{source['repository']}/{source['commit']}/"
            f"{source['path']}"
        )
    return None


def external_digest_candidates(
    url: str, cache: dict[str, tuple[set[str] | None, str | None]]
) -> tuple[set[str] | None, str | None]:
    if url not in cache:
        try:
            body = fetch_bytes(url)
            document = json.loads(body)
            items = document.get("items") if isinstance(document, dict) else document
            candidates = {hashlib.sha256(body).hexdigest(), canonical_items_sha256(items)}
            if isinstance(document, dict) and isinstance(document.get("sha256"), str):
                candidates.add(document["sha256"])
            if isinstance(items, list):
                projected = [
                    {key: item[key] for key in ("id", "force", "english", "ainglish")}
                    for item in items if isinstance(item, dict) and not item.get("calibration")
                    and all(key in item for key in ("id", "force", "english", "ainglish"))
                ]
                if projected:
                    candidates.add(canonical_items_sha256(projected))
            cache[url] = (candidates, None)
        except Exception as exc:
            cache[url] = (None, repr(exc))
    return cache[url]


def external_item_audit(
    row: dict, cache: dict[str, tuple[set[str] | None, str | None]]
) -> list[dict]:
    manifest = row.get("manifest") or {}
    pinned = manifest.get("items_sha256")
    if not isinstance(pinned, str):
        return []
    urls = []
    if isinstance(manifest.get("items_url"), str):
        urls.append(manifest["items_url"])
    declared_source_url = source_url(manifest)
    if declared_source_url and declared_source_url not in urls:
        urls.append(declared_source_url)
    candidates = {canonical_items_sha256(pair_rows(manifest))} if pair_rows(manifest) is not None else set()
    errors = []
    for url in urls:
        found, error = external_digest_candidates(url, cache)
        if found:
            candidates.update(found)
        elif error:
            errors.append(f"{url}: {error}")
    if pinned in candidates:
        return []
    source = manifest.get("source") or {}
    # Some legacy manifests name a raw-source digest without retaining a dereferenceable URL.
    # The declaration is a provenance limitation, not enough to allege contradictory bytes.
    if source.get("sha256") == pinned and not urls:
        return [issue(
            "audit_gap", "declared_source_digest_not_dereferenceable", row,
            "source.sha256 matches items_sha256 but no immutable URL can be reconstructed",
        )]
    if errors and not candidates:
        return [issue("review", "external_items_dereference_failed", row, "; ".join(errors))]
    if urls:
        return [issue(
            "review", "items_digest_convention_unresolved", row,
            f"declared {pinned}; no raw, canonical-list, embedded, or declared projection digest matched",
        )]
    return []


def main() -> None:
    client = AinglishClient(use_env=False)
    summaries = list(client.iter_measurements(page_size=200))
    details: list[dict] = []
    problems: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        future_map = {pool.submit(audit_one, row): row["manifest_hash"] for row in summaries}
        for future in as_completed(future_map):
            row, found = future.result()
            problems.extend(found)
            if row is not None:
                details.append(row)

    hashes = {row["manifest_hash"] for row in details}
    for row in details:
        target = row.get("replicates_hash")
        if target and target not in hashes:
            problems.append(issue(
                "definite", "replication_target_missing", row,
                f"replicates_hash {target} is absent from the served corpus",
            ))
        problems.extend(audit_tiktoken(row))
    item_cache: dict[str, tuple[set[str] | None, str | None]] = {}
    for row in details:
        problems.extend(external_item_audit(row, item_cache))

    problems.sort(key=lambda item: (
        {"definite": 0, "review": 1, "legacy_gap": 2, "audit_gap": 3}.get(item["severity"], 9),
        item["code"], item.get("manifest_hash") or "",
    ))
    status_counts = Counter(row.get("evidence_state") or "unknown" for row in details)
    metric_counts = Counter(row.get("metric") or "unknown" for row in details)
    code_counts = Counter((item["severity"], item["code"]) for item in problems)
    report = {
        "kind": "dexagon.ainglish.measurement-integrity-audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "complete public /api/v1/measurements corpus at generated_at",
        "measurement_count_index": len(summaries),
        "measurement_count_dereferenced": len(details),
        "metric_counts": dict(sorted(metric_counts.items())),
        "evidence_state_counts": dict(sorted(status_counts.items())),
        "external_item_urls_checked": len(item_cache),
        "checks": [
            "served manifest commitment and attempt pins",
            "replication target referential integrity",
            "inline and externally served item-set digests",
            "within-manifest duplicate complete pairs",
            "token roster maximum and member span",
            "local tiktoken recomputation for recognized inline token carriers",
            "comparison-identity presence (legacy gap only)",
        ],
        "policy": "Only definite contradictions are candidates for moderation. Missing modern provenance on legacy evidence is never treated as invalidity by itself.",
        "issue_counts": [
            {"severity": severity, "code": code, "count": count}
            for (severity, code), count in sorted(code_counts.items())
        ],
        "issues": problems,
    }
    (ROOT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "measurement_count_index", "measurement_count_dereferenced", "metric_counts",
        "evidence_state_counts", "external_item_urls_checked", "issue_counts",
    )}, indent=2))


if __name__ == "__main__":
    main()
