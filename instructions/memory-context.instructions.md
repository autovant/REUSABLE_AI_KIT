---
applyTo: '**'
description: 'Use persistent DuckDB memory strategically for cross-session recall, BM25 search, and pattern analysis'
---

# Memory & Context Strategy

The kit ships a DuckDB-backed memory store (`tools/global_memory.py`) with columnar storage and BM25 full-text search. Use it as a first-class tool — not a last resort.

## Retrieval-First Rule (Non-Negotiable)

Before ANY medium or large task:
1. Query memory for related conventions, prior decisions, and known issues.
2. Apply relevant findings before generating a plan.
3. If no matches: proceed, then capture learnings at the end.

Silently skipping retrieval is a mistake. The cost of a fast search is zero. The cost of rediscovering a known bug is high.

## When to Use Memory

| Signal | Action |
|--------|--------|
| Multi-session investigation | Query at start, save at end |
| "How does X work in this codebase?" | Query `architecture` namespace first |
| About to touch auth/infra/config | Query `issues` for prior pitfalls |
| Running a build/test/deploy | Query `commands` for verified invocations |
| End of any productive session | Save all durable learnings |

## Three Scopes — Use Them Correctly

| Scope | TTL intent | Use for |
|-------|-----------|----------|
| `global` | Permanent | Language conventions, universal architecture facts |
| `project` | Project lifetime | This repo's patterns, commands, decisions |
| `session` | Ephemeral reference | Today's investigation log, WIP hypotheses |

Query globally first, then narrow: `--scope project` to find project-specific overrides.

## Namespaces

- `conventions` — coding style, naming, structure
- `issues` — bug patterns, root causes, prevention
- `architecture` — design decisions, constraints, component boundaries
- `commands` — verified build/test/lint/deploy invocations
- `sessions` — brief dated summaries of key outcomes
- `context` — large snippets or data too big for chat (schema, audit output, specs)

## Tags — Use for Precise Filtering

Tag entries at save time so recall can filter precisely:
```bash
# Save with tags
python tools/global_memory.py upsert \
  --scope project --namespace issues --key auth.timeout \
  --title "Auth timeout on cold start" \
  --content "Add TIMEOUT_SECONDS=30 to env; root cause is lazy DB connection pool" \
  --tags "auth,backend,env"
```

## BM25 Search — Prefer Keyword-Rich Queries

DuckDB FTS uses BM25 (relevance-ranked). Results are ordered by score — higher is better. Unlike SQLite LIKE, partial words and stemming work:

```bash
# Good — term-rich, gets ranked results
python tools/global_memory.py search --query "auth timeout cold start" --limit 8

# Scope-narrow when the problem is project-specific
python tools/global_memory.py search --query "pytest collection" --scope project --limit 5

# Namespace-narrow for surgical recall
python tools/global_memory.py search --query "migration rollback" --namespace architecture --limit 5

# Recent entries — good for session continuity
python tools/global_memory.py recent --limit 10 --scope session
```

## Analytical Pattern Mining (DuckDB advantage)

Because DuckDB is columnar, agents can query patterns across the entire memory store:

```bash
# What do we know about authentication across all projects?
python tools/global_memory.py search --query "authentication" --scope global --limit 20 --format markdown

# Review all saved commands before automating
python tools/global_memory.py recent --namespace commands --limit 20 --format markdown

# Session audit: what did we investigate today?
python tools/global_memory.py recent --scope session --limit 50 --format markdown
```

## What to Store

**Store:**
- Project conventions that would take >5 minutes to rediscover
- Root causes of bugs that took >1 hour to find
- Architecture decisions and the reasoning behind them
- Every verified build/test/deploy command
- Brief session summaries with outcomes

**Never store:**
- Secrets, tokens, API keys, passwords
- PII or sensitive user data
- Transient state (current line numbers, WIP diffs)
- Full file contents (store location + summary instead)

## Save Discipline

- Use `upsert` with a stable key for facts that update over time
- Use `append` for investigation logs and session events
- Keep content actionable: "Add X to env" beats "Something about X"
- Keep titles scannable: they appear in BM25 search results

## Large-Context Workflow

1. **Retrieve** — search 5-10 entries most relevant to the task
2. **Synthesize** — distil into a 3-5 bullet working brief
3. **Execute** — implement with focused context
4. **Persist** — save net-new durable learnings before session ends

## One-Time Setup

```bash
# Installer handles this automatically; manual steps if needed:
pip install duckdb
python tools/global_memory.py init
```
