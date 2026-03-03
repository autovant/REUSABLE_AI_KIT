---
agent: agent
description: 'Report AI Kit installation and project integration status.'
tools: ["read", "search"]
---

# Kit Status

Show current status of global and local AI Kit setup.

## Check

- Global kit existence:
  - Windows: `%APPDATA%\Code\User\REUSABLE_AI_KIT`
  - macOS: `~/Library/Application Support/Code/User/REUSABLE_AI_KIT`
  - Linux: `~/.config/Code/User/REUSABLE_AI_KIT`
- Bootstrap instruction in the platform-appropriate `Instructions` folder
- Prompt and agent availability in the platform-appropriate `prompts` folder
- Local project integration in `.copilot/` or `.github/copilot-instructions.md`

## Output

- installation type (global/local/both)
- component counts (instructions/agents/prompts/tools)
- memory status
- health checklist
- recommended next action
