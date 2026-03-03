---
agent: agent
description: 'Multi-agent code review pipeline: review, security audit, auto-fix minor issues, re-review.'
---

# Code Review Pipeline

Orchestrate thorough code review using reviewer and security auditor agents.

## Pipeline

```
memory-recall -> reviewer -> security-auditor -> [auto-fix if minor] -> reviewer (re-check) -> memory-save
```

## Step 0: Memory Recall

Before reviewing, check DuckDB for known patterns and prior issues in these files:
```bash
python tools/global_memory.py search --query "<files or components under review>" --scope project --namespace issues --limit 5 --format markdown
python tools/global_memory.py search --query "<files or components under review>" --scope project --namespace conventions --limit 3 --format markdown
```
Apply known conventions as review criteria. Flag deviations from stored project standards.

## Step 1: Code Review (@reviewer)

Comprehensive review across 7 dimensions:
- Correctness, security, performance, maintainability, testing, architecture, documentation
- Produce structured findings with severity ratings
- Identify what's good, not just problems

## Step 2: Security Audit (@security-auditor)

Focused security analysis:
- OWASP Top 10 checklist
- Input validation, injection, auth, secrets exposure
- Dependency vulnerabilities
- Produce findings with remediation guidance

## Step 3: Auto-Fix Minor Issues

If the reviewer or auditor found LOW severity issues with clear fixes:
- Unused imports
- Missing null checks
- Simple type errors
- Formatting inconsistencies

Apply these fixes automatically. Do NOT auto-fix:
- Architecture decisions
- Business logic changes
- Security vulnerability fixes (require human review)
- Performance optimizations

## Step 4: Re-Review (@reviewer)

If auto-fixes were applied:
- Quick re-review of the changes
- Confirm fixes are correct
- Final verdict: Approve / Request Changes

## Completion

1. Produce combined review report with all findings
2. Update `memory/shared/issue-tracker.md` with any issues found
3. Save recurring patterns to DuckDB for future reviews:
   ```bash
   python tools/global_memory.py upsert --scope project --namespace conventions --key "<pattern.name>" --title "<convention title>" --content "<what to enforce and why>" --tags "review,<domain>"
   ```
4. Present verdict to user with actionable next steps

## Rules

- Reviewer is read-only in Step 1 (report findings, don't fix)
- Auto-fix only LOW severity with clear, mechanical fixes
- Security findings always require human decision
- If review finds CRITICAL issues, stop and report immediately
