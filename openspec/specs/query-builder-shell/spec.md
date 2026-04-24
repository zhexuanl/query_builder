# query-builder-shell Specification

## Purpose
TBD - created by archiving change frontend-query-builder-ui. Update Purpose after archive.
## Requirements
### Requirement: Query builder shell is delivered as a split-panel library component
The frontend SHALL expose one shell component, `<qb-query-builder>`, from `@query-builder/ui`. The shell milestone public API SHALL expose only `QueryBuilderComponent` and `QUERY_BUILDER_PT`. `<qb-query-builder>` SHALL render a persistent split-panel shell with a builder rail on the left and a preview pane on the right. The shell milestone SHALL use local UI state only and SHALL NOT perform HTTP calls or backend integration anywhere in the component surface.

#### Scenario: Split-panel shell renders on first load
- **WHEN** a consumer renders `<qb-query-builder>`
- **THEN** the builder rail and preview pane are both visible without routing or page-shell dependencies
- **AND** the shell surface relies on local UI state only
- **AND** no HTTP request or backend integration is triggered by the shell milestone implementation

---

### Requirement: Builder shell uses business-language sections
`<qb-query-builder>` SHALL render these shell sections in the builder rail: `Start with`, `Add related data`, `Choose columns`, `Filter rows`, `Parameters`, and `Sort & Limit`. The sections SHALL be visible on first render and SHALL start mostly expanded.

#### Scenario: Business-language sections are visible on first render
- **WHEN** `<qb-query-builder>` first renders
- **THEN** the builder rail shows `Start with`, `Add related data`, `Choose columns`, `Filter rows`, `Parameters`, and `Sort & Limit`
- **AND** most sections begin expanded

---

### Requirement: Preview pane supports local shell states only
The preview pane SHALL support `empty`, `data`, and `sql` shell states. Switching preview states in this milestone SHALL use local UI state only. The milestone SHALL NOT perform HTTP calls or other backend integration from the preview pane.

#### Scenario: Preview state switches without backend activity
- **WHEN** the user changes the preview shell state between `empty`, `data`, and `sql`
- **THEN** the visible shell content updates immediately from local UI state
- **AND** no HTTP request is made

