## Context

The approved frontend milestone is a shell milestone, not a product-complete UI. The change must stay inside four things only: Angular scaffold, query builder shell, theme system, and a demo app for local verification.

The shell still needs to look like the real governed query workflow. That means the split-panel layout, business-language sections, and preview states are part of this milestone. Service layers, API wiring, and secondary surfaces are not.

## Goals

- Create `frontend/` as an Angular workspace with one library and one demo app
- Configure the library surface as `@query-builder/ui`
- Establish PrimeNG unstyled mode, Tailwind styling, and a shared pass-through theme object
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

PrimeNG runs in unstyled mode. Visual styling comes from Tailwind utilities, CSS tokens, and the exported `QUERY_BUILDER_PT` pass-through theme object. This milestone establishes the design system contract without inventing backend behavior.

## Component Structure

```text
frontend/
  projects/
    query-builder-ui/
      src/lib/
        query-builder/
          query-builder.component.ts
          builder-panel.component.ts
          builder-section.component.ts
          preview-panel.component.ts
          preview-data-shell.component.ts
          preview-sql-shell.component.ts
        theme/
          query-builder-pt.ts
          query-builder.tokens.css
      src/public-api.ts
    demo/
```

## State Model

Use local signals in `QueryBuilderComponent` and shell subcomponents only.

- `expandedSections`
- `previewMode`

That is enough for this milestone. No service or persistence boundary is justified yet.

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
