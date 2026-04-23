## Context

`query-builder` is consumed as a Python library. Its domain types, ports, and reference implementations are currently only accessible by importing deep paths like `from domain.entities.query_spec import QuerySpec`. There is no declared public surface, no machine-readable schema for the DSL, and no connection registration guide. This change formalises what the library exposes and how consumers integrate.

## Goals / Non-Goals

**Goals:**
- Explicit public API via `backend/app/__init__.py`
- JSON Schema v7 for `QuerySpec` and all nested types (`schemas/queryspec.v1.json`)
- Documented connection management lifecycle (register, resolve, execute)
- `pyproject.toml` optional `[fastapi]` extra so the HTTP layer is not a forced dependency
- Consumer integration guide with minimal wiring example

**Non-Goals:**
- SDK generation for TypeScript/Java
- Semver API compatibility guarantees
- Plugin system or hook points beyond the existing port interfaces

---

## Decisions

### Decision 1 — Public API grouped into four export tiers

```python
# query_builder/__init__.py

# Tier 1: DSL types — consumers construct these
from .domain.entities.query_spec import QuerySpec
from .domain.value_objects.query_parts import JoinDef, SelectField, SortDef
from .domain.value_objects.refs import ColumnRef, ParamRef, ValueRef
from .domain.value_objects.filters import Predicate, FilterGroup
from .domain.value_objects.dialect import Dialect
from .domain.value_objects.serialisation import QuerySpecCodec

# Tier 2: Errors — consumers catch these
from .domain.errors import (
    QueryBuilderError,
    PolicyViolation, CompilationError,
    CatalogMiss, SourceConnectionError, DatasetNotFound,
)

# Tier 3: Ports — consumers implement or inject these
from .domain.interfaces.query_compiler import IQueryCompiler, CompiledQuery
from .domain.interfaces.query_executor import IQueryExecutor
from .domain.interfaces.query_policy import IQueryPolicy
from .domain.interfaces.catalog_repository import ICatalogRepository, CatalogView
from .domain.interfaces.connection_repository import IConnectionRepository
from .domain.interfaces.dataset_repository import IDatasetRepository
from .domain.interfaces.audit_log import IAuditLog
from .domain.interfaces.credential_cipher import ICredentialCipher

# Tier 4: Reference implementations — consumers use or replace these
from .adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from .adapters.executor.sqlalchemy_query_executor import SqlAlchemyQueryExecutor
from .adapters.executor.pooled_sqlalchemy_query_executor import PooledSqlAlchemyQueryExecutor
from .adapters.policy.default_query_policy import DefaultQueryPolicy
from .adapters.policy.table_allowlist_policy import TableAllowlistPolicy
from .adapters.cipher.fernet_credential_cipher import FernetCredentialCipher
from .adapters.catalog.sqlalchemy_schema_reflector import SqlAlchemySchemaReflector
from .infrastructure.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from .infrastructure.connection.in_memory_connection_repository import InMemoryConnectionRepository
from .infrastructure.connection.cipher_backed_connection_repository import CipherBackedConnectionRepository
from .infrastructure.dataset.in_memory_dataset_repository import InMemoryDatasetRepository
from .use_cases.compile_query import CompileQueryUseCase
from .use_cases.execute_query import ExecuteQueryUseCase
from .use_cases.save_dataset import SaveDatasetUseCase
from .use_cases.get_dataset import GetDatasetUseCase
```

`create_app()` is **not** exported at library root — it requires the `[fastapi]` extra and is accessed via `from query_builder.infrastructure.app import create_app`.

### Decision 2 — QuerySpec JSON Schema v1

The schema lives at `backend/app/schemas/queryspec.v1.json` and is shipped in the package via `pyproject.toml` `[tool.setuptools.package-data]`. It uses JSON Schema draft-07 with `$defs` for all nested types. Key design choices:

**Operand discriminated union** — `Predicate.right` uses `oneOf` with a `"kind"` discriminator field:
```json
"Operand": {
  "oneOf": [
    { "$ref": "#/$defs/ColumnRef" },
    { "$ref": "#/$defs/ParamRef" },
    { "$ref": "#/$defs/ValueRef" }
  ]
}
```
`ColumnRef`: `{"kind": "column", "alias": str, "name": str}`
`ParamRef`: `{"kind": "param", "name": str}`
`ValueRef`: `{"kind": "value", "value": str|int|float|bool|null}`

**FilterGroup recursion** — JSON Schema does not support recursive `$ref` natively in draft-07; use `"items": { "oneOf": [{"$ref": "#/$defs/Predicate"}, {"$ref": "#/$defs/FilterGroup"}] }` with `"$recursiveRef"` fallback for validators that support it.

**Nullary ops** — `is_null` and `is_not_null` predicates: `right` MUST be omitted or `null`. Enforce with `if/then` in the schema.

**Version field** — top-level `"version": {"type": "integer", "const": 1}` allows future schema evolution.

### Decision 3 — Connection management lifecycle

```
Consumer                           Library
   |                                  |
   |-- register(id, url) -----------> IConnectionRepository.register(id, url)
   |                                  |  └─ CipherBackedConnectionRepository:
   |                                  |      encrypt(url) → store bytes
   |                                  |
   |-- execute(spec, dialect) ------> ExecuteQueryUseCase
   |                                  |  └─ IConnectionRepository.get_url(spec.connection_id)
   |                                  |      └─ decrypt bytes → plaintext URL
   |                                  |  └─ IQueryExecutor.execute(compiled, url)
   |<- rows -------------------------  |
```

Consumers MUST call `register()` before any `execute()` referencing that `connection_id`. `TableAllowlistPolicy` MUST also be configured with the same `connection_id` and its permitted tables — otherwise the closed-by-default policy will reject the request.

**Consumer-provided vs library-provided:**

| Component | Library provides | Consumer provides |
|---|---|---|
| `IQueryCompiler` | `SqlAlchemyCoreCompiler` ✓ | Optional custom compiler |
| `IQueryExecutor` | `SqlAlchemyQueryExecutor` ✓ | Optional (e.g., for Spark) |
| `IQueryPolicy` | `DefaultQueryPolicy`, `TableAllowlistPolicy` ✓ | Additional domain policies |
| `ICatalogRepository` | `InMemoryCatalogRepository` ✓ | Replace with persistent cache |
| `IConnectionRepository` | `InMemory...`, `CipherBacked...` ✓ | Replace with DB-backed store |
| `IDatasetRepository` | `InMemoryDatasetRepository` ✓ | Replace with persistent store |
| `IAuditLog` | `JsonStdoutAuditLog` ✓ | Replace with DB/event bus |
| `ICredentialCipher` | `FernetCredentialCipher` ✓ | Replace with KMS-backed cipher |
| `ISchemaReflector` | `SqlAlchemySchemaReflector` ✓ | Optional custom reflector |

### Decision 4 — FastAPI as `[fastapi]` optional extra

`pyproject.toml`:
```toml
[project.optional-dependencies]
fastapi = ["fastapi>=0.115", "uvicorn[standard]", "httpx"]
```

Core dependencies (always required): `sqlalchemy>=2.0`, `cryptography`, `sqlglot`.

This means a consumer using the library purely for SQL generation (compiling `QuerySpec → SQL` without executing) only pulls in SQLAlchemy and SQLGlot. A consumer who also wants the HTTP reference implementation installs `query-builder[fastapi]`.

### Decision 5 — Minimal wiring example in `docs/consumer_guide.md`

```python
from query_builder import (
    QuerySpec, JoinDef, SelectField, ColumnRef, Dialect,
    SqlAlchemyCoreCompiler, SqlAlchemyQueryExecutor,
    InMemoryCatalogRepository, CipherBackedConnectionRepository,
    SqlAlchemySchemaReflector, FernetCredentialCipher,
    DefaultQueryPolicy, TableAllowlistPolicy,
    CompileQueryUseCase, ExecuteQueryUseCase,
    InMemoryDatasetRepository,
)
from cryptography.fernet import Fernet

# 1. Wiring
cipher = FernetCredentialCipher(key=Fernet.generate_key())
conn_repo = CipherBackedConnectionRepository(cipher)
conn_repo.register("prod-pg", "postgresql://user:pass@host/db")

catalog_repo = InMemoryCatalogRepository(
    reflector=SqlAlchemySchemaReflector(),
    url_for={"prod-pg": "postgresql://user:pass@host/db"},
)
policies = [
    DefaultQueryPolicy(),
    TableAllowlistPolicy({"prod-pg": frozenset({"customers", "orders"})}),
]
compiler = SqlAlchemyCoreCompiler()
compile_uc = CompileQueryUseCase(catalog_repo, policies, compiler)
execute_uc = ExecuteQueryUseCase(compile_uc, conn_repo, SqlAlchemyQueryExecutor())

# 2. Build a spec using the DSL
spec = QuerySpec(
    connection_id="prod-pg",
    source=JoinDef(type="inner", table="customers", alias="c", on=()),
    select=(SelectField(kind="column", source=ColumnRef("c", "name"), label="name"),),
    limit=100,
)

# 3. Compile only (no DB)
compiled = compile_uc.execute(spec, Dialect.postgres)
print(compiled.sql)

# 4. Execute (requires DB)
rows = execute_uc.execute(spec, Dialect.postgres, caller_id="svc-etl")
```

## Risks / Trade-offs

- **`__init__.py` import time**: importing everything at the root means SQLAlchemy is imported on `import query_builder`. Mitigate with lazy imports if startup time becomes a concern (post-QA).
- **`kind` discriminator field on `ColumnRef` / `ParamRef` / `ValueRef`**: these domain objects do not currently carry a `"kind"` field — they are distinguished by Python `isinstance`. The JSON Schema needs it for discriminated union serialisation. `QuerySpecCodec` must inject/strip it on encode/decode.
- **`[fastapi]` extra splits the package**: consumers using FastAPI routes need to install `query-builder[fastapi]`; document prominently.

## Open Questions

- Should `QuerySpec.version` default to `1` (current) or be required? (Propose: optional with default `1` so existing call sites don't break)
- Should `schemas/queryspec.v1.json` be validated against in `QuerySpecCodec.decode()`? (Propose: yes — one jsonschema validation call on decode catches malformed consumer input early)
