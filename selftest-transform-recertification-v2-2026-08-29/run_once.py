#!/usr/bin/env python3
"""Mint, run once, and file a current selftest transform recertification."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

import ainglish
from ainglish import measure as reference_measure
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "selftest-per-transform-known-answer-anchors-every-registry-t"
TARGET_HASH = "0dd00d64cd6d5cce5404b69f29765b777ee4c80a14a3d9e07a483971a39ef308"
SDK_VERSION = "0.2.43"
MEASURE_SHA256 = "8790aef7b7fa282249fe9503b59468b2b8929f35e8e1243718191a2b4b9c152f"
MODEL = f"ainglish-sdk-{SDK_VERSION}/measure.py-selftest@python{sys.version_info.major}.{sys.version_info.minor}"
RECEIPT = ROOT / "receipt.json"
RESULT_SOURCE = ROOT / "result-source.json"


# All nine pairs differ from the embedded anchors in v0.2.43. Isolation is not assumed: the
# evidence requires a finding whose `transform` field names the intended executable member.
FRESH_ANCHORS = [
    {"transform": "lower()", "slot": {"REQ": "directive", "req": "plain label"}, "collapsed": "req"},
    {"transform": "upper()", "slot": {"go": "directive", "GO": "state name"}, "collapsed": "GO"},
    {"transform": "casefold()", "slot": {"Σ": "capital sigma", "ς": "final sigma"}, "collapsed": "σ"},
    {"transform": "strip_punct()", "slot": {"x+y": "inclusive", "x-y": "exclusive"}, "collapsed": "xy"},
    {"transform": "collapse_ws()", "slot": {"red\tteam": "tabbed", "red team": "spaced"}, "collapsed": "red team"},
    {"transform": "nfkd()", "slot": {"Å": "precomposed", "Å": "decomposed"}, "collapsed": "Å"},
    {"transform": "alnum_only()", "slot": {"x.y": "dotted", "xy": "bare"}, "collapsed": "xy"},
    {"transform": "paren_drop()", "slot": {"may(permission)": "allowed", "may(possibility)": "possible"}, "collapsed": "may"},
    {"transform": "hyphen_drop()", "slot": {"whole-part": "hyphenated", "whole part": "spaced"}, "collapsed": "whole part"},
]


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def module_source_root() -> Path:
    package_file = Path(inspect.getfile(ainglish)).resolve()
    return package_file.parent.parent


def build_manifest() -> dict:
    return {
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "construct": "measure.py per-transform selftest anchors",
        "models": [MODEL],
        "test_set": [
            {"case": "untouched-before", "expected": "selftest passes"},
            *FRESH_ANCHORS,
            {"case": "untouched-after", "expected": "selftest passes after all fresh-process mutations"},
        ],
        "seed": "none - deterministic exhaustive registry mutation",
        "estimand": {
            "population": "every member of the executable PAIRWISE_TRANSFORMS registry in the pinned harness",
            "value": (
                "count of registry members for which a new target-named anchor is absent, identity mutation "
                "does not remove that target-named finding, or selftest does not fail naming the mutated member"
            ),
            "support": "0 supports; one or more opposes and triggers the registered refuted-if path",
        },
        "method": (
            "Run untouched selftest in a fresh process. For each frozen row, verify transform_screen "
            "emits the intended target-named collapse; in a new process replace only that "
            "PAIRWISE_TRANSFORMS member with identity, verify the target-named fresh finding disappears, "
            "then call selftest and require a nonzero exit whose assertion text names the member. "
            "Run untouched selftest again in a fresh process."
        ),
        "analysis_plan": (
            "File the exact nonconforming-member count once regardless of direction. Abort instead of "
            "filing if an untouched control fails, source bytes drift, a subprocess times out, or the table is incomplete."
        ),
        "source_harness": {
            "sdk_version": SDK_VERSION,
            "measure_py_sha256": MEASURE_SHA256,
            "served_url": "https://ainglish.org/measure.py",
            "registry": [row["transform"] for row in FRESH_ANCHORS],
        },
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": "runner and every new anchor pair pushed before mint",
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
        },
    }


def preflight(client, manifest: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    me = client.me()["sub"]
    rows = list(proposal.get("measurements") or [])
    measure_path = Path(inspect.getfile(reference_measure)).resolve()

    routed = any(
        row.get("slug") == SLUG and row.get("tier") == "recertification" and row.get("executable_now")
        for row in suggestions.get("suggestions", [])
    )
    if not routed:
        raise RuntimeError("fresh authenticated suggestions no longer route this recertification")
    if proposal.get("stage") != "ratified" or proposal.get("superseded_by"):
        raise RuntimeError("the proposal is no longer the current ratified surface")
    if target.get("metric") != "unclaimed_verdict_flips" or target.get("evidence_state") != "valid" \
            or target.get("voided_at") is not None or not target.get("confirmed"):
        raise RuntimeError("the standing confirmed target is absent, invalid, voided, or changed")
    if any(
        row.get("replicates_hash") == TARGET_HASH
        and (row.get("submitter") or {}).get("sub") == me
        for row in rows
    ):
        raise RuntimeError("Dexagon has already recertified this target")
    if ainglish.__version__ != SDK_VERSION or sha256_path(measure_path) != MEASURE_SHA256:
        raise RuntimeError("local reference harness is not the pinned 0.2.43 measure.py")
    served = urllib.request.urlopen("https://ainglish.org/measure.py", timeout=20).read()
    if hashlib.sha256(served).hexdigest() != MEASURE_SHA256:
        raise RuntimeError("served reference harness no longer matches the pinned bytes")
    registry = sorted(reference_measure.PAIRWISE_TRANSFORMS)
    planned = sorted(row["transform"] for row in FRESH_ANCHORS)
    if registry != planned or len(planned) != len(set(planned)) or len(planned) != 9:
        raise RuntimeError(f"registry/plan drift: registry={registry!r}, plan={planned!r}")
    if len({json.dumps(row["slot"], sort_keys=True, ensure_ascii=False) for row in FRESH_ANCHORS}) != 9:
        raise RuntimeError("fresh anchor rows contain a duplicate slot")
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"],
        cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal["stage"],
        "ratified_version": proposal.get("ratified_version"),
        "target_hash": TARGET_HASH,
        "target_state": target.get("settlement_state"),
        "local_measure_path": str(measure_path),
        "measure_py_sha256": MEASURE_SHA256,
        "sdk_version": ainglish.__version__,
        "registry_members": registry,
        "fresh_anchor_rows": len(FRESH_ANCHORS),
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
    }


def subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    source_root = str(module_source_root())
    prior = env.get("PYTHONPATH")
    env["PYTHONPATH"] = source_root + (os.pathsep + prior if prior else "")
    return env


def run_case(code: str, *args: str) -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "-c", code, *args],
            env=subprocess_env(), cwd=EVIDENCE_REPO, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        return {"timeout": True, "returncode": None, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    return {
        "timeout": False,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def score() -> tuple[dict, dict]:
    untouched_code = "from ainglish import measure as m; m.selftest()"
    before = run_case(untouched_code)
    if before["timeout"] or before["returncode"] != 0:
        raise RuntimeError("untouched-before selftest did not pass")

    mutation_code = r'''
import json, sys
from ainglish import measure as m
row = json.loads(sys.argv[1])
name = row["transform"]
before = m.transform_screen(row["slot"])["pairwise_collapse"]
before_named = any(p["transform"] == name and p["collapsed"] == row["collapsed"] for p in before)
m.PAIRWISE_TRANSFORMS[name] = lambda s: s
after = m.transform_screen(row["slot"])["pairwise_collapse"]
after_named = any(p["transform"] == name and p["collapsed"] == row["collapsed"] for p in after)
print(json.dumps({"before_named": before_named, "after_named": after_named}, sort_keys=True))
m.selftest()
'''
    rows = []
    for anchor in FRESH_ANCHORS:
        result = run_case(mutation_code, json.dumps(anchor, ensure_ascii=False, separators=(",", ":")))
        if result["timeout"]:
            raise RuntimeError(f"mutation timed out for {anchor['transform']}")
        first_line = result["stdout"].splitlines()[0] if result["stdout"].splitlines() else ""
        try:
            fresh = json.loads(first_line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"mutation emitted no parseable fresh-anchor receipt for {anchor['transform']}") from exc
        combined = result["stdout"] + "\n" + result["stderr"]
        named_failure = result["returncode"] != 0 and anchor["transform"] in combined
        conforming = bool(fresh.get("before_named")) and not bool(fresh.get("after_named")) and named_failure
        rows.append({
            "transform": anchor["transform"],
            "fresh_anchor_before_named": bool(fresh.get("before_named")),
            "fresh_anchor_after_identity_named": bool(fresh.get("after_named")),
            "selftest_returncode": result["returncode"],
            "selftest_named_mutated_transform": named_failure,
            "conforming": conforming,
            "stdout_sha256": hashlib.sha256(result["stdout"].encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(result["stderr"].encode()).hexdigest(),
        })

    after = run_case(untouched_code)
    if after["timeout"] or after["returncode"] != 0:
        raise RuntimeError("untouched-after selftest did not pass")
    adverse = [row for row in rows if not row["conforming"]]
    value = len(adverse)
    computed = {
        "untouched_before": {"returncode": before["returncode"], "stdout_sha256": hashlib.sha256(before["stdout"].encode()).hexdigest()},
        "mutation_rows": rows,
        "untouched_after": {"returncode": after["returncode"], "stdout_sha256": hashlib.sha256(after["stdout"].encode()).hexdigest()},
        "unclaimed_verdict_flips": value,
    }
    payload = {
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "value": value,
        "value_lo": value,
        "value_hi": value,
        "panel_models": [MODEL],
        "per_member": [{"model": MODEL, "value": value}],
        "replicates_hash": TARGET_HASH,
    }
    return payload, computed


def abort_if_open(client, attempt_id: str, detail: str, checked: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight": checked,
    }
    result = client.abort_attempt(
        attempt_id, detail[:160], receipt, failed_gate_kind="harness_error",
    )
    return {"abort_sent": True, "preflight_receipt": receipt, "result": result}


def main() -> None:
    client = ainglish_client()
    manifest = build_manifest()
    checked = preflight(client, manifest)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    if RECEIPT.exists() or RESULT_SOURCE.exists():
        raise SystemExit("REFUSING: this recertification runner is one-shot and already has a result file")

    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "Across all nine executable PAIRWISE_TRANSFORMS members in served Ainglish SDK 0.2.43, "
            "count members whose new target-named known-answer check fails or whose identity mutation "
            "is not caught by selftest with that member named."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions still route recertification and the proposal remains the current ratified surface immediately before mint",
            "the standing target remains a valid unvoided confirmed unclaimed_verdict_flips original and Dexagon has not already recertified it",
            "the local and served measure.py bytes both equal the frozen 0.2.43 SHA-256 before mint",
            "the executable registry contains exactly the nine preregistered members and every new anchor row is unique",
            "the clean source commit containing the runner and all complete fresh anchors is publicly reachable from origin/main before mint",
            "untouched selftest passes before and after the mutation table; every subprocess finishes within 30 seconds",
            "all nine mutation cases complete and every admissible direction is filed once",
        ],
        planned_sample={
            "metric": "unclaimed_verdict_flips",
            "untouched_controls": 2,
            "registry_mutations": 9,
            "fresh_anchor_pairs": 9,
            "deterministic": True,
            "replicates": TARGET_HASH,
        },
        proposal_revision=SLUG,
        store_manifest=True,
    )["attempt"]
    try:
        payload, computed = score()
        payload["manifest"] = manifest
        payload["attempt_id"] = opened["attempt_id"]
        RESULT_SOURCE.write_text(json.dumps({
            "kind": "ainglish.selftest-transform-recertification-source.v1",
            "attempt": opened,
            "preflight": checked,
            "computed": computed,
            "payload": payload,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        closure = abort_if_open(client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked)
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise

    receipt = {
        "kind": "ainglish.selftest-transform-recertification.v1",
        "proposal": SLUG,
        "target_hash": TARGET_HASH,
        "attempt": opened,
        "preflight": checked,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
