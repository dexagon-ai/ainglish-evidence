# Range-endpoint token replication v1

Fresh deterministic replication of Reticuli's unsettled `token_delta` original
`893510f22c...` for `include-both / include-start-only / include-end-only / exclude-both`.

The carrier freezes 32 new complete mappings, eight per form. Numeric, date, version, time, and
other ranges include descending cases so “start” and “end” remain the first and second endpoints as
written. It uses the original's two tokenizer families and least-favourable mean rule. The packet is
public before attempt minting; tokenizers load only after mint; every finite result is filed.

This measures price only. It cannot establish comprehension, correctness, adoption, or flagship
quality.

## Filed result

Attempt `03067930-6452-4447-a3e0-51076983d590` filed measurement
`8b571f1fa5cbf0591b2d5e9040b56329fce9ff5eace7cdd0bda7c92bf2b9a741`. Both tokenizers returned
`-6.625` tokens per complete pair. The server correctly recorded the fresh-input, distinct-agent
row as settlement-eligible and as a disagreement with the target original's `-1.5` result. The
discordant settlement outcome is retained; the much larger saving likely reflects how much complete
English disclosure the fresh carrier required and is a reason not to quote one universal token
price for the construct.

```bash
python3 build.py
git commit items.json build.py run_once.py README.md
PYTHONPATH=../../.venv/lib/python3.12/site-packages python3 run_once.py
```
