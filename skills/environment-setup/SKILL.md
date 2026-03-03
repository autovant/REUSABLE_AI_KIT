---
name: environment-setup
description: Auto-detect project type, install dependencies, validate configuration, and verify the development environment is working. Invoke when starting work on a new or existing project.
---

# Environment Setup Skill

## When This Skill Activates

- User opens a new project or workspace
- User says: setup, install, configure, environment, deps, dependencies
- Build or start commands fail due to missing dependencies
- New team member onboarding

## Step 1: Detect Project Stack

Read the project root to identify the stack. Check for these files in order:

| File | Stack | Package Manager |
|------|-------|----------------|
| `package.json` | Node.js / JavaScript / TypeScript | npm, yarn, pnpm (check lockfiles) |
| `pyproject.toml` | Python (modern) | pip, poetry, pdm, uv |
| `requirements.txt` | Python (legacy) | pip |
| `*.csproj` / `*.sln` | .NET / C# | dotnet |
| `go.mod` | Go | go mod |
| `Cargo.toml` | Rust | cargo |
| `Gemfile` | Ruby | bundler |
| `composer.json` | PHP | composer |
| `docker-compose.yml` | Multi-service | docker compose |
| `Makefile` | Generic | make |

**Also detect**:
- Framework: React, Next.js, Vue, Nuxt, Angular, FastAPI, Django, Flask, ASP.NET, Express, etc.
- Test runner: pytest, jest, vitest, playwright, cypress, xunit, nunit
- Linter: eslint, biome, ruff, flake8, pylint
- Database: PostgreSQL, MySQL, SQLite, MongoDB (check docker-compose, .env, config files)
- Ports: What ports do services run on? Check scripts, config, docker-compose.

## Step 2: Install Dependencies

### Node.js
```powershell
# Detect package manager from lockfile
if (Test-Path "pnpm-lock.yaml") { pnpm install }
elseif (Test-Path "yarn.lock") { yarn install }
else { npm install }
```

### Python
```powershell
# Create venv if missing
if (-not (Test-Path ".venv")) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1

# Install deps
if (Test-Path "pyproject.toml") { pip install -e ".[dev]" }
elseif (Test-Path "requirements.txt") { pip install -r requirements.txt }
if (Test-Path "requirements-dev.txt") { pip install -r requirements-dev.txt }
```

### .NET
```powershell
dotnet restore
dotnet build
```

### Docker
```powershell
docker compose up -d
docker compose ps   # Verify all services healthy
```

## Step 3: Environment Configuration

1. Check for `.env.example` or `.env.template` - copy to `.env` if `.env` doesn't exist
2. Check for required environment variables and warn about any that are missing
3. Check database connectivity if a database is configured
4. Check for required external tools (Docker, Node, Python version, etc.)

```powershell
# Check .env
if ((Test-Path ".env.example") -and -not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Warning "Created .env from .env.example - review and update values"
}
```

## Step 4: Validate Setup

Run validation checks in order:

1. **Build**: Does the project compile/build without errors?
2. **Lint**: Do linters pass?
3. **Tests**: Do tests run (at least smoke test)?
4. **Start**: Can the app/server start? (Use background terminal - never block VS Code)

```powershell
# Node.js validation
npm run build          # or: npx tsc --noEmit
npm run lint           # or: npx eslint src/
npm test -- --watchAll=false

# Python validation
ruff check .
python -m pytest --co -q   # Collect tests (don't run)
```

## Step 5: Document Findings

Write setup results to `shared/shared-context.md` (if using AI kit) or output to chat:

```markdown
## Environment Setup - [Project Name]
- **Stack**: [e.g., React 18 + TypeScript + Vite]
- **Backend**: [e.g., Python 3.12 + FastAPI + PostgreSQL]
- **Package Manager**: [npm/yarn/pnpm/pip/poetry]
- **Ports**: Frontend :5173, Backend :8001, DB :5432
- **Test Runner**: Vitest (unit), Playwright (E2E)
- **Linter**: ESLint + Biome (frontend), Ruff (backend)
- **Status**: All checks passed / [list any issues]
```

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `node_modules` missing | Run the detected package manager install |
| Python venv not activated | `.\.venv\Scripts\Activate.ps1` |
| Port already in use | `Get-NetTCPConnection -LocalPort <port>` then kill the process |
| Docker not running | Start Docker Desktop, wait for daemon |
| Database connection refused | Check docker-compose, verify port, check credentials in .env |
| Missing system dependency | Check README for prerequisites |
