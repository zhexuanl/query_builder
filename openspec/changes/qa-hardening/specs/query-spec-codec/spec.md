## ADDED Requirements

### Requirement: QuerySpecCodec round-trips a QuerySpec through a plain Python dict
`QuerySpecCodec` SHALL provide `encode(spec: QuerySpec) -> dict[str, Any]` and `decode(data: dict[str, Any]) -> QuerySpec`. The encoded dict MUST be JSON-serialisable using the stdlib `json` module with no custom encoder. `frozenset` values MUST be encoded as sorted `list`. `tuple` values MUST be encoded as `list`. `Dialect` MUST be encoded as its string value.

#### Scenario: encode produces a JSON-serialisable dict
- **WHEN** `QuerySpecCodec.encode(spec)` is called on any valid `QuerySpec`
- **THEN** `json.dumps(result)` succeeds without raising

#### Scenario: Round-trip is lossless
- **WHEN** `QuerySpecCodec.decode(QuerySpecCodec.encode(spec))` is called
- **THEN** the result compares equal to the original `spec` by value

#### Scenario: decode rejects an unrecognised version field
- **WHEN** `decode()` is called with `{"version": 99, ...}`
- **THEN** `ValueError` is raised identifying the unsupported version

---

### Requirement: QuerySpecCodec handles all QuerySpec field types without framework imports
The codec SHALL reside in `domain/value_objects/serialisation.py` and MUST NOT import SQLAlchemy, Pydantic, or any infrastructure framework. It MUST handle `ColumnRef`, `ValueRef`, `ParamRef`, `Predicate`, `FilterGroup`, `JoinDef`, `SelectField`, `SortDef`, and `Dialect`.

#### Scenario: Spec with nested FilterGroup round-trips correctly
- **WHEN** a `QuerySpec` with a `FilterGroup` containing a nested `FilterGroup` is encoded and decoded
- **THEN** the decoded filter tree is structurally identical to the original

#### Scenario: Spec with aggregates and group_by round-trips correctly
- **WHEN** a `QuerySpec` with `SelectField(kind="agg")` and `group_by` is encoded and decoded
- **THEN** the decoded `select` and `group_by` fields are identical to the original
