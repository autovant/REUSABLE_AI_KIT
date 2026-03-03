---
agent: agent
description: 'Create and execute an E2E demo test suite with HD video recording, covering full application workflow with real services.'
---

# E2E Demo Pipeline - Full Workflow Test with Video Recording

Create and execute an end-to-end demo test suite that exercises the full application workflow with real services (no mocks), captures HD video and screenshots at every key step, and produces professional demo-quality recordings.

## Phase 0: Discovery (MANDATORY FIRST STEP)

1. Read project README, package.json/pyproject.toml, and test config to identify:
   - **App type**: Web app, API, CLI, etc.
   - **Services**: What needs to run (backend, frontend, database, proxies)
   - **How to start**: Scripts (Start-Dev.ps1, docker-compose, Makefile) or manual commands
   - **Existing tests**: Playwright config, test files, fixtures
   - **Key user flows**: The critical paths through the application
2. Identify the demo narrative: What story does this demo tell? Who is the audience?
3. Document findings before proceeding

## Phase 1: Environment Setup

### 1.1 Start All Services
- **CRITICAL**: Start servers via project scripts or background terminals. NEVER block the VS Code terminal.
- Verify health endpoints for every service
- If any service fails, diagnose and fix before proceeding

### 1.2 Test Data / Fixtures
- Review or create fixture data that tells a realistic story
- Fixtures should use domain-accurate terminology and realistic values
- Each fixture should map to form fields or API inputs in the application
- Store fixtures in a `fixtures/` or `demo-data/` directory alongside the tests

## Phase 2: Build the Demo Test Suite

### 2.1 Playwright Configuration
```typescript
// Key settings for demo recording
{
  headless: false,           // Visible browser for recording
  slowMo: 300,               // Slowed for demo clarity
  video: { mode: 'on', size: { width: 1920, height: 1080 } },
  screenshot: 'on',
  trace: 'on',
  viewport: { width: 1920, height: 1080 },
  timeout: 300000,           // 5 min per test (adjust for your app)
}
```

### 2.2 Test Structure
Structure tests as a narrative arc - each test is a chapter:

| Test | Purpose | Verifications |
|------|---------|---------------|
| 00 | Platform readiness | Services healthy, prerequisites met |
| 01 | Setup / initialization | Create resources, verify initial state |
| 02-N | Core workflow steps | Each major feature/flow as a separate test |
| N+1 | Verification / summary | End state correct, all outputs valid |
| N+2 | Audit / history | Logs, history, provenance verified |

### 2.3 Screenshot Strategy
Capture named screenshots at every key moment using a helper:
```typescript
async function snap(page: Page, name: string, outputDir: string) {
  await page.screenshot({ path: path.join(outputDir, `${name}.png`), fullPage: true });
}
```
Target 30+ screenshots covering: initial state, form fills, running states, completions, error states, final overview.

### 2.4 Console Error Collection
Register a console listener to collect errors. Assert zero real errors (excluding known benign ones like favicon 404, DevTools, third-party scripts).

## Phase 3: Execute

### 3.1 Pre-Run Cleanup
```powershell
# Remove stale results
if (Test-Path "test-results") { Remove-Item -Recurse -Force "test-results" }
if (Test-Path "playwright-report") { Remove-Item -Recurse -Force "playwright-report" }
```

### 3.2 Run
```powershell
npx playwright test --project=<your-project> --reporter=line
```
- Use `--reporter=line` only. Never `--reporter=html` without `open=never` (blocks terminal).
- All tests must pass in a single run. No partial passes.

## Phase 4: Verification

### 4.1 Video Check
- Video file exists and is > 10 MB
- Video duration covers the full test run

### 4.2 Screenshot Gallery
- 30+ screenshots captured
- Every expected screenshot exists per the manifest
- No blank/empty screenshots

### 4.3 Visual Inspection (REQUIRED)
For each screenshot, verify:
- No error dialogs or React error overlays
- No blank screens
- No broken layouts or overlapping elements
- No frozen loading states in completion screenshots
- Consistent branding/styling throughout
- All form fields populated with realistic data (not "test" or "asdf")

### 4.4 Produce Verification Report
```markdown
## Demo Verification Report
**Video:** [filename] ([size] MB)
**Screenshots:** [count] captured, [count] verified
| Screenshot | Status | Notes |
|-----------|--------|-------|
| ... | PASS/FAIL | ... |
```

## Success Criteria

- All tests pass in a single run (exit code 0)
- All services used real backends (no mocks, no stubs)
- HD video recorded (1920x1080 .webm)
- 30+ screenshots captured
- Every screenshot visually verified: zero error dialogs, zero broken layouts
- Console errors: zero (excluding known benign)
- Demo is suitable for presenting to stakeholders

## Constraints

- **Real services only**: No mock responses, no stubbed backends
- **No terminal blocking**: Use project scripts or background terminals for servers
- **Sequential execution**: Tests share state, do not parallelize
- **Professional quality**: The resulting video must be presentation-ready
- **No report auto-open**: `--reporter=line` only
