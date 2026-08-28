#!/usr/bin/env python3
"""Read-only cross-surface acceptance for the deployed flagship evidence map."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent
AXES = ["editorial", "lifecycle", "contract", "settlement", "qualification", "adoption"]
PLUGIN_PATHS = {
    "openai": Path("/home/dexagon/plugins/ainglish-openai-plugin/skills/ainglish-participate/main.py"),
    "claude": Path("/home/dexagon/plugins/worktrees/claude-sdk-0.2.43-conformance-20260829/skills/ainglish-participate/main.py"),
}
EXCLUSIONS = {"amend", "create_webhook", "delete_webhook", "get", "post", "webhooks"}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def request(base: str, path: str, payload: dict | None = None) -> tuple[bytes, dict[str, str]]:
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=body,
        headers={
            "Accept": "application/json, text/event-stream, text/html;q=0.9",
            "Content-Type": "application/json",
            "User-Agent": "ainglish-evidence-map-conformance-v1",
        },
        method="GET" if payload is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read(), {key.lower(): value for key, value in response.headers.items()}


def json_request(base: str, path: str, payload: dict | None = None) -> tuple[dict, dict[str, str]]:
    raw, headers = request(base, path, payload)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} did not return an object")
    return value, headers


def plugin_actions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(
        row for row in tree.body
        if isinstance(row, ast.AnnAssign) and getattr(row.target, "id", None) == "ALLOWED_ACTIONS"
    )
    expression = node.value.args[0] if isinstance(node.value, ast.Call) else node.value
    return set(ast.literal_eval(expression))


def check_map(payload: dict, catalog: dict) -> list[str]:
    checks = []
    if payload.get("kind") != "ainglish.flagship-evidence-map.v1":
        raise RuntimeError("unexpected evidence-map kind")
    if [row.get("key") for row in payload.get("axes") or []] != AXES:
        raise RuntimeError("axis contract drift")
    count = payload.get("entry_count")
    entries = payload.get("entries") or []
    if not isinstance(count, int) or count <= 0 or len(entries) != count:
        raise RuntimeError("entry population is empty or inconsistent")
    if payload.get("source_catalog_sha256") != catalog.get("content_sha256"):
        raise RuntimeError("evidence map is not bound to the served catalogue digest")
    for row in entries:
        states = row.get("states") or {}
        if list(states) != AXES or len(row.get("path") or []) != len(AXES):
            raise RuntimeError(f"six-axis entry contract drift for {row.get('pinned_slug')}")
        if row["path"] != [f"{axis}:{states[axis]}" for axis in AXES]:
            raise RuntimeError(f"entry path/state mismatch for {row.get('pinned_slug')}")
        if {"score", "rank", "readiness_score", "composite"} & set(row):
            raise RuntimeError(f"composite field leaked into {row.get('pinned_slug')}")
    node_totals = {axis: 0 for axis in AXES}
    for node in payload.get("nodes") or []:
        node_totals[node["axis"]] += node["entry_count"]
    if node_totals != {axis: count for axis in AXES}:
        raise RuntimeError("node population is not conserved on every axis")
    if sum(row["entry_count"] for row in payload.get("edges") or []) != count * (len(AXES) - 1):
        raise RuntimeError("edge population is not conserved")
    interpretation = payload.get("interpretation") or {}
    if "No points, ranking, ladder" not in interpretation.get("no_composite", ""):
        raise RuntimeError("no-composite claim boundary is missing")
    for key in ("source_catalog_sha256", "content_sha256"):
        if re.fullmatch(r"[0-9a-f]{64}", str(payload.get(key))) is None:
            raise RuntimeError(f"{key} is not a SHA-256 digest")
    checks.extend(["kind", "axes", "population", "catalog_digest", "entry_paths", "nodes", "edges", "no_composite", "digests"])
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="https://ainglish.org")
    args = parser.parse_args()
    target = ROOT / "receipt.json"
    if target.exists():
        raise SystemExit("REFUSING: receipt.json already exists")

    catalog, _ = json_request(args.base, "/api/v1/flagships")
    evidence_map, map_headers = json_request(args.base, "/api/v1/flagships/evidence-map")
    checks = check_map(evidence_map, catalog)

    html_raw, _ = request(args.base, "/flagships/evidence-map")
    html = html_raw.decode("utf-8")
    if html.count('class="flagship-map-row"') != evidence_map["entry_count"]:
        raise RuntimeError("HTML row population differs from the API")
    for text in ("Six receipts. No blended score.", "This is a receipt matrix, not a progression chart."):
        if text not in html:
            raise RuntimeError(f"HTML claim boundary is missing: {text}")
    checks.append("html")

    openapi, _ = json_request(args.base, "/openapi.json")
    if "/api/v1/flagships/evidence-map" not in (openapi.get("paths") or {}):
        raise RuntimeError("OpenAPI does not declare the evidence-map route")
    checks.append("openapi")

    listed, _ = json_request(args.base, "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tool_names = {row.get("name") for row in ((listed.get("result") or {}).get("tools") or [])}
    if "get_flagship_evidence_map" not in tool_names:
        raise RuntimeError("MCP discovery omits get_flagship_evidence_map")
    called, _ = json_request(args.base, "/mcp", {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "get_flagship_evidence_map", "arguments": {}},
    })
    content = ((called.get("result") or {}).get("content") or [])
    mcp_map = json.loads(content[0]["text"]) if content else None
    if mcp_map != evidence_map:
        raise RuntimeError("MCP and REST evidence-map payloads differ")
    checks.append("mcp")

    from ainglish.client import AinglishClient

    sdk_map = AinglishClient(base_url=args.base).flagship_evidence_map()
    if sdk_map != evidence_map:
        raise RuntimeError("SDK and REST evidence-map payloads differ")
    sdk_version = version("ainglish")
    if tuple(int(part) for part in sdk_version.split(".")[:3]) < (0, 2, 43):
        raise RuntimeError(f"SDK version {sdk_version} is below 0.2.43")
    checks.append("sdk")

    surfaces = {name: plugin_actions(path) for name, path in PLUGIN_PATHS.items()}
    if surfaces["openai"] != surfaces["claude"] or len(surfaces["openai"]) != 48:
        raise RuntimeError("plugin action surfaces differ or are not the reviewed 48-action set")
    if "flagship_evidence_map" not in surfaces["openai"] or surfaces["openai"] & EXCLUSIONS:
        raise RuntimeError("plugin allowlist inclusion/exclusion contract failed")
    checks.append("plugins")

    receipt = {
        "kind": "dexagon.ainglish.flagship-evidence-map-deploy-conformance.v1",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base,
        "checks": checks,
        "entry_count": evidence_map["entry_count"],
        "axes": AXES,
        "catalog_sha256": catalog["content_sha256"],
        "evidence_map_sha256": evidence_map["content_sha256"],
        "rest_etag": map_headers.get("etag"),
        "mcp_tool": "get_flagship_evidence_map",
        "sdk_version": sdk_version,
        "plugin_actions": len(surfaces["openai"]),
        "governance_writes": 0,
        "claim_boundary": "Deployment and contract acceptance only; not governance or human-comprehension evidence.",
    }
    receipt["content_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    target.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as error:
        raise SystemExit(f"HTTP {error.code} for {error.url}") from error
