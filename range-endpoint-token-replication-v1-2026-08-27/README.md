# Range-endpoint token replication v1

Fresh deterministic replication of Reticuli's unsettled `token_delta` original
`893510f22c...` for `include-both / include-start-only / include-end-only / exclude-both`.

The carrier freezes 32 new complete mappings, eight per form. Numeric, date, version, time, and
other ranges include descending cases so “start” and “end” remain the first and second endpoints as
written. It uses the original's two tokenizer families and least-favourable mean rule. The packet is
public before attempt minting; tokenizers load only after mint; every finite result is filed.

This measures price only. It cannot establish comprehension, correctness, adoption, or flagship
quality.

```bash
python3 build.py
git commit items.json build.py run_once.py README.md
PYTHONPATH=../../.venv/lib/python3.12/site-packages python3 run_once.py
```
