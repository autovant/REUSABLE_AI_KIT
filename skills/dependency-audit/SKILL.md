---
name: dependency-audit
description: Check for vulnerabilities, outdated packages, license compliance, and suggest safe upgrades. Invoke when auditing dependencies or updating packages.
---

# Dependency Audit Skill

## When This Skill Activates

- User says: audit, dependencies, vulnerabilities, outdated, upgrade, update packages, security scan
- Starting work on a project after a period of inactivity
- Before a release or deployment

## Step 1: Detect Package Ecosystem

| File | Ecosystem | Audit Command | Outdated Command |
|------|-----------|---------------|-----------------|
| `package.json` | npm | `npm audit` | `npm outdated` |
| `yarn.lock` | yarn | `yarn audit` | `yarn outdated` |
| `pnpm-lock.yaml` | pnpm | `pnpm audit` | `pnpm outdated` |
| `requirements.txt` / `pyproject.toml` | pip | `pip-audit` | `pip list --outdated` |
| `Cargo.toml` | cargo | `cargo audit` | `cargo outdated` |
| `go.mod` | go | `govulncheck ./...` | `go list -m -u all` |
| `*.csproj` | dotnet | `dotnet list package --vulnerable` | `dotnet list package --outdated` |
| `Gemfile` | bundler | `bundle audit` | `bundle outdated` |

## Step 2: Run Vulnerability Scan

```powershell
# Node.js
npm audit --json | ConvertFrom-Json

# Python (install pip-audit if missing)
pip install pip-audit 2>$null
pip-audit --format=json

# .NET
dotnet list package --vulnerable --format json
```

**Categorize findings by severity:**

| Severity | Action |
|----------|--------|
| Critical | Fix immediately. Block deployment. |
| High | Fix before next release. |
| Moderate | Plan fix within sprint. |
| Low | Track, fix opportunistically. |

## Step 3: Check for Outdated Packages

```powershell
# Node.js
npm outdated

# Python
pip list --outdated --format=json
```

**Categorize updates:**

| Type | Risk | Approach |
|------|------|----------|
| Patch (1.2.3 -> 1.2.4) | Low | Auto-update, run tests |
| Minor (1.2.3 -> 1.3.0) | Medium | Update, review changelog, run tests |
| Major (1.2.3 -> 2.0.0) | High | Research breaking changes, plan migration |

## Step 4: Safe Upgrade Process

For each update:

1. **Read the changelog** for breaking changes
2. **Update one package at a time** (or group related packages)
3. **Run the full test suite** after each update
4. **Check for type errors** (`tsc --noEmit` / `mypy`)
5. **Spot-check the app** if tests are sparse

```powershell
# Node.js - update one package
npm install <package>@latest

# Python - update one package
pip install --upgrade <package>
pip freeze > requirements.txt  # or: pip-compile

# .NET
dotnet add package <Package> --version <latest>
```

**Never run `npm update` or `pip install --upgrade` on everything at once.** Update incrementally.

## Step 5: License Compliance

```powershell
# Node.js
npx license-checker --summary

# Python
pip install pip-licenses
pip-licenses --format=table
```

**Flag these licenses for legal review:**
- GPL, AGPL (copyleft - may require source disclosure)
- SSPL (Server Side Public License)
- Any "Unknown" or missing license

**Generally safe:**
- MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, Unlicense

## Step 6: Report

Output a summary:

```markdown
## Dependency Audit Report - [Date]

### Vulnerabilities
| Package | Severity | Current | Fixed In | Action |
|---------|----------|---------|----------|--------|
| express | High | 4.17.1 | 4.18.2 | Upgrade |

### Outdated (Major)
| Package | Current | Latest | Breaking Changes |
|---------|---------|--------|-----------------|
| react | 17.0.2 | 18.2.0 | Concurrent mode, new root API |

### License Concerns
| Package | License | Risk |
|---------|---------|------|
| some-lib | GPL-3.0 | Copyleft - legal review needed |

### Recommended Actions
1. [Critical] Upgrade express to 4.18.2 (security fix)
2. [High] Plan React 18 migration (major version)
3. [Info] Review GPL dependency with legal team
```

## Rules

- Never auto-upgrade major versions without checking breaking changes
- Always run tests after any upgrade
- Keep lockfiles committed (package-lock.json, yarn.lock, etc.)
- Document any dependency pins with a comment explaining why
