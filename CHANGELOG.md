# Changelog

All notable changes to this repository are documented here.

## [3.2.1] - 2026-03-03

### Fixed
- **orchestration.instructions.md** — removed duplicate "Quality Gates" section; merged into single checklist with impact assessment subsection.
- **feature-development.prompt.md** — fixed duplicate step 3 in Completion section.
- **code-templates.md** — replaced outdated `React.FC` pattern with modern plain function components; replaced `Optional[dict]` with `dict | None` for Python templates.
- **code-scaffold SKILL.md** — removed 100+ lines of inline templates that duplicated `code-templates.md`; now references the template file directly (169 → 52 lines).

### Changed
- **terminal-management.instructions.md** — added cross-platform note (PowerShell → bash equivalents).
- **kit-status.prompt.md** — added macOS/Linux kit paths alongside Windows `%APPDATA%`.
- **global-bootstrap.instructions.md** — replaced Windows-only paths with cross-platform path table.

## [3.2.0] - 2026-03-03

### Changed
- **Merged @orchestrator into @aikit** — eliminates redundant double-hop routing. @aikit now handles task decomposition and parallel subagent dispatch directly.
- Added explicit **context conservation thresholds** — delegates to subagents when >10 files involved; prefers subagent summaries over raw file reading.
- Added **plan file persistence** — M+ tasks write structured plans to `plans/<task-name>-plan.md` before execution, creating an auditable trail. @planner also persists plans.
- AGENT-REGISTRY updated: removed orchestrator, added parallel subagent pattern section.
- All cross-references to @orchestrator removed (core-rules, bootstrap, synthesizer, README).

### Removed
- `orchestrator.agent.md` — absorbed into @aikit.

## [3.1.0] - 2026-03-03

### Changed
- **Memory backend migrated from SQLite → DuckDB** — columnar storage, native BM25 full-text search, `RETURNING` for inserts, vectorized ILIKE fallback.
- Memory instructions and prompts (`memory-context`, `memory-save`, `memory-recall`) fully rewritten for DuckDB-specific patterns: BM25 scoring, scoped queries, tags, multi-angle search strategy.
- **All 3 pipelines now start with memory-recall and end with memory-save** — bugfix, feature-development, and code-review pipelines auto-query DuckDB for prior context and persist findings.
- **@aikit is the new primary entry point** — replaces @orchestrator as the default agent users should select.
- Root documentation is now v3-first and minimal to avoid legacy drift.
- Global install flow and prompts are aligned with current frontmatter/tool alias conventions.
- AGENT-REGISTRY updated with @aikit at the top and revised routing decision tree.
- Bootstrap template updated with @aikit default, DuckDB mention, and full prompt/command list.

### Added
- **`@aikit` agent** — primary intelligent entry point that auto-classifies tasks (XS-XL), boosts vague prompts, recalls DuckDB memory for M+ tasks, handles simple tasks directly, and routes complex work to specialists.
- `scripts/install-global.sh` — macOS/Linux global installer mirroring the PS1 workflow.
- VS Code Insiders auto-detection in both installers.
- `_archive/` directory — all pre-v3 root dirs moved here to prevent file confusion.

### Removed
- Obsolete planning artifact: `KIT_IMPROVEMENT_PLAN.md`.
- Legacy-heavy root docs replaced by compatibility shims that point to `v3/` sources.
- SQLite as memory backend (replaced by DuckDB).

## [3.0.0] - 2026-03-03

### Added
- DuckDB-backed global memory utility (`global_memory.py`) for durable recall/search.
- Memory/context instruction and prompts for using persistent memory during large-context workflows.

### Removed
- Obsolete planning artifact: `KIT_IMPROVEMENT_PLAN.md`.
- Legacy-heavy root docs replaced by compatibility shims that point to `v3/` sources.

---

## [2.3.0] - 2026-02-01

- Agent registration and global verification improvements for pre-v3 root-era structure.

## [2.2.0] - 2026-02-01

- Global installation script and bootstrap flow introduced.

## [2.1.0]

- Legacy pre-consolidation toolkit baseline.
