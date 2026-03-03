# Agent Registry

All available agents in the kit. **Start with `@aikit`** — it classifies, boosts, recalls memory, handles simple tasks directly, and decomposes complex work into parallel subagent calls.

## Primary Entry Point

| Agent | Tools | Purpose | Invoke When |
|-------|-------|---------|-------------|
| **`@aikit`** | read, edit, search, execute, agent, todo | **Default agent.** Classifies tasks, boosts vague prompts, recalls DuckDB memory, handles XS/S directly, decomposes M+ into parallel subagent work, synthesizes results. | **All tasks.** Select this by default. |

## Quality Gate

| Agent | Tools | Purpose | Invoke When |
|-------|-------|---------|-------------|
| `@synthesizer` | read, edit, search, execute | Reviews subagent outputs, resolves conflicts, corrects errors | Called by @aikit after parallel subagents complete |

## Domain Specialists

| Agent | Tools | Purpose | Invoke When |
|-------|-------|---------|-------------|
| `@frontend-engineer` | read, edit, search, execute | React, TypeScript, CSS, accessibility, responsive design | UI components, styling, client-side work |
| `@backend-engineer` | read, edit, search, execute | API design, database, auth, server performance | Endpoints, migrations, server logic |
| `@investigator` | read, search, execute | Cross-layer debugging, traces issues across boundaries | Bug spans frontend+backend+DB |
| `@janitor` | read, edit, search, execute | Tech debt, dead code, dependency updates, cleanup | Maintenance, hygiene tasks |

## Methodology Specialists

| Agent | Tools | Purpose | Invoke When |
|-------|-------|---------|-------------|
| `@debugger` | read, edit, search, execute | Scientific root cause analysis | Bugs, errors, test failures |
| `@reviewer` | read, search | Code quality across 7 dimensions (read-only) | Code review, PR checks |
| `@architect` | read, search | System design, tech choices, ADRs | New components, major design decisions |
| `@tester` | read, edit, search, execute | Test generation, coverage, edge cases | Writing/fixing tests |
| `@planner` | read, search, todo | Task breakdown, estimation, dependency mapping | Complex multi-step work, unclear scope |
| `@refactorer` | read, edit, search, execute | Safe restructuring with verification | Cleanup without behavior change |
| `@documenter` | read, edit, search | README, API docs, architecture docs | Documentation tasks |
| `@security-auditor` | read, search, execute | OWASP Top 10, vulnerability detection | Security reviews, auth work |

## Routing Decision

```
Task arrives → @aikit (always)
│
├─ Vague / underspecified?
│   └─ @aikit auto-boosts: explores codebase, asks 2-3 questions, then proceeds
│
├─ Simple (XS/S: 1-2 files, one domain)?
│   └─ @aikit handles directly (no overhead)
│
├─ Complex (M+: multi-domain, 3+ files)?
│   └─ @aikit recalls DuckDB memory → decomposes → parallel subagents → synthesize
│
├─ Bug / Error?
│   ├─ Single layer → @debugger
│   └─ Cross-layer → @investigator
│
├─ New feature?
│   ├─ Frontend only → @frontend-engineer
│   ├─ Backend only → @backend-engineer
│   └─ Full stack → @aikit decomposes into parallel subagents
│
├─ Code review? → @reviewer then @security-auditor
├─ Tests needed? → @tester
├─ Docs needed? → @documenter
├─ Cleanup? → @janitor
├─ Design decision? → @architect
└─ Plan needed? → @planner
```

## Parallel Subagent Pattern

For M+ tasks, @aikit decomposes and launches independent subtasks as parallel subagents:

```
1. ANALYZE task scope
2. DECOMPOSE into independent subtasks
3. LAUNCH independent subtasks as parallel subagents
4. WAIT for all to return
5. SYNTHESIZE results (fix conflicts, check errors)
6. LAUNCH sequential subtasks (tests, docs) that depend on step 3
7. REPORT final result to user
```
