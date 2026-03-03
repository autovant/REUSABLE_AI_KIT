---
agent: agent
description: 'Multi-agent feature development pipeline: plan, architect, implement, test, review.'
---

# Feature Development Pipeline

Orchestrate a complete feature implementation using specialized agents in sequence.

## Pipeline

```
memory-recall -> planner -> architect (if needed) -> implement -> tester -> reviewer -> memory-save
```

## Step 0: Memory Recall

Before planning, check DuckDB for prior context on this feature area:
```bash
python tools/global_memory.py search --query "<feature domain keywords>" --scope project --limit 5 --format markdown
python tools/global_memory.py search --query "<feature domain keywords>" --scope global --namespace conventions --limit 3 --format markdown
python tools/global_memory.py recent --namespace commands --limit 5 --format markdown
```
Apply known conventions, architecture decisions, and verified commands.

## Step 1: Plan (@planner)

Break the feature into actionable tasks:
- Clarify requirements and success criteria
- Decompose into phases and sized tasks
- Map dependencies
- Identify risks

## Step 2: Architect (@architect) - If Needed

Skip this step for small features that fit within existing patterns. Invoke architect when:
- New components or services are needed
- API contracts must be designed
- Database schema changes required
- Technology choices needed

## Step 3: Implement

For each task from the plan:
- Read existing code to understand conventions
- Implement the change following project patterns
- Write the code, verify with `get_errors`
- Update `memory/shared/session-log.md` with what was done

## Step 4: Test (@tester)

Generate and run tests for the new feature:
- Unit tests for business logic
- Integration tests for API/service interactions
- E2E tests for critical user flows
- Verify all existing tests still pass

## Step 5: Review (@reviewer)

Final quality gate:
- Code review across all 7 dimensions
- Security check
- Architecture compliance
- Test coverage assessment

## Completion

After the pipeline completes:
1. Update `memory/shared/session-log.md` with feature summary
2. Update `memory/shared/issue-tracker.md` if any issues were found/fixed
3. Save conventions and decisions to DuckDB:
   ```bash
   python tools/global_memory.py upsert --scope project --namespace architecture --key "<component.decision>" --title "<decision title>" --content "<what was decided and why>" --tags "<domain,component>"
   ```
4. Report to user: what was built, key decisions, test results, open items

## Rules

- Each step must complete successfully before proceeding to the next
- If any step reveals a problem, fix it before moving forward
- The user can skip steps (e.g., "skip planning, just implement")
- Start servers in background/external terminals - never block VS Code
