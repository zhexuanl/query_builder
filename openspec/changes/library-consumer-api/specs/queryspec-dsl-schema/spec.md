## ADDED Requirements

### Requirement: queryspec.v1.json is a valid JSON Schema draft-07 document covering all QuerySpec fields
The schema SHALL define `QuerySpec` as the root object and use `$defs` for all nested types. It MUST be self-contained (no external `$ref`). Every field from the domain model SHALL appear in the schema with correct type constraints.

#### Scenario: Valid minimal QuerySpec passes schema validation
- **WHEN** `{"version": 1, "connection_id": "prod-pg", "source": {...}, "select": [...], "limit": 100}` is validated against the schema
- **THEN** validation passes with zero errors

#### Scenario: QuerySpec missing connection_id fails schema validation
- **WHEN** a JSON object without `connection_id` is validated
- **THEN** validation fails with an error identifying `connection_id` as required

#### Scenario: Unknown dialect value fails schema validation
- **WHEN** `"dialect": "oracle"` appears in the JSON
- **THEN** validation fails because `"oracle"` is not in the `enum` `["postgres", "mssql"]`

---

### Requirement: Operand types use a kind discriminator for unambiguous deserialisaton
`ColumnRef`, `ParamRef`, and `ValueRef` SHALL each carry a `"kind"` string literal field. The schema SHALL define `Operand` as `oneOf` these three shapes, discriminated by `"kind"`. `QuerySpecCodec.encode()` MUST inject the `"kind"` field; `decode()` MUST use it to reconstruct the correct Python type.

| Type | kind value | Additional fields |
|---|---|---|
| `ColumnRef` | `"column"` | `alias: str`, `name: str` |
| `ParamRef` | `"param"` | `name: str` |
| `ValueRef` | `"value"` | `value: str\|int\|float\|bool\|null` |

#### Scenario: ColumnRef encoded with kind="column"
- **WHEN** `QuerySpecCodec.encode(spec)` is called on a spec with a `ColumnRef`
- **THEN** the encoded dict contains `{"kind": "column", "alias": "...", "name": "..."}`

#### Scenario: ValueRef decoded correctly from kind field
- **WHEN** `QuerySpecCodec.decode(data)` encounters `{"kind": "value", "value": 42}`
- **THEN** a `ValueRef(value=42)` is returned

#### Scenario: Unknown kind raises ValueError on decode
- **WHEN** `QuerySpecCodec.decode(data)` encounters `{"kind": "expression", ...}` in an operand position
- **THEN** `ValueError` is raised identifying the unknown kind

---

### Requirement: Predicate operator arity is enforced in the schema
The schema SHALL use `if/then` constraints to enforce `right` field arity per operator:
- Nullary ops (`is_null`, `is_not_null`): `right` MUST be absent or `null`
- Scalar ops (`=`, `!=`, `>`, `>=`, `<`, `<=`, `like`, `not_like`): `right` MUST be a single `Operand`
- List ops (`in`, `not_in`): `right` MUST be a non-empty array of `Operand`
- Range op (`between`): `right` MUST be an array of exactly two `Operand` items

#### Scenario: is_null predicate with non-null right fails validation
- **WHEN** `{"op": "is_null", "right": {"kind": "value", "value": 1}}` is validated
- **THEN** schema validation fails

#### Scenario: between predicate with three operands fails validation
- **WHEN** `{"op": "between", "right": [{...}, {...}, {...}]}` is validated
- **THEN** schema validation fails because `right` must have exactly two items

#### Scenario: in predicate with empty array fails validation
- **WHEN** `{"op": "in", "right": []}` is validated
- **THEN** schema validation fails because `right` must be non-empty

---

### Requirement: FilterGroup supports recursive nesting up to a documented depth
The schema SHALL document that `FilterGroup.items` contains `oneOf [Predicate, FilterGroup]`. Implementations MUST enforce a maximum nesting depth of 10 at runtime (not in the schema, which cannot count recursion depth).

#### Scenario: Nested FilterGroup within FilterGroup is valid
- **WHEN** a `FilterGroup` containing another `FilterGroup` is validated against the schema
- **THEN** validation passes

#### Scenario: FilterGroup with empty items array fails validation
- **WHEN** `{"op": "and", "items": []}` is validated
- **THEN** schema validation fails because `items` must be non-empty (`minItems: 1`)
