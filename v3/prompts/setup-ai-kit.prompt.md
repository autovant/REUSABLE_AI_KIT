---
agent: agent
description: 'Integrate AI Kit into the current project with safe merge behavior and local memory scaffolding.'
tools: ["read", "edit", "search"]
---

# Setup AI Kit for Current Project

Safely integrate project-local configuration without overwriting user instructions.

## Goals

1. Detect existing project instruction files.
2. Merge AI Kit integration section (append-only, never destructive).
3. Create `.copilot/memory/` subfolders if missing.
4. Keep all existing project guidance intact.

## Safety Rules

- Never overwrite existing instruction files.
- Read before edit.
- Append integration section only if missing.
- Report exactly what was changed and what was preserved.

## Integration Section (append if missing)

- Instruct loading of kit instruction files in order:
  1. `000-core-rules.instructions.md`
  2. `orchestration.instructions.md`
  3. remaining `*.instructions.md`

## Completion

Return:
- Files modified
- Files created
- Detected stack summary
- Next steps for the user
