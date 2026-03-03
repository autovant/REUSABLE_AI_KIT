# Python Analysis Tools

Lightweight, zero-dependency Python scripts that work in any environment.
Every tool auto-detects the project ecosystem and outputs structured JSON or Markdown.

## Tools

| Script | Purpose | Key Flags |
|--------|---------|-----------|
| `vuln_scan.py` | Dependency vulnerability scanner | `--severity`, `--format` |
| `license_check.py` | License compliance checker | `--policy`, `--allow`, `--deny` |
| `env_health.py` | Environment health validator | `--config`, `--format` |
| `code_metrics.py` | LOC, complexity, duplicates, TODOs | `--exclude`, `--top` |
| `global_memory.py` | DuckDB-backed durable memory store + BM25 search | `upsert`, `append`, `search`, `recent` |

## Quick Start

```bash
# From any project root:
python <kit_path>/tools/vuln_scan.py --path . --format markdown
python <kit_path>/tools/license_check.py --path . --format json
python <kit_path>/tools/env_health.py --path . --format markdown
python <kit_path>/tools/code_metrics.py --path . --format markdown --top 15

# Persistent memory — requires: pip install duckdb
python <kit_path>/tools/global_memory.py init
python <kit_path>/tools/global_memory.py upsert --scope global --namespace conventions --key python-style --title "Python Style" --content "Use type hints for all public APIs"
python <kit_path>/tools/global_memory.py search --query "python style" --limit 5 --format markdown
```

## Requirements

- **Python 3.8+** (stdlib only for all tools except `global_memory.py`)
- `global_memory.py`: requires `pip install duckdb` (single native library, ~30 MB)
- For `vuln_scan.py`: the ecosystem audit tool must be installed separately
  (e.g., `pip install pip-audit` for Python projects, `npm` for Node projects)

## Backend: DuckDB

`global_memory.py` uses **DuckDB** as its storage engine.

- Columnar storage + SIMD vectorized execution — faster than SQLite for analytics
- Native BM25 full-text search via the `fts` extension (auto-installed on first use)
- Falls back to ILIKE vectorized scan if FTS is unavailable
- Single `.duckdb` file — portable, no server required
- Requires: `pip install duckdb`

## Output Formats

- `--format json` (default) — structured data for agent consumption
- `--format markdown` — human-readable tables for PR descriptions or user display

## Common Patterns

```bash
# Full project audit
python tools/env_health.py --path .
python tools/vuln_scan.py --path . --severity high
python tools/license_check.py --path . --policy permissive
python tools/code_metrics.py --path . --top 20

# Pre-PR quality gate
python tools/code_metrics.py --path . --format json  # check complexity
python tools/vuln_scan.py --path . --format json       # check vulns
python tools/license_check.py --path . --format json    # check licenses

# Session close-out memory capture
python tools/global_memory.py append --scope session --namespace sessions --title "Session summary" --content "Fixed auth timeout and added regression test"
```
