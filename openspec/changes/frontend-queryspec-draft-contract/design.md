## Context

The committed shell milestone exports one Angular library component, `<qb-query-builder>`, plus the theme token object. It intentionally has no QuerySpec state, no API integration, and no application-owned services.

The next milestone must make the shell useful as a library surface without violating that boundary. The library should produce a typed draft value that consuming applications can compile, preview, save, or transmit through their own infrastructure.

## Goals / Non-Goals

**Goals:**

- Define a frontend `QuerySpecDraft` contract aligned with the Python DSL and JSON schema concepts.
- Keep draft ownership local to `QueryBuilderComponent` using Angular signals.
- Emit typed draft and preview-intent events from the shell.
- Add enough controls to prove each business section mutates the draft.
- Keep the public library API honest and minimal.

**Non-Goals:**

- No backend calls, `HttpClient`, generated OpenAPI client, or FastAPI wiring.
- No connection manager, dataset browser, saved dataset UI, schema reflection, or SQL compiler.
- No shared draft service, BehaviorSubject store, global state, persistence layer, or app shell.
- No new public visual components unless required by the draft contract.

## Decision Gate Outcome

Objective: make the shell emit a truthful QuerySpec-shaped value without turning the library into an application.

User goal vs mechanism: the goal is a usable library contract; the wrong mechanism would be API wiring, a global service, or generated backend DTOs in this milestone.

Affected invariants and owners:

- Python backend/domain remains the canonical compiler and policy owner.
- Angular library owns only local UI draft construction and event emission.
- Consuming applications own transport, persistence, preview execution, auth, and audit.
- Public API must expose model types and the existing shell only; it must not expose adapters or app services.

Can this be avoided by a better design? No. Once the shell emits data, the payload must be typed. The avoidable pieces are service state, backend coupling, and generated clients.

Correctness-critical:

- discriminated operand shape for `column`, `param`, and `value`
- dialect limited to `postgres` and `mssql`
- draft changes emitted from local user edits
- no raw SQL entry point in the builder rail
- no HTTP activity from the library

Operational recovery: none in this milestone. Consumers handle failed preview, compile, save, and transport.

Policy sugar: section copy, placeholder option labels, and demo rendering remain visual affordances only.

Remaining decision: use plain exported TypeScript interfaces and discriminated unions for `QuerySpecDraft`, not classes or generated OpenAPI models. This keeps the contract serializable, testable, and independent of backend runtime packaging.

## Decisions

### Decision 1 — Draft Model Is A UI Contract, Not The Backend Aggregate

The library will export `QuerySpecDraft` and supporting draft types from a `queryspec-draft.models.ts` file. These types mirror the JSON boundary of `QuerySpec` closely enough for consumers to serialize or validate later, but they do not claim to be the Python frozen dataclasses.

Alternative rejected: importing generated OpenAPI models. That would add backend transport coupling before the library has any API integration requirement.

### Decision 2 — Local Signals Own Draft State

`QueryBuilderComponent` will keep a local signal for the draft and expose changes through Angular outputs. Initial values can come from an input, but the component must not require a service provider.

Alternative rejected: `QuerySpecService` or BehaviorSubject store. That creates an application state boundary inside a reusable library.

### Decision 3 — Events Express Intent, Not Execution

The component may emit `draftChange`, `previewRequested`, and `sqlRequested` style events. Those are consumer-owned intents. The library must not compile SQL, execute preview queries, or persist drafts.

Alternative rejected: internal preview execution. That would cross from UI library into infrastructure ownership.

### Decision 4 — Controls Stay Deliberately Small

Each business section should mutate at least one draft field, but only through bounded local controls. This milestone proves state and event contract, not full authoring UX.

Alternative rejected: building full source/catalog pickers, dynamic column discovery, or arbitrary filter builders now. Those require separate schema/catalog capabilities.

## Clean Architecture Layer Map

- `frontend/projects/query-builder-ui/src/lib/query-builder/queryspec-draft.models.ts`: library UI contract.
- `frontend/projects/query-builder-ui/src/lib/query-builder/query-builder.component.*`: reusable Angular presentation and local state.
- `frontend/projects/demo/src/app/*`: demo-only visualization of emitted draft and intents.

No backend domain, use case, adapter, infrastructure, port, or repository changes are introduced. No new port interface is required.

## Risks / Trade-offs

- Draft model drift from Python DSL -> mitigate by naming it `QuerySpecDraft`, keeping discriminators explicit, and testing representative serialization shape.
- Overbuilding UI controls -> mitigate by limiting each section to one or two bounded local controls.
- Event contract churn -> mitigate by exporting named payload interfaces and testing emitted payloads.
- Shell becoming an app -> mitigate by forbidding services, HTTP imports, persistence, and catalog reflection in this change.

## Migration Plan

1. Add draft model exports without removing existing shell exports.
2. Initialize the shell with a default local draft.
3. Add section controls that update draft signals.
4. Emit typed events for draft changes and preview/sql intent.
5. Update demo app to show emitted draft JSON for verification only.

Rollback is simple: consumers can continue rendering `<qb-query-builder>` without listening to outputs.

## Open Questions

- Should a later milestone generate TypeScript types from `queryspec.v1.json`, or keep hand-authored library draft types until the schema stabilizes?
- Should validation errors be represented by a future frontend validation capability, or remain backend/compiler-owned?
