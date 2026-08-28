# Flagship evidence-map deploy conformance v1

Status: **preregistered; production deployment pending**

This acceptance packet binds the public website, REST API, OpenAPI description, MCP tool, Python
SDK, and both agent-plugin action surfaces to one flagship evidence-map contract. It is read-only and
uses no credential.

The checker requires all of the following in one run:

1. `/api/v1/flagships/evidence-map` serves `ainglish.flagship-evidence-map.v1` with exactly the six
   declared axes and a digest-bound entry population;
2. its source catalogue digest equals `/api/v1/flagships` and every entry carries one state per axis;
3. node and edge counts conserve the complete population without creating a score or ladder;
4. `/flagships/evidence-map` renders every row and names both “No blended score” and the receipt-matrix
   boundary;
5. `/openapi.json` declares the REST path;
6. MCP discovery lists `get_flagship_evidence_map`, and the MCP call returns exactly the REST payload;
7. the released Python SDK exposes `flagship_evidence_map()` and returns exactly the REST payload;
8. the checked-out OpenAI and Claude plugin dispatchers expose the same reviewed 48-action set,
   including `flagship_evidence_map`, while excluding exactly the six documented low-level or
   infrastructure methods.

The run refuses to overwrite a prior receipt. Execute only after Symfony PR #340 is deployed, SDK PR
#109 is merged, and SDK 0.2.43 is installed:

```bash
python3 check.py
```

This is transport and contract acceptance, not human validation, governance evidence, or proof that
the catalogue entries deserve ratification.
