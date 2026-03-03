---
agent: agent
description: 'Systematic multi-phase bug hunt: static analysis, test execution, runtime review, security audit, with documented fixes.'
---

# Comprehensive Bug Hunt & Fix

Systematically identify, fix, and document all bugs, errors, and code quality issues across the entire application.

## Phase 0: Context Loading (MANDATORY FIRST STEP)

1. Read project README, AGENTS.md, or equivalent for architecture and conventions
2. Read `package.json`, `pyproject.toml`, `*.csproj`, or equivalent to identify the full stack
3. Identify: language(s), framework(s), test runner(s), linter(s), build tool(s), database, ports
4. Read any existing issue tracker (IssueTracker.md, memory/shared/issue-tracker.md) to avoid re-fixing known issues
5. Note the current bug number ceiling and continue numbering from there

## Phase 1: Environment Setup & Service Startup

1. Start all services using project scripts (Start-Dev.ps1, docker-compose, Makefile, etc.)
   - **CRITICAL**: Start servers in background/external terminals. Never block the VS Code terminal with a long-running process.
2. Verify all services are healthy (health endpoints, port checks)
3. If any service fails to start, diagnose and fix first - document as a bug

## Phase 2: Static Analysis

Run all configured static analysis and fix every error/warning:

**Detect and run the appropriate tools:**
- Python: `ruff check`, `mypy`, `flake8`, `pylint`
- TypeScript/JavaScript: `tsc --noEmit`, `eslint`, `biome`
- C#: `dotnet build`, analyzer warnings
- Go: `go vet`, `staticcheck`

**Common fix categories:** type errors, unused imports/variables, bare excepts, missing type annotations, import sorting, magic numbers, exception chaining, accessibility violations.

## Phase 3: Test Execution & Failure Analysis

Run all test suites and fix every failure:

- **Unit tests**: Distinguish product bugs (fix source) from test bugs (fix test)
- **Integration tests**: Check service connectivity, database state, API contracts
- **E2E tests**: Use `--reporter=line` (not html) to avoid terminal blocking. Analyze whether failures are UI bugs, API bugs, or test flakiness

## Phase 4: Runtime & Logic Bug Hunting

With services running, perform targeted code review for:

**API Layer:**
- Missing input validation/sanitization
- Wrong HTTP status codes
- Missing error handling (bare try/except, swallowed exceptions)
- N+1 query patterns
- Race conditions in async code
- Missing auth checks

**Service/Business Logic:**
- Timezone-naive datetime usage
- Non-deterministic queries (`.first()` without `.order_by()`)
- Resource leaks (unclosed connections, file handles)
- Unbounded data fetching (missing pagination/limits)

**Frontend:**
- XSS vulnerabilities (`dangerouslySetInnerHTML` without sanitizer)
- Missing error boundaries
- Stale closures in hooks
- Missing loading/error states
- `console.log` left in production code

**Database/Models:**
- Missing indexes on frequently queried columns
- Nullable columns that should be non-nullable
- Missing cascade rules
- Migration gaps

## Phase 5: Security Audit

- Hardcoded secrets/passwords (grep for `password`, `secret`, `api_key`, `token`)
- SQL injection vectors (string concatenation in queries)
- Path traversal in file handlers
- SSRF in URL-accepting endpoints
- Missing or overly permissive CORS
- JWT/session security (expiry, rotation, secure flags)
- Dependency vulnerabilities (`pip-audit`, `npm audit`, `dotnet list package --vulnerable`)

## Fix Implementation Rules

1. **Minimal fix only.** Change the absolute minimum. No unrelated refactoring.
2. **Match existing style.** Follow the codebase's naming and patterns.
3. **Preserve behavior.** Fixes must not break existing functionality.
4. **Type safety.** Add proper types, no `any` escape hatches.
5. **Exception handling.** Specific exception types. Chain with `from e` in Python.
6. **Verify after fixing.** Run `get_errors` after edits. Re-run relevant tests after each phase.

## Documentation

After each phase, append findings to the project's issue tracker (IssueTracker.md or memory/shared/issue-tracker.md):

```markdown
## Bug #XXXX: [Title]
- **File:** `path/to/file.ext`
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW
- **Issue:** What was wrong
- **Fix:** What was changed
- **Impact:** Why it matters
```

## Success Criteria

- All static analysis tools pass with zero errors
- All test suites pass (unit, integration, E2E)
- No hardcoded credentials in codebase
- Issue tracker updated with all new bugs (numbered sequentially)
- All services still healthy after all fixes applied

## Constraints

- Do NOT delete existing issue tracker entries. Append only.
- Do NOT re-fix bugs already documented in previous sessions.
- Do NOT refactor unrelated code. Minimal surgical changes only.
- Do NOT block the VS Code terminal with servers. Use background/external terminals.
- Do NOT skip testing after fixes. Every phase ends with verification.
