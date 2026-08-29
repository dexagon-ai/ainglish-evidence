# Group-scope uncertainty boundary gauntlet v1

Status: **protocol preparation; no inference result yet**.

This supplied-reference diagnostic responds to an independent review objection: neither
`each-group` nor `groups-combined` says that a directional result is statistically significant,
precise, low-variance, or equal in magnitude across member groups. Aggregation scope and
uncertainty are separate axes.

The 48 frozen items cross both forms, four boundary families, and three explicit evidence states:
the extra claim is stated true, stated false, or absent. Answer labels and positions are balanced.
The run uses three already-installed model families, makes no download, and retains malformed,
null, and adverse outcomes without retry.

Every prompt supplies the exact reference. This therefore tests reference-grounded boundary
application, not cold comprehension, human understanding, independent evidence, or an Ainglish
measurement eligible for governance.

```bash
python3 build.py
python3 run_ollama.py verify
python3 run_ollama.py run
python3 analyse.py
```
