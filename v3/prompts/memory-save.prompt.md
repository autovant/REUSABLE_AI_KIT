---
agent: agent
description: 'Capture durable session learnings into DuckDB memory (conventions, issues, architecture, commands).'
---

# Memory Save

Capture high-value learnings from this session into persistent memory.

## Steps

1. **Identify durable facts** from this session:
   - Conventions discovered or confirmed
   - Root causes / bugs likely to recur
   - Architecture decisions and reasoning
   - Verified commands (build, test, lint, deploy)
   - Hard-won context that took time to find

2. **Check for existing entries** before saving to avoid stale overwrites:
   ```bash
   python tools/global_memory.py search --query "<topic>" --limit 3
   ```
   - If an entry exists and is still accurate: skip (upsert only if content improved).
   - If it is outdated: upsert with the corrected content.
   - If it is net-new: upsert with a fresh key.

3. **Save each durable fact:**
   ```bash
   # Stable fact (updates over time) — use upsert with key
   python tools/global_memory.py upsert \
     --scope project --namespace conventions --key python.typing \
     --title "Python typing conventions" \
     --content "Use type hints for all public APIs. PEP 604 union syntax (X | Y) preferred." \
     --tags "python,style"

   # Investigation finding or event log — use append (no key)
   python tools/global_memory.py append \
     --scope session --namespace sessions \
     --title "2026-03-03: Auth refactor" \
     --content "Resolved timeout on cold start: added TIMEOUT_SECONDS=30 to env. 14 tests fixed."
   ```

4. **Output a save summary table.**

## Save Rules

- Content must be **actionable**, not descriptive. "Add X to env" beats "something about X".
- Titles must be **scannable** — they appear in BM25 search results.
- Use scopes correctly: `global` for universal facts, `project` for this repo, `session` for today's log.
- Tag for precision: `--tags "auth,backend"` enables surgical recall later.
- Never store: secrets, tokens, API keys, PII, full file contents, transient state.

## Namespace Guide

| Namespace | Key format example | Use for |
|-----------|--------------------|----------|
| `conventions` | `python.typing` | Coding/style/naming rules |
| `issues` | `auth.timeout.cold-start` | Bug patterns + root causes |
| `architecture` | `api.error-shape` | Design decisions + constraints |
| `commands` | `pytest.fast` | Verified build/test/deploy commands |
| `sessions` | (append — no key) | Dated session summaries |
| `context` | `schema.users-table` | Large data too big for chat |

## Completion Output

Provide:
- DB path used
- Entries saved (scope / namespace / key / title)
- Entries updated (what changed)
- Entries skipped (and why)
