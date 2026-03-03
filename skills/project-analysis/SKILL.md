# Project Analysis Tools Skill

This skill teaches agents how to use the universal Python analysis tools bundled with the kit.
All tools are **zero-dependency** (Python 3.8+ stdlib only), auto-detect project ecosystems,
and output structured JSON or Markdown for agent consumption.

---

## Available Tools

| Tool | Script | Purpose |
|------|--------|---------|
| Vulnerability Scanner | `tools/vuln_scan.py` | Finds known CVEs in project dependencies |
| License Checker | `tools/license_check.py` | Audits dependency licenses against allow/deny lists |
| Environment Validator | `tools/env_health.py` | Validates dev environment readiness |
| Code Metrics | `tools/code_metrics.py` | LOC, complexity, duplicates, TODO density |

---

## When to Use Each Tool

### vuln_scan.py
**Trigger**: User asks about security, vulnerabilities, dependency audit, CVE check, or supply-chain risk.

```bash
python tools/vuln_scan.py --path . --format json
python tools/vuln_scan.py --path . --format markdown --severity high
```

- Requires ecosystem-specific audit tools installed (pip-audit, npm, dotnet, etc.)
- Outputs list of vulnerable packages with severity, fix versions, advisory links
- Use `--severity high` to filter noise

### license_check.py
**Trigger**: User asks about license compliance, open-source risk, legal review, or dependency licensing.

```bash
python tools/license_check.py --path . --format json --policy permissive
python tools/license_check.py --path . --format markdown --policy custom --deny "GPL-3.0,AGPL-3.0"
```

- Policies: `permissive` (default - flags copyleft), `copyleft` (denies GPL family), `custom`, `none`
- Exit code 1 if any denied licenses found
- Use `--allow` and `--deny` with `--policy custom` for fine-grained control

### env_health.py
**Trigger**: User asks about setup issues, environment problems, "it works on my machine", onboarding, or project setup validation.

```bash
python tools/env_health.py --path . --format json
python tools/env_health.py --path . --format markdown
python tools/env_health.py --path . --config checks.json
```

- Auto-detects required tools from project manifests (package.json, requirements.txt, etc.)
- Checks: CLI tool presence + version, env vars, file existence, port availability, disk space
- Supply a custom `--config checks.json` to override auto-detection
- Custom config format:
  ```json
  [
    {"type": "tool", "name": "node", "version_cmd": ["node", "--version"], "min_version": "18.0"},
    {"type": "env", "name": "DATABASE_URL"},
    {"type": "file", "path": ".env"},
    {"type": "port", "port": 3000},
    {"type": "disk", "min_gb": 2.0}
  ]
  ```

### code_metrics.py
**Trigger**: User asks for code overview, codebase analysis, complexity report, LOC count, duplicate detection, or tech debt assessment.

```bash
python tools/code_metrics.py --path . --format json
python tools/code_metrics.py --path . --format markdown --top 20
python tools/code_metrics.py --path . --exclude "test,docs,migrations"
```

- Auto-detects 40+ languages by file extension
- Python files get cyclomatic complexity analysis per function
- Detects exact and near-duplicate files (shared code chunks)
- Scans for TODO/FIXME/HACK/XXX comments
- Use `--top N` to control how many largest files / hotspots to show

---

## Integration Patterns

### Chain: Full Project Audit
Run all tools in sequence for a comprehensive project health picture:

```bash
python tools/env_health.py --path . --format markdown
python tools/vuln_scan.py --path . --format markdown
python tools/license_check.py --path . --format markdown
python tools/code_metrics.py --path . --format markdown
```

### Parse JSON for Decision-Making
When an agent needs to make decisions based on tool output, use JSON format and parse:

```bash
python tools/vuln_scan.py --path . --format json
```

Then check `summary.total_vulnerabilities` to decide next steps.

### Pre-PR Quality Gate
Before creating a pull request, run:
1. `code_metrics.py` - check no high-complexity functions added
2. `vuln_scan.py` - ensure no new vulnerabilities introduced
3. `license_check.py` - verify all new deps have acceptable licenses

---

## Output Formats

All tools support `--format json` (default) and `--format markdown`.

- **JSON**: Best for agent consumption and programmatic decision-making
- **Markdown**: Best for presenting results to the user or including in PR descriptions

---

## Ecosystem Detection

All tools auto-detect ecosystems by looking for manifest files:

| Ecosystem | Detected By |
|-----------|-------------|
| Python | `requirements.txt`, `Pipfile`, `pyproject.toml`, `setup.py` |
| Node.js | `package.json` |
| .NET | `*.csproj`, `*.fsproj`, `*.sln` |
| Go | `go.mod` |
| Ruby | `Gemfile` |
| Rust | `Cargo.toml` |
| Terraform | `*.tf` |
