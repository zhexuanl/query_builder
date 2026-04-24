## Context

The approved frontend milestone is a shell milestone, not a product-complete UI. The change must stay inside four things only: Angular scaffold, query builder shell, theme system, and a demo app for local verification.

The shell still needs to look like the real governed query workflow. That means the split-panel layout, business-language sections, and preview states are part of this milestone. Service layers, API wiring, and secondary surfaces are not.

## Goals

- Create `frontend/` as an Angular workspace with one library and one demo app
- Configure the library surface as `@query-builder/ui`
- Establish Tailwind styling, CSS tokens, and a shared class-token theme object
- Export one shell component, `QueryBuilderComponent`, rendered as `<qb-query-builder>`
- Render the real business-language shell sections and preview shell states with local-only interactions

## Non-goals

- `ConnectionManagerComponent`
- `DatasetListComponent`
- `QUERY_BUILDER_CONFIG`
- API services or HTTP calls
- QuerySpec draft state service
- Connection, dataset, or auth flows
- Fake persistence or placeholder backend adapters

## Decision Gate Outcome

The hard-to-reverse choices for this milestone are already decided and locked for the shell pass.

- Package surface:
  Outcome: configure the shell library surface as `@query-builder/ui`, with only `QueryBuilderComponent` and `QUERY_BUILDER_PT` exported in this milestone.
  Rejected: exporting secondary surfaces or config tokens before they exist.
- Theme contract:
  Outcome: Tailwind utilities, CSS custom properties, and `QUERY_BUILDER_PT` as the visual contract.
  Rejected: Material-style defaults, stock component theme CSS, or a shell that delays the theme system to a later milestone.

## Decision Gate Correction

Task 3 verified that the PrimeNG Angular package available for this Angular 17 workspace does not expose a real unstyled pass-through configuration surface. Mutating private or non-existent config fields would create a false contract, so the cleaner design removes PrimeNG from this milestone and keeps the theme boundary owned by the library.

Correctness-critical:

- the public package exports the promised theme object
- visual tokens are local to the library and demo
- no dependency is configured through unsupported API shape

Rejected mechanism:

- fake `unstyled` or `pt` fields on PrimeNG config
- an unused third-party primitive dependency for a shell that can be rendered with Angular templates and Tailwind
- Shell state model:
  Outcome: local Angular signals only for shell interaction state.
  Rejected: shared service state, RxJS draft orchestration, or any API-backed state model in this milestone.

## Design Decisions

### Decision 1 — Scope is shell-only

This milestone owns only:

- Angular scaffold
- Query builder shell
- Theme system
- Demo app

Nothing else belongs here. The change must not carry forward full-product exports, service layers, or API contracts that are not implemented in this milestone.

### Decision 2 — Public API stays minimal

The library public API exports only:

- `QueryBuilderComponent`
- `QUERY_BUILDER_PT`

That is the truthful package surface for this milestone. Secondary components and config tokens stay out until they actually exist.

### Decision 3 — State is local signals only

State in this milestone is local Angular signals only for:

- expanded sections
- preview mode

There is no service layer in this milestone. No shared draft store, no RxJS state service, and no API orchestration belong in a shell-only pass.

### Decision 4 — Layout must show the real product shape

`<qb-query-builder>` renders a persistent split panel:

- builder rail on the left at roughly `420px`
- preview pane on the right filling remaining width

The builder rail shows the real business-language sections in order so the shell already reads like a governed query tool instead of a marketing mock.

### Decision 5 — Theme foundation ships now

Visual styling comes from Tailwind utilities, CSS tokens, and the exported `QUERY_BUILDER_PT` class-token object. This milestone establishes the design system contract without inventing backend behavior or binding the package to unsupported third-party theming APIs.

## Design Boundaries

The design contract stays at invariant level:

- one exported shell component, `<qb-query-builder>`
- one exported theme object, `QUERY_BUILDER_PT`
- split-panel layout with a builder rail and preview pane
- business-language sections rendered in order
- local shell interaction state only
- demo app present for local verification, but not part of the public library API

## State Model

Shell interaction state stays local to the shell component tree.

- `expandedSections`
- `previewMode`

That is enough for this milestone. No shared service, external store, or API-backed state boundary is justified in this milestone.

## Layout Rules

- Desktop-first split layout
- Builder rail width around `420px`
- Most sections expanded on first render
- One surface per section, no nested card stacks
- Persistent preview action bar so the future interaction model is obvious

## Visual Direction

The approved direction is balanced enterprise:

- light-only theme
- warm surfaces and cool borders
- restrained orange accent
- IBM Plex Sans for UI text
- IBM Plex Mono for SQL
- shallow depth and soft radii

The shell should feel premium and production-intentional without inventing fake data workflows.

## Verification

Required verification for the implementation milestone:

1. `ng build query-builder-ui`
2. `ng build demo`
3. `ng serve demo`
4. Manual browser verification of split layout, section expansion behavior, preview state switching, and theme application

## Risks / Trade-offs

- Locking `@query-builder/ui` now keeps the shell honest, but it does commit the milestone to a library-first surface before richer features land.
- Owning the shell styling with Tailwind and CSS tokens gives stronger control over the visual result, but later primitive adoption will need a separate milestone if it changes the public theme contract.
- Local signals keep the shell clean and reversible for this phase, but later milestones will need an explicit state boundary when real QuerySpec editing arrives.

## Migration Plan

- This milestone creates the Angular workspace, shell component surface, and theme contract only.
- Later milestones can add richer shell internals without changing the exported shell tag.
- Service state, API wiring, and secondary exported surfaces remain deferred until their own milestone artifacts make those boundaries explicit.

## Open Questions

- Should a later milestone introduce a dedicated shell state service, or can real QuerySpec editing still stay component-local after the shell is implemented?
