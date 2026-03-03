---
applyTo: '**'
description: 'Agent orchestration, tool usage, context management, and task estimation'
---

# Orchestration & Workflow

## Tool Usage Strategy

### Read Operations (parallelizable)
- Read multiple files in parallel when they're independent
- Use `grep_search` for quick lookups in known files
- Use `semantic_search` when you don't know the exact string
- Use `file_search` when you know the filename pattern

### Edit Operations (sequential)
- Read the file before editing
- Include 3-5 lines of context in replacements
- Run `get_errors` after edits
- One logical change per edit

### Terminal Operations (one at a time)
- Never run two terminal commands in parallel
- Check for running services before reusing a terminal
- Use `isBackground: true` for servers and watch processes

## Quality Gates

Before declaring any task done:
- [ ] `get_errors` returns clean on all changed files
- [ ] Tests run and pass (if test infrastructure exists)
- [ ] No regressions in related functionality
- [ ] Changes match existing code style

### Change Impact Assessment (M+ tasks)

Before any M+ change, also check:
1. What files import/use the thing being changed?
2. Are there tests that will break?
3. Does the UI consume this data?
4. Are there database migrations needed?
