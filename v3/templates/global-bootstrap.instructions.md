---
applyTo: '**'
description: 'GLOBAL BOOTSTRAP: Auto-load REUSABLE_AI_KIT v3 for all projects'
---

# REUSABLE_AI_KIT Global Bootstrap (v3)

> This instruction is installed in `%APPDATA%\Code\User\Instructions\` by `scripts/install-global.ps1`.

## Default Agent

Select **`@aikit`** as your default agent. It automatically:
- Classifies task complexity (XS through XL)
- Boosts vague prompts (asks 2-3 questions instead of guessing)
- Recalls DuckDB memory before M+ tasks for prior conventions, decisions, and pitfalls
- Handles simple tasks directly; decomposes complex work into parallel subagent calls
- Saves durable learnings to DuckDB at session end

For full iterative prompt crafting, use `/boost-prompt` instead.

## Required Load Order

1. Load `000-core-rules.instructions.md` first.
2. Load `orchestration.instructions.md` second.
3. Load remaining `*.instructions.md` files from the kit.

## Global Kit Location

- **Windows**: `%APPDATA%\Code\User\REUSABLE_AI_KIT\`
- **macOS**: `~/Library/Application Support/Code/User/REUSABLE_AI_KIT/`
- **Linux**: `~/.config/Code/User/REUSABLE_AI_KIT/`

## Key Resources

- **Primary agent**: `@aikit` (always start here)
- Agents: `<kit-root>/agents/`
- Prompts: `<kit-root>/prompts/`
- Tools: `<kit-root>/tools/`
- Memory: `<kit-root>/memory/` (DuckDB-backed, BM25 search)

## Global Commands

- `/setup-ai-kit`
- `/update-ai-kit`
- `/kit-status`
- `/boost-prompt` — interactive prompt refinement wizard
- `/memory-save` — persist session learnings to DuckDB
- `/memory-recall` — retrieve prior context before a task
