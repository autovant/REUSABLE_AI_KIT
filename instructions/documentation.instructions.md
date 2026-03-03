---
applyTo: '**/*.md,**/docs/**'
description: 'Keep documentation in sync with code changes'
---

# Documentation Sync

When code changes, update related docs in the same commit.

## Trigger Map

| Code Changed | Check These Docs |
|---|---|
| Routes, endpoints | API docs, OpenAPI spec |
| Dependencies (package.json, requirements.txt) | README.md, setup guides |
| Environment variables | .env.example, setup docs |
| Database models | Data model docs, ERD |
| CLI commands | CLI reference |
| Config options | Configuration docs |

## After Code Changes, Verify

- [ ] README.md reflects current setup steps
- [ ] API docs match actual endpoints
- [ ] Config examples are accurate
- [ ] CHANGELOG.md includes the change

## Architecture Diagrams

Use Mermaid (not ASCII art). Keep diagrams focused - one concept per diagram. Update when services, data flows, or integrations change.
