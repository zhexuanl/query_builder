## 1. Draft Model Contract

- [ ] 1.1 Add `queryspec-draft.models.ts` with `QuerySpecDraft`, dialect, source, join, select, predicate, filter group, parameter, sort, and discriminated operand draft types
- [ ] 1.2 Export the draft model types from `@query-builder/ui` without adding services or backend client symbols
- [ ] 1.3 Add model tests proving operand `kind` discriminators, dialect narrowing, and JSON-serializable representative draft shape

## 2. Local Draft State

- [ ] 2.1 Add a default local `QuerySpecDraft` factory for the shell component
- [ ] 2.2 Store the draft in `QueryBuilderComponent` with Angular signals and no injected draft service
- [ ] 2.3 Add component tests proving `<qb-query-builder>` renders with a default draft and requires no application provider

## 3. Section Controls

- [ ] 3.1 Convert `Start with` from display copy into bounded local source controls that update the draft source
- [ ] 3.2 Convert `Add related data` into bounded local join controls that update draft joins
- [ ] 3.3 Convert `Choose columns` into bounded local select controls that update draft select fields
- [ ] 3.4 Convert `Filter rows` and `Parameters` into bounded local predicate and parameter controls using `column`, `param`, and `value` operands
- [ ] 3.5 Convert `Sort & Limit` into bounded local sort, limit, and dialect controls
- [ ] 3.6 Add tests proving each business section mutates only its corresponding draft field and preserves unrelated fields

## 4. Public Events

- [ ] 4.1 Add typed `draftChange` output that emits the updated `QuerySpecDraft` after local edits
- [ ] 4.2 Add typed preview and SQL intent outputs that emit the current `QuerySpecDraft`
- [ ] 4.3 Add tests proving emitted payloads are serializable and contain no component, service, observable, or adapter references
- [ ] 4.4 Add a guard test or import scan proving the library does not import `HttpClient`, `fetch`, generated API clients, or backend adapters

## 5. Demo Verification Surface

- [ ] 5.1 Update the demo app to display the latest emitted draft and intent payload for verification only
- [ ] 5.2 Keep demo interactions local; do not add connection, dataset, auth, save, or API flows
- [ ] 5.3 Add demo tests proving the app renders the shell and captures emitted draft output without backend calls

## 6. Verification

- [ ] 6.1 Run `npx ng test query-builder-ui --watch=false`
- [ ] 6.2 Run `npx ng test demo --watch=false`
- [ ] 6.3 Run `npx ng build query-builder-ui`
- [ ] 6.4 Run `npx ng build demo`
- [ ] 6.5 Run `openspec validate --changes frontend-queryspec-draft-contract`
- [ ] 6.6 Perform adversarial review against the design boundaries before committing
