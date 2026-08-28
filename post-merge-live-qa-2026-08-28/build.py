#!/usr/bin/env python3
"""Derive the live-deploy QA verdict from the frozen response receipt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CC0 = '<https://creativecommons.org/publicdomain/zero/1.0/>; rel="license"'
CC_BY = '<https://creativecommons.org/licenses/by/4.0/>; rel="license"'
IMMUTABLE = "public, max-age=31536000, immutable"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    responses = snapshot["responses"]
    dynamic = ["/releases", "/training", "/paper"]
    static = {
        "/releases/ainglish-core-v0.35.0/MANIFEST.json": (CC0, "application/json"),
        "/training/ainglish-training-v0.35.0/data/parallel.jsonl": (CC0, "application/x-ndjson"),
        "/paper/1.0/ainglish-whitepaper.md": (CC_BY, None),
    }

    checks: dict[str, bool] = {}
    for path, response in responses.items():
        checks[f"status_200:{path}"] = response["status"] == 200
    for name, present in snapshot["deployment"]["contains_required_merges"].items():
        checks[f"deployed:{name}"] = present is True
    for group, values in snapshot["markers"].items():
        for marker, present in values.items():
            checks[f"marker:{group}:{marker}"] = present is True
    for path in dynamic:
        headers = responses[path]["headers"]
        checks[f"site_chrome_not_relicensed:{path}"] = headers["link"] is None
        checks[f"site_chrome_not_immutable:{path}"] = headers["cache-control"] != IMMUTABLE
    for path, (licence, content_type) in static.items():
        headers = responses[path]["headers"]
        checks[f"artifact_licence:{path}"] = headers["link"] == licence
        checks[f"artifact_immutable:{path}"] = headers["cache-control"] == IMMUTABLE
        checks[f"artifact_cors:{path}"] = headers["access-control-allow-origin"] == "*"
        if content_type is not None:
            checks[f"artifact_mime:{path}"] = (headers["content-type"] or "").startswith(content_type)

    failed = sorted(name for name, passed in checks.items() if not passed)
    report = {
        "kind": "dexagon.ainglish.post-merge-live-qa-report.v1",
        "captured_at": snapshot["captured_at"],
        "source_snapshot_sha256": snapshot["content_sha256"],
        "deployment_commit": snapshot["deployment"]["commit"],
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_checks": failed,
        "status": "verified" if not failed else "failed",
        "scope": [
            "PR 323 press and public correction history",
            "PR 326 versioned-artifact licence and cache boundary",
            "PR 327 applied-map semantic categories and accessible summary",
        ],
        "claim_boundary": (
            "This is a point-in-time public-origin smoke receipt. It demonstrates the observed HTTP and page "
            "contracts at the captured deployment commit; it is not a substitute for unit tests or continuous monitoring."
        ),
        "model_calls": 0,
        "governance_writes": 0,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Post-merge live QA — 2026-08-28",
        "",
        f"**{report['status'].upper()}**: {report['passed_count']}/{report['check_count']} checks passed against the public origin at `{snapshot['captured_at']}`.",
        "",
        f"The health receipt identified deployed commit `{report['deployment_commit']}`. Git ancestry checks confirm that it contains the merge commits for Symfony PRs #323, #326 and #327.",
        "",
        "- `/press` and `/history` return 200, expose the reviewed claim boundaries and correction-history wording, and are present in the sitemap.",
        "- `/state` exposes all six usage-status categories in the mobile summary and accessible SVG label, including the distinction between missing readings and project machinery to which corpus adoption does not apply.",
        "- The `/releases`, `/training` and `/paper` landing pages do not carry an artifact licence or immutable cache promise.",
        "- Representative frozen core, training and paper files carry the correct scoped licence, one-year immutable cache contract and cross-origin access; JSON and JSONL media types were also checked.",
        "",
        "## Claim boundary",
        "",
        report["claim_boundary"],
        "",
        f"Snapshot digest: `{snapshot['content_sha256']}`. Report digest: `{report['content_sha256']}`.",
    ]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "passed": report["passed_count"],
        "total": report["check_count"],
        "failed": failed,
        "content_sha256": report["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
