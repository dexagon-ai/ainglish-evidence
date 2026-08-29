#!/usr/bin/env python3
"""Audit the frozen SDK/plugin action surface without importing or calling it."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *arguments],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def sdk_methods(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    classes = [
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "AinglishClient"
    ]
    if len(classes) != 1:
        raise ValueError(f"Expected one AinglishClient in {path}, found {len(classes)}")
    return {
        node.name
        for node in classes[0].body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }


def plugin_actions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    candidates: list[ast.AST] = []
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "ALLOWED_ACTIONS" and node.value is not None:
                candidates.append(node.value)
        elif isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "ALLOWED_ACTIONS" for target in node.targets):
                candidates.append(node.value)
    if len(candidates) != 1:
        raise ValueError(f"Expected one ALLOWED_ACTIONS assignment in {path}, found {len(candidates)}")
    value = candidates[0]
    if not (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "frozenset"
        and len(value.args) == 1
    ):
        raise ValueError(f"ALLOWED_ACTIONS in {path} must be a literal frozenset")
    parsed = ast.literal_eval(value.args[0])
    if not isinstance(parsed, set) or not all(isinstance(item, str) for item in parsed):
        raise ValueError(f"ALLOWED_ACTIONS in {path} must contain only string literals")
    return parsed


def project_version(path: Path) -> str:
    in_project = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("["):
            in_project = line == "[project]"
            continue
        if in_project:
            match = re.fullmatch(r'version\s*=\s*"([^"]+)"', line)
            if match:
                return match.group(1)
    raise ValueError(f"No [project] version found in {path}")


def requirement_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def checked_file(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.is_file():
        raise ValueError(f"Missing frozen input: {path}")
    return path


def inspect_sources(
    plan: dict[str, Any],
    sdk_root: Path,
    openai_root: Path,
    claude_root: Path,
) -> dict[str, Any]:
    roots = {
        "sdk": sdk_root.resolve(),
        "openai_plugin": openai_root.resolve(),
        "claude_plugin": claude_root.resolve(),
    }
    frozen = plan["frozen_sources"]
    commits = {name: git(root, "rev-parse", "HEAD") for name, root in roots.items()}
    clean = {name: git(root, "status", "--porcelain") == "" for name, root in roots.items()}

    sdk_client = checked_file(sdk_root, frozen["sdk"]["client_path"])
    plugin_main = {
        "openai_plugin": checked_file(openai_root, frozen["openai_plugin"]["dispatcher_path"]),
        "claude_plugin": checked_file(claude_root, frozen["claude_plugin"]["dispatcher_path"]),
    }
    methods = sdk_methods(sdk_client)
    actions = {name: plugin_actions(path) for name, path in plugin_main.items()}

    categories = plan["expected_action_categories"]
    memberships = [action for values in categories.values() for action in values]
    expected_actions = set(memberships)
    exclusions = set(plan["expected_exclusions"])
    requirement = plan["required_sdk_range"]

    pin_files: dict[str, dict[str, Path]] = {}
    for name, root in (("openai_plugin", openai_root), ("claude_plugin", claude_root)):
        pin_files[name] = {
            "requirements": checked_file(root, "skills/ainglish-participate/requirements.txt"),
            "workflow": checked_file(root, ".github/workflows/ci.yml"),
            "readme": checked_file(root, "README.md"),
            "skill": checked_file(root, "skills/ainglish-participate/SKILL.md"),
        }

    source_hashes = {
        "sdk/client.py": sha256(sdk_client),
        "sdk/pyproject.toml": sha256(checked_file(sdk_root, "pyproject.toml")),
    }
    for name, path in plugin_main.items():
        source_hashes[f"{name}/main.py"] = sha256(path)
        for label, pin_path in pin_files[name].items():
            source_hashes[f"{name}/{label}"] = sha256(pin_path)

    checks: dict[str, bool] = {
        "source_commits_match": all(
            commits[name] == frozen[name]["commit"] for name in roots
        ),
        "source_checkouts_clean": all(clean.values()),
        "sdk_source_version_is_preregistered": project_version(sdk_root / "pyproject.toml")
        == frozen["sdk"]["source_version"],
        "plugin_requirements_exact": all(
            requirement_lines(files["requirements"]) == [requirement]
            for files in pin_files.values()
        ),
        "plugin_ci_pins_range": all(
            requirement in files["workflow"].read_text(encoding="utf-8")
            for files in pin_files.values()
        ),
        "plugin_readmes_pin_range": all(
            requirement in files["readme"].read_text(encoding="utf-8")
            for files in pin_files.values()
        ),
        "plugin_skills_pin_range": all(
            requirement in files["skill"].read_text(encoding="utf-8")
            for files in pin_files.values()
        ),
        "category_membership_has_no_duplicates": len(memberships) == len(expected_actions),
        "expected_action_count_is_48": len(expected_actions) == 48,
        "plugins_match_each_other": actions["openai_plugin"] == actions["claude_plugin"],
        "plugins_match_preregistered_actions": all(
            value == expected_actions for value in actions.values()
        ),
        "sdk_minus_plugins_is_exactly_six_exclusions": methods - expected_actions == exclusions,
        "plugins_have_no_non_sdk_action": expected_actions - methods == set(),
        "sdk_public_callable_count_is_54": len(methods) == 54,
        "flagship_map_is_exposed": "flagship_evidence_map" in expected_actions,
        "moderator_slug_rename_is_exposed": "rename_proposal_slug" in expected_actions,
        "raw_transport_is_not_exposed": {"get", "post"}.isdisjoint(expected_actions),
        "webhook_configuration_is_not_exposed": {
            "webhooks", "create_webhook", "delete_webhook"
        }.isdisjoint(expected_actions),
    }

    result: dict[str, Any] = {
        "schema": "ainglish.plugin_sdk_action_surface.result.v1",
        "pass": all(checks.values()),
        "checks": checks,
        "source_commits": commits,
        "source_checkouts_clean": clean,
        "source_file_sha256": dict(sorted(source_hashes.items())),
        "sdk": {
            "source_version": project_version(sdk_root / "pyproject.toml"),
            "intended_release": frozen["sdk"]["intended_release"],
            "public_callable_count": len(methods),
            "public_callables": sorted(methods),
        },
        "plugins": {
            name: {"action_count": len(value), "actions": sorted(value)}
            for name, value in sorted(actions.items())
        },
        "action_categories": categories,
        "exclusions": plan["expected_exclusions"],
        "required_sdk_range": requirement,
        "claim_boundary": plan["claim_boundary"],
    }
    result["content_sha256"] = canonical_sha256(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--openai-root", type=Path, required=True)
    parser.add_argument("--claude-root", type=Path, required=True)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--output", type=Path)
    target.add_argument("--verify", type=Path)
    args = parser.parse_args()

    plan = json.loads((HERE / "RUN_PLAN.json").read_text(encoding="utf-8"))
    try:
        result = inspect_sources(plan, args.sdk_root, args.openai_root, args.claude_root)
    except (OSError, subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSED: {error}")
        return 2

    if not result["pass"]:
        failed = [name for name, passed in result["checks"].items() if not passed]
        print("REFUSED: " + ", ".join(failed))
        return 1

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"PASS: {len(result['sdk']['public_callables'])} SDK methods, "
              f"{result['plugins']['openai_plugin']['action_count']} reviewed plugin actions")
        print(result["content_sha256"])
        return 0

    expected = args.verify.read_text(encoding="utf-8")
    if expected != rendered:
        print(f"REFUSED: regenerated result differs from {args.verify}")
        return 1
    print(f"PASS: {args.verify} reproduces exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
