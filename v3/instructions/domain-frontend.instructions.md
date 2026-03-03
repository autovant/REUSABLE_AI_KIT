---
applyTo: '**/*.{tsx,jsx,css,scss,html,svelte,vue}'
description: 'Frontend domain patterns: React, CSS, accessibility, performance'
---

# Frontend Patterns

Applied only to frontend files. Reference these when building or reviewing UI code.

## React/TypeScript

- Functional components with hooks. No class components.
- TypeScript interfaces for all props. No `any`.
- Custom hooks for reusable logic (prefix `use`).
- Separate presentation from logic (container/presentational or hooks).

### State Management Hierarchy

1. Derived (compute during render) - No state needed
2. useState - Simple local state
3. useReducer - Complex local state
4. Context - Cross-cutting (theme, auth)
5. External store (Zustand, Redux) - Shared app state
6. React Query / SWR - Server state

### Common React Mistakes

| Mistake | Fix |
|---------|-----|
| `useEffect` for derived state | Compute during render |
| Missing deps in useEffect | Add all referenced values to array |
| `index` as key in dynamic lists | Use stable unique ID |
| Prop drilling 5+ levels | Use Context or external store |
| `useEffect` -> setState -> re-render loop | Restructure data flow |

## CSS & Styling

- **Detect project approach first** (Tailwind, CSS Modules, styled-components, etc.)
- Mobile-first responsive design (min-width breakpoints)
- Design tokens over hardcoded values
- No `!important` except for third-party overrides

## Accessibility (WCAG 2.1 AA)

- Semantic HTML: `<button>`, `<nav>`, `<main>`, `<section>`, not `<div>` for everything
- All interactive elements keyboard-accessible (Tab, Enter, Escape)
- `aria-label` on icons/buttons without visible text
- Color contrast ratio 4.5:1 for normal text, 3:1 for large
- Focus indicators visible on all interactive elements

## Performance

- Lazy load routes and heavy components (`React.lazy`, dynamic imports)
- Memoize expensive renders (`React.memo`) and calculations (`useMemo`)
- Virtualize lists with 100+ items
- Optimize images (next/image, srcset, lazy loading)
- Monitor Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1
