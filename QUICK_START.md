# Quick Start — REUSABLE_AI_KIT

## 1. Install globally

**Windows** (PowerShell):
```powershell
git clone https://github.com/autovant/REUSABLE_AI_KIT
cd REUSABLE_AI_KIT
.\scripts\install-global.ps1
```

**macOS / Linux** (bash):
```bash
git clone https://github.com/autovant/REUSABLE_AI_KIT
cd REUSABLE_AI_KIT
chmod +x scripts/install-global.sh
./scripts/install-global.sh
```

The installer:
- Copies the kit to your VS Code User directory (detects Insiders automatically)
- Registers instructions that auto-load in every project
- Installs 14 custom agents + 12+ prompts
- Installs `duckdb` and initializes the memory database

## 2. Use immediately

Open any project in VS Code Copilot Chat and type:
- `/setup-ai-kit` — integrates the kit into the current project
- `/kit-status` — checks that everything is working
- `@architect`, `@debugger`, `@tester`, etc. — switch to specialist agents

## 3. Explore

- Full reference: [`README.md`](README.md)
- Agent catalog: [`AGENT-REGISTRY.md`](AGENT-REGISTRY.md)
- Memory tool: [`tools/README.md`](tools/README.md)

## Uninstall

```powershell
.\scripts\install-global.ps1 -Uninstall   # Windows
./scripts/install-global.sh --uninstall   # macOS/Linux
```
