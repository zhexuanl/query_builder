## Frontend Query Builder: Shell Milestone

## Why

The active frontend change is lying about scope. The approved milestone is only the Angular shell needed to stand up the query builder surface, theme system, and demo workflow. Anything beyond that mixes phases and guarantees throwaway work.

This change now tracks only the shell milestone. It establishes the Angular workspace, the library package surface, the shell component contract, and the visual foundation needed for the first honest frontend slice.

## What Changes

- New Angular workspace at `frontend/` with one library and one demo app
- Library package surface for `@query-builder/ui`
- Tailwind styling + CSS tokens + exported theme class-token object
- One exported shell component: `<qb-query-builder>`
- Premium split-panel shell with business-language sections and preview states

## Capabilities

### New Capabilities
- `query-builder-shell`: Angular workspace scaffold, library packaging, theme foundation, and the split-panel shell for `<qb-query-builder>`

### Modified Capabilities
_(none)_

## Impact

- New frontend workspace under `frontend/`
- New Angular library package surface configured as `@query-builder/ui`
- New demo application used only for local visual verification
- No backend or API contract changes in this milestone

## Non-goals

- Connection CRUD
- Dataset browser
- API integration
- QuerySpec draft state management
- Authentication wiring
- Save/delete flows
- Real query execution
- Additional exported UI surfaces beyond `<qb-query-builder>`
