## 1. Draft Model Contract

- [x] 1.1 Add `queryspec-draft.models.ts` with `QuerySpecDraft`, dialect, source, join, select, predicate, filter group, parameter, sort, and discriminated operand draft types
- [x] 1.2 Export the draft model types from `@query-builder/ui` without adding services or backend client symbols
- [x] 1.3 Add model tests proving operand `kind` discriminators, dialect narrowing, and JSON-serializable representative draft shape

## 2. Local Draft State

- [x] 2.1 Add a default local `QuerySpecDraft` factory for the shell component
- [x] 2.2 Store the draft in `QueryBuilderComponent` with Angular signals and no injected draft service
- [x] 2.3 Add component tests proving `<qb-query-builder>` renders with a default draft and requires no application provider

## 3. Section Controls

- [x] 3.1 Convert `Start with` from display copy into bounded local source controls that update the draft source
- [x] 3.2 Convert `Add related data` into bounded local join controls that update draft joins
- [x] 3.3 Convert `Choose columns` into bounded local select controls that update draft select fields
- [x] 3.4 Convert `Filter rows` and `Parameters` into bounded local predicate and parameter controls using `column`, `param`, and `value` operands
- [x] 3.5 Convert `Sort & Limit` into bounded local sort, limit, and dialect controls
- [x] 3.6 Add tests proving each business section mutates only its corresponding draft field and preserves unrelated fields

## 4. Public Events

- [x] 4.1 Add typed `draftChange` output that emits the updated `QuerySpecDraft` after local edits
- [x] 4.2 Add typed preview and SQL intent outputs that emit the current `QuerySpecDraft`
- [x] 4.3 Add tests proving emitted payloads are serializable and contain no component, service, observable, or adapter references
- [x] 4.4 Add a guard test or import scan proving the library does not import `HttpClient`, `fetch`, generated API clients, or backend adapters (`Select-String` import scan)

## 5. Demo Verification Surface

- [x] 5.1 Update the demo app to display the latest emitted draft and intent payload for verification only
- [x] 5.2 Keep demo interactions local; do not add connection, dataset, auth, save, or API flows
- [x] 5.3 Add demo tests proving the app renders the shell and captures emitted draft output without backend calls

## 6. Verification

- [x] 6.1 Run `npx ng test query-builder-ui --watch=false`
- [x] 6.2 Run `npx ng test demo --watch=false`
- [x] 6.3 Run `npx ng build query-builder-ui`
- [x] 6.4 Run `npx ng build demo`
- [x] 6.5 Run `openspec validate --changes frontend-queryspec-draft-contract`
- [x] 6.6 Perform adversarial review against the design boundaries before committing
