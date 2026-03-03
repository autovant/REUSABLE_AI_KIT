---
applyTo: '**'
description: 'Project analysis and quick-start patterns for any codebase'
---

# Project Quick-Start

## Phase 1: Rapid Assessment

Check these files first to identify the project:

| File | Indicates |
|------|-----------|
| package.json | Node.js - check scripts, deps, lockfile type |
| pyproject.toml / requirements.txt | Python - check framework, test runner |
| *.csproj / *.sln | .NET |
| docker-compose.yml | Multi-service - check all services |
| Makefile | Build commands |
| .env.example | Required environment variables |

Identify: language, framework, test runner, linter, database, ports, entry points.

## Phase 2: Common Project Structures

### Backend API
```
src/ (or app/)
  api/ or routes/    - Endpoints
  services/          - Business logic
  models/            - Data models
  utils/             - Helpers
tests/
config/
```

### Frontend SPA
```
src/
  components/        - UI components
  pages/ or views/   - Route pages
  hooks/             - Custom hooks
  stores/            - State management
  utils/             - Helpers
public/
```

### Full-Stack
```
backend/ or server/
frontend/ or web/
shared/ or common/
docker-compose.yml
```

## Phase 3: Validate Environment

1. Install dependencies (detect package manager from lockfile)
2. Copy `.env.example` to `.env` if missing
3. Build: does it compile without errors?
4. Lint: do linters pass?
5. Test: do tests run?
6. Start: can the app start? (Use background terminal)

## Document Findings

Write to `memory/shared/conventions.md`:
- Stack, framework, test runner, linter
- Port numbers for each service
- Build/test/start commands
- Naming conventions observed
