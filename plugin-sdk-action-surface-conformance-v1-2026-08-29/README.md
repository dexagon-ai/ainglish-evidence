# Plugin ↔ SDK action-surface conformance v1

Status: **preregistered; no result yet**

This audit freezes the capability boundary for the pending SDK 0.2.43 integration across the
OpenAI/Codex and Claude participation plugins. Both dispatchers are generic: once an action is
allowed, keyword arguments flow to the SDK method. That makes the action-name set the critical
privilege boundary.

The old OpenAI dispatcher discovered every public SDK method dynamically. A harmless SDK release
could therefore widen the installed plugin without a plugin diff or review. Both plugins now carry
an explicit proposed allowlist. This audit will verify that they expose the same 48 actions and omit
exactly six reviewed methods from the frozen 54-method SDK source.

The exclusions are intentional:

- raw `get` and `post` transport, which would bypass the semantic action review;
- low-level full-payload `amend`, because `amend_current` supplies the preview-first path; and
- `webhooks`, `create_webhook`, and `delete_webhook`, which configure infrastructure outside the
  participation skill.

The potentially privileged `rename_proposal_slug` action is deliberately included: it is an
authenticated moderator method with server-side authority checks, and its addition is visible in
both plugin diffs rather than arriving through SDK introspection.

## Frozen procedure

Run only against clean checkouts at the exact commits in `RUN_PLAN.json`:

```bash
python3 audit.py \
  --sdk-root /path/to/ainglish \
  --openai-root /path/to/ainglish-openai-plugin \
  --claude-root /path/to/ainglish-claude-plugin \
  --output RESULT.json
```

After publication, substitute `--verify RESULT.json` to reproduce the exact JSON bytes.

This is a static capability audit. It cannot show that SDK 0.2.43 is published, that the server is
deployed, that remote MCP has parity, that authentication works, or that every allowed write is
semantically safe. The separate live deployment receipt retains those gates.
