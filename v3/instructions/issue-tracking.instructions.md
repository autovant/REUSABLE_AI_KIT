---
applyTo: '**'
description: 'Lightweight issue tracking for cross-agent learning'
---

# Issue Tracking

Maintain `memory/shared/issue-tracker.md` to document resolved issues for cross-agent learning.

## When to Log

- Build failures, runtime errors, configuration issues
- Integration problems, performance fixes
- Do NOT log: simple typos, one-off dev environment issues

## Entry Format

### ISS-XXX: [Brief Title]
**Category**: Build | Runtime | Config | Integration | Performance | Testing
**Severity**: Critical | High | Medium | Low
**Symptoms**: What error appeared, when/where
**Root Cause**: Why it happened
**Solution**: What was changed
**Prevention**: How to avoid in future
**Files Changed**: List of files

## Usage

- Before starting work: search tracker for similar issues
- After fixing: add entry with full details
- Update the quick reference table at the top
