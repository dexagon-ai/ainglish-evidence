#!/usr/bin/env python3
"""Run the one frozen generic instruction revision over exposed controls."""

from __future__ import annotations

from run_development_once import CODES, execute


def tuned_prompt(item: dict, plan: dict) -> tuple[str, dict[str, str]]:
    mapping = {CODES[index]: option for index, option in enumerate(item["options"])}
    choices = "\n".join(f"{code}: {option}" for code, option in mapping.items())
    text = (
        plan["prompt_contract"] + "\n\nPremise:\n---\n" + item["premise"] +
        "\n---\n\nHypothesis: " + item["hypothesis"] + "\nChoices:\n" + choices +
        "\nAnswer with EXACTLY one choice code and nothing else."
    )
    return text, mapping


if __name__ == "__main__":
    execute(
        "tuned-run-plan.json",
        "development-tuned-result.json",
        "development-tuned-attempt-journal.jsonl",
        tuned_prompt,
    )
