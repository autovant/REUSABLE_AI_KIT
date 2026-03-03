# REUSABLE_AI_KIT

> **Canonical version: `v3/`** — everything else in this repo is archive or scripts.

A composable AI engineering toolkit for GitHub Copilot. One global install gives you a consistent agent roster, smart instructions, persistent memory, and quality-gate tools in every VS Code project — without copying anything per-project.

---

## Installation

### Windows
```powershell
.\scripts\install-global.ps1
```
Detects VS Code Insiders automatically. Requires PowerShell 5+.

### macOS / Linux
```bash
chmod +x scripts/install-global.sh
./scripts/install-global.sh
```
Requires bash + rsync (both standard on macOS/Linux).

**Uninstall:**
```powershell
.\scripts\install-global.ps1 -Uninstall   # Windows
./scripts/install-global.sh --uninstall   # macOS/Linux
```

---

## What you get after install

| Component | Count | What it does |
|-----------|-------|--------------|
| Instructions | 11 | Auto-loaded rules, domain guides, memory strategy |
| Agents | 14 | Specialist modes: architect, debugger, tester, etc. |
| Prompts | 12+ | Pipelines: bug hunt, feature dev, code review, memory |
| Tools | 5 | Python scripts: vuln scan, metrics, env health, memory |
| Memory | DuckDB | Persistent cross-session recall with BM25 search |

---

## Getting started (after install)

1. Open any project in VS Code
2. Type `/setup-ai-kit` in Copilot Chat
3. The kit is now active for that project

Or start immediately — the global bootstrap auto-loads for all projects.

---

## What's in this repo

```
v3/                 ← CANONICAL: everything you need
  agents/           ← 14 specialist agents
  instructions/     ← 11 instruction files
  prompts/          ← 12 prompts + 3 pipeline prompts
  skills/           ← 5 skill guides
  templates/        ← bootstrap + issue tracker templates
  tools/            ← 5 Python analysis/memory scripts
  memory/           ← shared memory files + DuckDB store
scripts/
  install-global.ps1  ← Windows installer
  install-global.sh   ← macOS/Linux installer
_archive/           ← legacy pre-v3 files (not used)
```

---

## Memory system

The kit ships a DuckDB-backed memory tool for durable cross-session recall:

```bash
# One-time setup (installer does this automatically)
pip install duckdb
python v3/tools/global_memory.py init

# Save a fact
python v3/tools/global_memory.py upsert \
  --scope global --namespace conventions \
  --key python-style --title "Python Style" \
  --content "Use type hints for all public APIs"

# Search
python v3/tools/global_memory.py search --query "type hints" --format markdown
```

See [`v3/tools/README.md`](v3/tools/README.md) and [`v3/instructions/memory-context.instructions.md`](v3/instructions/memory-context.instructions.md).

---

## Full docs

→ [`v3/README.md`](v3/README.md) — complete component reference
