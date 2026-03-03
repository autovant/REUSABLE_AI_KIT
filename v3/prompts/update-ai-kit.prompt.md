---
agent: agent
description: 'Update globally installed REUSABLE_AI_KIT and report version-level changes.'
tools: ["read", "search", "execute"]
---

# Update AI Kit

Update `%APPDATA%\Code\User\REUSABLE_AI_KIT` safely.

## Steps

1. Read current version/changelog from the installed kit.
2. Check for updates from source repository if git remote exists.
3. Apply update (`git pull` or reinstall script).
4. Report:
   - previous version
   - new version
   - notable changes
   - any manual follow-up required
