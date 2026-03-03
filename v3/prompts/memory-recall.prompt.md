---
agent: agent
description: 'BM25-powered recall of relevant persistent memory before a high-context task.'
---

# Memory Recall

Before starting the current task, retrieve and synthesize relevant persistent memory using BM25 search.

## Steps

1. **Extract keywords** from the user's request: subject, domain, component names, error terms.

2. **Run scoped searches** — start project-specific, widen if sparse:
   ```bash
   # Primary: project-scoped (most specific)
   python tools/global_memory.py search \
     --query "<task keywords>" --scope project --limit 8 --format markdown

   # Secondary: global conventions that always apply
   python tools/global_memory.py search \
     --query "<task keywords>" --scope global --limit 5 --format markdown

   # Commands: always check before running anything
   python tools/global_memory.py recent \
     --namespace commands --limit 10 --format markdown
   ```

3. **Narrow by namespace** when the task is domain-specific:
   ```bash
   # For architecture / design work
   python tools/global_memory.py search \
     --query "<component>" --namespace architecture --limit 5

   # For bug investigation
   python tools/global_memory.py search \
     --query "<symptom or component>" --namespace issues --limit 8
   ```

4. **Synthesize** the relevant hits into a concise working brief:
   - 3-5 bullets max
   - Highlight any conflicts or outdated entries (flag them for update)
   - State what BM25 score threshold you treated as meaningful (typically > 0.1)

5. **Apply** findings before generating a plan. Do not regenerate knowledge you already have.

## Reading BM25 Results

- Results are sorted by relevance score (higher = more relevant).
- Top result at > 0.3 score: highly relevant, apply directly.
- 0.1 – 0.3: probably relevant, use with judgment.
- < 0.1: weak match, treat as background context only.
- Zero results or ILIKE fallback (`"mode": "ilike"`): keyword not indexed yet — proceed without memory bias.

## Fallback (no useful hits)

1. State that memory has no relevant matches.
2. Proceed with normal investigation.
3. Schedule a `memory-save` at end of session to capture what was learned.

## Output Brief Format

```
## Memory Brief: <task summary>

**Relevant hits (n):**
- [id:X scope/namespace/key] — <title>: <one-line summary to apply>

**Verified commands:**
- <command>

**Known pitfalls:**
- <pitfall>

**Applying:** <what this knowledge changes about the approach>
**Not found:** <what still needs investigation>
```
