# Frontend M2: QuerySpec Draft Contract

## Why

The shell milestone renders the right workflow shape, but it still cannot produce a truthful library value. The next slice should make `<qb-query-builder>` emit a local `QuerySpec` draft contract before any API, dataset, or persistence surface is added.

## What Changes

- Add TypeScript models for the frontend-owned `QuerySpec` draft shape, aligned with the Python DSL concepts: source, joins, select fields, predicates, parameters, sort, limit, and dialect.
- Convert the existing six builder sections from display-only content into local shell controls backed by Angular signals.
- Expose draft updates from `QueryBuilderComponent` through Angular inputs/outputs so consumers can own compile, preview, persistence, and transport.
- Keep preview modes local; preview actions may emit intent events but SHALL NOT perform HTTP calls.
- Add tests proving draft defaults, section edits, event emission, and absence of backend coupling.

## Non-goals

- No connection manager, dataset browser, or saved dataset UI.
- No FastAPI wiring, generated OpenAPI client, `HttpClient`, or direct backend calls.
- No shared QuerySpec service, global store, BehaviorSubject orchestration, or persistence layer.
- No real schema reflection, column discovery, query execution, or SQL compilation in the frontend library.
- No new public components beyond the existing shell component unless explicitly required by the draft contract.

## Capabilities

### New Capabilities

- `queryspec-draft-contract`: Defines the Angular library contract for creating, updating, and emitting local `QuerySpec` drafts from the shell.

### Modified Capabilities

_(none)_

## Impact

- Affects `frontend/projects/query-builder-ui` models, `QueryBuilderComponent`, section interaction logic, and unit tests.
- May update the demo app only to visualize draft changes and emitted intents.
- Public library API expands only if needed for draft model types and event payloads; it must not expose application services or backend adapters.
