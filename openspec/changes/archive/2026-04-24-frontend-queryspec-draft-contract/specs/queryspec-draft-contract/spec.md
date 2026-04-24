## ADDED Requirements

### Requirement: Library exports a typed QuerySpec draft contract
The frontend library SHALL export a `QuerySpecDraft` model and supporting draft types that represent source, joins, select fields, predicates, filter groups, parameters, sort definitions, limit, and dialect. Operand draft types SHALL use explicit discriminators for `column`, `param`, and `value`. Dialect draft values SHALL be limited to `postgres` and `mssql`.

#### Scenario: Consumer imports draft model types
- **WHEN** a consuming application imports from `@query-builder/ui`
- **THEN** it can import `QuerySpecDraft` and the draft operand types
- **AND** the operand types distinguish `column`, `param`, and `value` by a `kind` discriminator
- **AND** the dialect type allows only `postgres` and `mssql`

### Requirement: Query builder initializes a local draft without services
`<qb-query-builder>` SHALL create a local `QuerySpecDraft` using Angular component state only. The component SHALL NOT require an injected draft service, global store, backend client, or application provider to render and update the draft.

#### Scenario: Shell renders with a default local draft
- **WHEN** a consumer renders `<qb-query-builder>` without inputs
- **THEN** the component creates a default `QuerySpecDraft`
- **AND** the builder rail remains usable
- **AND** no draft service, global store, or backend client is required

### Requirement: Business sections mutate draft fields
The builder rail SHALL provide local controls for the six business sections: `Start with`, `Add related data`, `Choose columns`, `Filter rows`, `Parameters`, and `Sort & Limit`. Each section SHALL update the local `QuerySpecDraft` field that corresponds to its business responsibility.

#### Scenario: User edits section controls
- **WHEN** the user changes a control in any business section
- **THEN** the local `QuerySpecDraft` updates the corresponding field
- **AND** unchanged draft fields are preserved
- **AND** the builder rail continues to use business-language labels

### Requirement: Draft changes are emitted to consumers
`<qb-query-builder>` SHALL emit typed draft-change events when local controls update the `QuerySpecDraft`. Event payloads SHALL be serializable draft values and SHALL NOT include Angular component instances, services, observables, or backend adapter objects.

#### Scenario: Consumer receives a draft update
- **WHEN** a user edit changes the local draft
- **THEN** the component emits a typed draft-change event
- **AND** the emitted payload contains the updated `QuerySpecDraft`
- **AND** the payload can be JSON serialized without component or service references

### Requirement: Preview and SQL actions emit intent only
Preview and SQL actions SHALL emit typed intent events containing the current `QuerySpecDraft`. The library SHALL NOT compile SQL, execute preview queries, persist drafts, or perform HTTP requests from these actions.

#### Scenario: Consumer handles preview intent
- **WHEN** the user triggers a preview or SQL action
- **THEN** the component emits an intent event with the current `QuerySpecDraft`
- **AND** no HTTP request is made by the library
- **AND** no SQL compilation or query execution happens inside the library

### Requirement: Demo visualizes draft output without owning product behavior
The demo app SHALL render `<qb-query-builder>` and MAY display the latest emitted draft or intent payload for verification. The demo SHALL NOT introduce connection management, persistence, API calls, auth flows, or saved dataset behavior.

#### Scenario: Demo shows emitted draft for verification
- **WHEN** a user edits the demo shell
- **THEN** the demo can show the latest emitted draft payload
- **AND** the demo does not call backend APIs
- **AND** the demo does not add non-library product flows
