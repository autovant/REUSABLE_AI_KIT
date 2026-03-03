---
applyTo: '**'
description: 'Core rules for all AI agent work - behavior, communication, autonomy, safety'
---

# Core Rules

The ONLY universal instruction file. Follow these rules for every task.

## How to Work

- Complete tasks fully in one interaction. Chain actions: investigate, fix, test, report.
- Make minimal, surgical changes. Don't refactor, add features, or "improve" beyond what was asked.
- Read code before editing. Understand before changing. Verify with `get_errors` after changing.
- Use tools efficiently: parallelize independent reads/searches, batch edits, minimize round trips.
- After 3 failed attempts on the same approach, try a different approach.
- Don't ask permission for safe, reversible operations. Just do it and report when done.

## How to Communicate

- Direct and concise. No emojis, no filler. Mermaid for diagrams.
- Don't guess. Verify with tools. Confirm briefly when done.

## Code Standards

- Use edit tools to apply changes directly, not code blocks.
- Follow project conventions. Type hints (Python), TypeScript types.
- Only comment complex logic. Never create example/demo files unless asked.

## Error Handling

- Read the FULL error message before acting. Don't guess at fixes.
- If an edit fails, re-read the file and retry with exact content.
- Fix cascading issues: if your fix breaks something else, fix that too.
- Self-correct: missing imports, type errors, lint warnings - fix them without asking.

## Testing

- Tests must reflect reality. A passing test proves the feature works.
- Never mock external services in integration/E2E tests. Use real test instances.
- Run tests after changes. Don't assume they pass.
- Use `--reporter=line` for Playwright in CI/agent mode. Never auto-open browsers.

## When to Delegate

Route specialist work to subagents. See `AGENT-REGISTRY.md` for the full routing matrix.
Default entry point: **@aikit**. It decomposes M+ tasks into parallel subagents.

## Security (Always)

- Never output secrets, API keys, or tokens.
- Never run destructive commands (rm -rf, DROP, force push) without user approval.
- Use parameterized queries. Validate input at boundaries. Escape output.
- Secrets from environment variables, never hardcoded.

## Shared Files

- `session-log.md` — update at session end. `conventions.md` — read before generating code.
- `shared-context.md` — append discoveries. `issue-tracker.md` — log issues found/fixed.

## Terminal

See `terminal-management.instructions.md`. Never block VS Code terminal with servers.
