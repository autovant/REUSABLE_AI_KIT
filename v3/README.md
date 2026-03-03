# Reusable AI Kit v3

A self-contained toolkit of agents, instructions, skills, prompts, and shared memory for VS Code GitHub Copilot. Drop it into any project workspace to get a coordinated multi-agent development system.

## What's In the Box

| Component | Count | Purpose |
|-----------|-------|---------|
| **Agents** | 14 | Primary @aikit agent + 13 specialist agents with scoped tools and expertise |
| **Instructions** | 11 | Consolidated rules with `applyTo` scoping |
| **Skills** | 5 | Reusable procedural knowledge (git, env setup, scaffolding, audits, project analysis) |
| **Tools** | 5 | Universal Python scripts (+ DuckDB-backed global memory) |
| **Prompts** | 9 | Ready-to-run task prompts (workflows, setup, status, memory save/recall) |
| **Pipelines** | 3 | Multi-agent workflow orchestrations (feature, bugfix, review) |
| **Templates** | 3 | Code starter templates + issue tracker + global bootstrap |
| **Memory** | 4 | Shared session log, context, conventions, and issue tracker |

## Quick Start

### 1. Install

Copy the `v3/` folder into your project's `.github/` or root directory:

```powershell
# Option A: Copy into .github (recommended for teams)
Copy-Item -Recurse v3\* .github\

# Option B: Copy to workspace root
Copy-Item -Recurse v3\* .\
```

### 2. Use Agents

Select **`@aikit`** as your default agent. It auto-classifies tasks, boosts vague prompts, recalls DuckDB memory, and routes complex work to specialists:

```
@aikit Build a user authentication feature with JWT tokens
@aikit Fix the login page 500 error
@aikit Review the changes in src/auth/
```

You can also invoke specialists directly:

```
@debugger The login page throws a 500 error after form submission
@reviewer Review the changes in src/auth/
@tester Write tests for the PaymentService class
```

### 3. Use Prompts

Open any `.prompt.md` file and run it as a Copilot prompt:

- **boost-prompt** — Interactive prompt refinement wizard
- **comprehensive-bug-hunt** — Full-app bug detection and fixing
- **ui-ux-audit** — Playwright-based UI/UX analysis
- **e2e-demo-pipeline** — HD video demo recording with real services
- **memory-save** — Persist durable learnings into DuckDB memory
- **memory-recall** — Retrieve prior context before large tasks
- **setup-ai-kit / update-ai-kit / kit-status** — setup and lifecycle helpers

### 4. Use Pipelines

Pipelines orchestrate multiple agents in sequence:

- **feature-development** — memory-recall → planner → architect → implement → tester → reviewer → memory-save
- **bugfix** — memory-recall → investigate → debugger → fix → tester → reviewer → memory-save
- **code-review** — memory-recall → reviewer → security-auditor → auto-fix → re-review → memory-save

### 5. Use Analysis Tools

Run the Python tools from any project directory:

```bash
# Scan dependencies for known vulnerabilities
python tools/vuln_scan.py --path . --format markdown --severity high

# Check license compliance (flags copyleft licenses by default)
python tools/license_check.py --path . --format markdown

# Validate dev environment health
python tools/env_health.py --path . --format markdown

# Collect code metrics (LOC, complexity, duplicates, TODOs)
python tools/code_metrics.py --path . --format markdown --top 15

# Persist and query durable memory
python tools/global_memory.py init
python tools/global_memory.py search --query "auth timeout" --limit 10 --format markdown
```

All tools require only Python 3.8+ stdlib — no pip install needed.

## Directory Structure

```
v3/
├── AGENT-REGISTRY.md              # Agent catalog with routing decision tree
├── README.md                       # This file
├── agents/                         # 14 agents (@aikit + 13 specialists)
│   ├── aikit.agent.md              # Primary entry point — classify, boost, decompose, parallel subagents
│   ├── synthesizer.agent.md        # Quality gate for multi-agent work
│   ├── frontend-engineer.agent.md  # React, CSS, accessibility
│   ├── backend-engineer.agent.md   # API, database, auth
│   ├── investigator.agent.md       # Cross-layer troubleshooting
│   ├── janitor.agent.md            # Tech debt + cleanup
│   ├── debugger.agent.md           # Scientific debugging
│   ├── reviewer.agent.md           # Code review (read-only)
│   ├── architect.agent.md          # System design + ADRs
│   ├── tester.agent.md             # Test generation
│   ├── planner.agent.md            # Task breakdown
│   ├── refactorer.agent.md         # Safe restructuring
│   ├── documenter.agent.md         # Documentation
│   └── security-auditor.agent.md   # OWASP + vulnerability detection
├── instructions/                   # 11 scoped instruction files
│   ├── 000-core-rules.instructions.md      # Universal rules (applyTo: **)
│   ├── debugging.instructions.md           # Debugging methodology
│   ├── documentation.instructions.md       # Doc sync (applyTo: *.md)
│   ├── domain-backend.instructions.md      # Backend patterns (applyTo: *.py, etc.)
│   ├── domain-frontend.instructions.md     # Frontend patterns (applyTo: *.tsx, etc.)
│   ├── issue-tracking.instructions.md      # Issue tracking format
│   ├── memory-context.instructions.md      # Persistent memory usage and large-context strategy
│   ├── orchestration.instructions.md       # Agent coordination
│   ├── project-quickstart.instructions.md  # Project analysis
│   ├── terminal-management.instructions.md # Terminal safety
│   └── testing.instructions.md             # Testing standards (applyTo: *.test.*)
├── skills/                         # 5 reusable skills
│   ├── git-workflow/SKILL.md       # Branch, commit, PR conventions
│   ├── environment-setup/SKILL.md  # Auto-detect + install + validate
│   ├── code-scaffold/SKILL.md      # Generate files matching conventions
│   ├── dependency-audit/SKILL.md   # Vulnerability + outdated checks
│   └── project-analysis/SKILL.md   # How to use the Python analysis tools
├── prompts/                        # 9 task prompts + 3 pipelines
│   ├── boost-prompt.prompt.md
│   ├── comprehensive-bug-hunt.prompt.md
│   ├── ui-ux-audit.prompt.md
│   ├── e2e-demo-pipeline.prompt.md
│   ├── memory-save.prompt.md
│   ├── memory-recall.prompt.md
│   ├── setup-ai-kit.prompt.md
│   ├── update-ai-kit.prompt.md
│   ├── kit-status.prompt.md
│   └── pipelines/
│       ├── feature-development.prompt.md
│       ├── bugfix.prompt.md
│       └── code-review.prompt.md
├── tools/                          # Universal Python analysis tools
│   ├── README.md                   # Tool documentation
│   ├── vuln_scan.py                # Dependency vulnerability scanner
│   ├── license_check.py            # License compliance checker
│   ├── env_health.py               # Environment health validator
│   ├── code_metrics.py             # LOC, complexity, duplicates, TODOs
│   └── global_memory.py            # DuckDB-backed durable memory + BM25 search
├── templates/                      # Starter templates
│   ├── code-templates.md           # React, Express, FastAPI, Django, .NET, tests
│   ├── issue-tracker.md            # Empty tracker template
│   └── global-bootstrap.instructions.md
└── memory/                         # Shared cross-agent memory
    └── shared/
        ├── session-log.md          # Append-only work log
        ├── shared-context.md       # Cross-agent findings
        ├── conventions.md          # Project conventions template
        └── issue-tracker.md        # Reusable issue/fix log
```

## Architecture

### Agent Tiers

**Entry Point** -- `@aikit` classifies tasks, handles simple work directly, and decomposes complex tasks into parallel subagent calls. `@synthesizer` reviews multi-agent output before it reaches the user.

**Domain** — `@frontend-engineer`, `@backend-engineer`, `@investigator`, `@janitor` handle domain-specific implementation work.

**Methodology** — `@debugger`, `@reviewer`, `@architect`, `@tester`, `@planner`, `@refactorer`, `@documenter`, `@security-auditor` apply specific methodologies regardless of domain.

### Instruction Scoping

Instructions use `applyTo` frontmatter to only load when relevant:
- `000-core-rules` loads for all files (`**`)
- `domain-frontend` loads only for `.tsx`, `.jsx`, `.css`, `.html`, etc.
- `domain-backend` loads only for `.py`, `.cs`, routes, controllers, etc.
- `testing` loads only for test files (`*.spec.*`, `*.test.*`, `conftest.py`, etc.)

This minimizes context token usage — agents only see rules relevant to the files they're working on.

### Shared Memory

All agents read and write to `memory/shared/`:
- **session-log.md** — What was done in each session (read at start, append at end)
- **shared-context.md** — Discoveries during the current session (architecture notes, conventions, decisions)
- **conventions.md** — Project patterns detected (naming, file organization, styling, testing, API patterns)

This enables cross-agent learning — one agent's discovery benefits all subsequent agents.

## Customization

### Add a New Agent

Create `agents/your-agent.agent.md` with frontmatter:

```yaml
---
description: What this agent does (one sentence)
tools: ["read", "edit", "search", "execute"]  # Tool aliases only
---
```

### Add a New Skill

Create `skills/your-skill/SKILL.md` with frontmatter:

```yaml
---
name: your-skill
description: When and how to use this skill
---
```

### Add a New Prompt

Create `prompts/your-prompt.prompt.md` with frontmatter:

```yaml
---
agent: agent
description: What this prompt does
---
```

### Add a New Instruction

Create `instructions/your-topic.instructions.md` with frontmatter:

```yaml
---
applyTo: '**/*.py'  # Scope to relevant files
description: What rules this contains
---
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Tool aliases (`read`, `edit`, `search`, `execute`) over individual tool names | Avoids "Unknown tool" lint warnings, more portable |
| `agent: agent` in prompt frontmatter | `mode: agent` is deprecated |
| 10 consolidated instructions (down from 30) | ~75% context token reduction, scoped loading |
| Shared memory files | Cross-agent knowledge transfer without re-discovery |
| DuckDB global memory (`global_memory.py`) | Durable recall/search for large-context and multi-session work |
| @aikit + @synthesizer pattern | Separation of routing from quality review |
| Skills as `SKILL.md` in named directories | VS Code recognizes this structure natively |
