---
name: code-scaffold
description: Generate components, services, tests, API endpoints, and other code files from templates matching project conventions. Invoke when creating new files or features.
---

# Code Scaffold Skill

## When This Skill Activates

- User says: create, generate, scaffold, new component, new service, new endpoint, new test, add feature
- Adding a new file to an existing project

## Step 1: Detect Project Conventions

Before generating any code, examine existing files to match conventions:

1. **Read 2-3 existing files** of the same type you're about to create
2. Detect: naming convention (PascalCase, camelCase, kebab-case), file organization, export style, import patterns
3. Detect: test co-location (same dir vs `__tests__/` vs `tests/`), test naming (`*.test.ts` vs `*.spec.ts`)
4. Check for existing templates, generators, or CLI tools in the project

## Template Reference

See `templates/code-templates.md` for a full library of starter templates across stacks (React, Express, FastAPI, Django, .NET, Playwright, Jest, pytest). Use those as starting points and adapt to match the project's detected conventions.

## Step 2: Choose Template and Scaffold

1. Select the appropriate template from `templates/code-templates.md` based on the detected stack
2. Adapt naming, imports, and patterns to match existing project files
3. For React components, co-locate related files:
   - `{ComponentName}.test.tsx` — Unit tests
   - `{ComponentName}.module.css` — Styles (if CSS modules detected)
   - `index.ts` — Re-export (only if barrel files used in project)

## Step 3: Generate and Wire Up

1. Create the file(s) using the adapted template
2. Register the new file where needed:
   - Add route to router config
   - Add service to DI container
   - Export from barrel file (index.ts)
   - Add migration to migration chain
3. Create corresponding test file
4. Verify: no compile errors, tests pass

## Rules

- Always match the existing project's conventions. Read before generating.
- Don't create barrel files (index.ts) if the project doesn't use them.
- Don't add comments unless the project style includes them.
- Use the project's existing patterns for error handling, validation, and response formatting.
- If the project has a generator CLI (e.g., `ng generate`, `rails generate`), prefer using it.
