## 1. Package Structure

- [x] 1.1 Rewrite `backend/app/__init__.py` with all four export tiers (DSL types, Errors, Ports, Reference implementations); exclude `create_app` from root; include `__all__` list
- [x] 1.2 Update `pyproject.toml`: add `[project.optional-dependencies] fastapi = [...]`; move `fastapi`, `uvicorn`, `httpx` from core dependencies to the `fastapi` extra; keep `sqlalchemy>=2.0`, `cryptography`, `sqlglot` as core
- [x] 1.3 Add `[tool.setuptools.package-data] query_builder = ["schemas/*.json"]` to `pyproject.toml`
- [x] 1.4 Write `tests/unit/test_public_api.py` — import every Tier 1–4 symbol from `query_builder`; assert none raise `ImportError`; assert `create_app` is NOT in `query_builder.__all__`

## 2. QuerySpec JSON Schema

- [x] 2.1 Create `backend/app/schemas/` directory and `queryspec.v1.json` — root object `QuerySpec` with all required/optional fields; use `$defs` for `JoinDef`, `SelectField`, `SortDef`, `ColumnRef`, `ParamRef`, `ValueRef`, `Predicate`, `FilterGroup`, `Operand`, `Dialect`
- [x] 2.2 Add `"kind"` discriminator field to `ColumnRef` (`"column"`), `ParamRef` (`"param"`), `ValueRef` (`"value"`) in schema; define `Operand` as `oneOf` these three using `"kind"` to discriminate
- [x] 2.3 Add `if/then` arity constraints for `Predicate.op`: nullary ops → `right` must be null/absent; scalar ops → single Operand; list ops → `minItems: 1` array; `between` → `minItems: 2, maxItems: 2`
- [x] 2.4 Add `minItems: 1` on `FilterGroup.items`; document max nesting depth of 10 as a comment
- [x] 2.5 Write `tests/unit/test_queryspec_schema.py` — use `jsonschema` library to validate: minimal valid spec, missing `connection_id` fails, bad dialect fails, `is_null` with `right` fails, `between` with 3 items fails, `in` with empty array fails, nested `FilterGroup` passes

## 3. QuerySpecCodec kind-field integration

- [x] 3.1 Update `domain/value_objects/serialisation.py` — `QuerySpecCodec.encode()` injects `"kind"` field on `ColumnRef`/`ParamRef`/`ValueRef`; `decode()` reads `"kind"` to dispatch to correct type; raises `ValueError` on unknown `"kind"`
- [x] 3.2 Update `tests/unit/test_query_spec_codec.py` — add: `ColumnRef` encoded with `kind="column"`, `ValueRef` decoded from `kind="value"`, unknown `kind` raises `ValueError`
- [x] 3.3 Optionally validate decoded dict against `queryspec.v1.json` using `jsonschema` before construction (add `jsonschema` to dev dependencies if not present)

## 4. Connection Management Documentation

- [x] 4.1 Create `docs/consumer_guide.md` — sections: Overview, Installation (`pip install query-builder` vs `[fastapi]`), Minimal wiring example (full copy-pasteable code block), Connection registration and allowlist co-configuration, Error handling (`try/except` patterns for all four domain errors), Replacing reference implementations (table of what to swap for production)
- [x] 4.2 Add docstring to `IConnectionRepository` clarifying: `register()` must be called before `execute()`; `InMemoryConnectionRepository` is test-only; `CipherBackedConnectionRepository` is the production default
- [x] 4.3 Add docstring to `TableAllowlistPolicy` clarifying: closed-by-default behaviour; every `connection_id` used in execution must appear in the allowlist mapping

## 5. Schema Accessibility Test

- [x] 5.1 Write `tests/unit/test_schema_resource.py` — `importlib.resources.files("query_builder").joinpath("schemas/queryspec.v1.json").read_text()` returns valid JSON; `json.loads()` succeeds; root has `"$schema"` and `"title": "QuerySpec"`
- [x] 5.2 Run full test suite (`pytest backend/tests/`) — all green before commit
