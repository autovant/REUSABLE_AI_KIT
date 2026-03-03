---
name: git-workflow
description: Branch naming, commit message standards, PR creation, conflict resolution, and changelog updates. Invoke when committing, branching, or creating pull requests.
---

# Git Workflow Skill

## When This Skill Activates

- User mentions: commit, branch, PR, pull request, merge, changelog, release, git
- Files staged for commit
- Working on a feature branch

## Branch Naming Convention

```
<type>/<ticket>-<short-description>
```

| Type | Usage |
|------|-------|
| `feature/` | New functionality |
| `bugfix/` | Bug repair |
| `hotfix/` | Urgent production fix |
| `chore/` | Tooling, deps, config |
| `refactor/` | Code improvement without behavior change |

Examples: `feature/PROJ-123-user-auth`, `bugfix/PROJ-456-null-pointer-login`

## Commit Message Format (Conventional Commits)

```
<type>(<scope>): <description>

[optional body]

[optional footer: BREAKING CHANGE, Refs, Closes]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

**Rules**:
- Subject line: imperative mood, lowercase, no period, max 72 chars
- Body: wrap at 80 chars, explain WHY not WHAT
- Footer: reference tickets (`Refs: PROJ-123`), note breaking changes

**Examples**:
```
feat(auth): add JWT refresh token rotation

Implements automatic token refresh when access token expires within 5 minutes.
Uses sliding window to avoid simultaneous refresh requests.

Refs: PROJ-123
```

```
fix(api): handle null response from payment gateway

The gateway returns null instead of error object for declined cards.
Added null check with appropriate error mapping.

Closes: PROJ-456
```

## PR Creation Checklist

Before creating a PR:
1. Rebase on latest target branch (no merge commits)
2. All tests pass locally
3. No lint/type errors
4. Commit history is clean (squash WIP commits)
5. Branch name follows convention

**PR Title**: Same format as commit subject (`feat(scope): description`)

**PR Description Template**:
```markdown
## What
[Brief description of the change]

## Why
[Business context or link to ticket]

## How
[Technical approach, key decisions]

## Testing
[How it was tested, what to verify]

## Screenshots
[If UI change, before/after]
```

## Changelog Update

When a release-worthy change is merged, update CHANGELOG.md:

```markdown
## [Unreleased]

### Added
- Description of new feature (#PR)

### Changed
- Description of change (#PR)

### Fixed
- Description of fix (#PR)

### Removed
- Description of removal (#PR)
```

Follow [Keep a Changelog](https://keepachangelog.com/) format.

## Conflict Resolution

1. `git fetch origin && git rebase origin/main` (or target branch)
2. Resolve conflicts file by file - never accept all incoming or all current blindly
3. After resolution: run tests, verify behavior
4. `git rebase --continue` and force-push to feature branch ONLY

## Terminal Commands Reference

```powershell
# Create branch
git checkout -b feature/PROJ-123-description

# Stage and commit
git add -p                       # Interactive staging (review each hunk)
git commit -m "feat(scope): description"

# Rebase before PR
git fetch origin
git rebase origin/main

# Squash WIP commits
git rebase -i HEAD~3             # Interactive rebase last 3 commits

# Push feature branch
git push -u origin feature/PROJ-123-description
```
