---
agent: agent
description: 'Multi-agent bugfix pipeline: investigate, debug, fix, test, review.'
---

# Bugfix Pipeline

Orchestrate systematic bug diagnosis and repair using specialized agents.

## Pipeline

```
memory-recall -> investigate -> debugger -> fix -> tester -> reviewer -> memory-save
```

## Step 0: Memory Recall

Before investigating, check DuckDB for prior context on this bug or component:
```bash
python tools/global_memory.py search --query "<error message or component name>" --scope project --namespace issues --limit 5 --format markdown
python tools/global_memory.py search --query "<component name>" --scope project --namespace conventions --limit 3 --format markdown
```
Apply any known pitfalls or prior fixes. Skip duplicate investigation.

## Step 1: Investigate

Gather context before debugging:
- Read the error message, stack trace, or bug report
- Identify affected files, components, and services
- Check `memory/shared/issue-tracker.md` for related known issues
- Check `memory/shared/session-log.md` for recent changes that might be related

## Step 2: Debug (@debugger)

Systematic root cause analysis:
- Form minimum 3 hypotheses
- Investigate each, starting with most likely
- Trace execution, check state at key points
- Confirm root cause with evidence

## Step 3: Fix

Apply the minimal fix:
- Change only what's necessary to resolve the root cause
- Match existing code style and patterns
- Verify with `get_errors` after editing

## Step 4: Test (@tester)

Verify the fix and prevent regression:
- Confirm the bug no longer reproduces
- Add a regression test for this specific bug
- Run existing test suite to confirm no regressions

## Step 5: Review (@reviewer)

Quick review of the fix:
- Fix is correct and complete
- No security implications
- No unintended side effects
- Regression test is adequate

## Completion

1. Update `memory/shared/issue-tracker.md` with the bug and fix details
2. Update `memory/shared/session-log.md` with what was found and fixed
3. Save root cause to DuckDB for future recall:
   ```bash
   python tools/global_memory.py upsert --scope project --namespace issues --key "<component.symptom>" --title "<bug title>" --content "<root cause and fix>" --tags "<component,category>"
   ```
4. Report to user: what broke, why, what was fixed, how it was tested

## Rules

- Don't guess. Investigate before fixing.
- Minimal changes only. Don't refactor while fixing bugs.
- Always add a regression test.
- Start servers in background/external terminals - never block VS Code
