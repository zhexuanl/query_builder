# Query Builder — Project Plan

## What This Project Is

`query-builder` is a **Python library** for governed SQL generation. It is not an application. Consuming projects import it, wire up the ports they care about, and own their own persistence, audit infrastructure, and HTTP layer.

Core value proposition:
- Non-technical users express a query using a structured DSL (`QuerySpec`) — never raw SQL
- The library compiles `QuerySpec → SQL` for Postgres or MSSQL via SQLAlchemy Core
- Policy checks (join limits, row caps, table allowlists) are enforced before compilation
- An optional execution path previews the result set against the source database
- Connection strings are encrypted at rest via a cipher port; consumers supply the key

The FastAPI HTTP reference implementation is an **optional extra** (`pip install "query-builder[fastapi]"`), not the primary interface.

---

## Architecture

```
query_builder/
├── domain/              # Pure Python — zero framework imports
│   ├── entities/        # QuerySpec (aggregate root), DatasetDefinition
│   ├── value_objects/   # JoinDef, SelectField, Predicate, FilterGroup, …
│   ├── interfaces/      # Abstract ports (IQueryCompiler, IQueryExecutor, …)
│   ├── errors.py        # PolicyViolation, CompilationError, CatalogMiss, …
│   └── value_objects/serialisation.py  # QuerySpecCodec (dict ↔ QuerySpec)
├── use_cases/           # Orchestration — no HTTP or ORM knowledge
│   ├── compile_query.py         # CompileQueryUseCase
│   ├── execute_query.py         # ExecuteQueryUseCase
│   ├── save_dataset.py          # SaveDatasetUseCase
│   └── get_dataset.py           # GetDatasetUseCase
├── adapters/            # Concrete port implementations
│   ├── compilers/       # SqlAlchemyCoreCompiler (+ optional SQLGlot qualify)
│   ├── executor/        # SqlAlchemyQueryExecutor, PooledSqlAlchemyQueryExecutor
│   ├── policy/          # DefaultQueryPolicy, TableAllowlistPolicy
│   ├── catalog/         # SqlAlchemySchemaReflector, SqlAlchemyCatalogView
│   ├── cipher/          # FernetCredentialCipher
│   └── audit/           # JsonStdoutAuditLog
├── infrastructure/      # Reference implementations (consumers replace these)
│   ├── catalog/         # InMemoryCatalogRepository
│   ├── connection/      # InMemoryConnectionRepository, CipherBackedConnectionRepository
│   ├── dataset/         # InMemoryDatasetRepository
│   └── api/             # FastAPI routes (optional [fastapi] extra)
│       ├── routes/      # POST /queries/execute, /datasets CRUD
│       └── models/      # Pydantic request/response models
└── schemas/
    └── queryspec.v1.json  # JSON Schema for the QuerySpec DSL (ships with package)
```

Dependency rule: `domain` → `use_cases` → `adapters` → `infrastructure`. Inner layers never import outer layers.

---

## QuerySpec DSL

`QuerySpec` is the aggregate root. Consumers construct it in Python or deserialise it from JSON (validated against `schemas/queryspec.v1.json`).

```python
QuerySpec(
    connection_id: str,                     # registered connection
    source: JoinDef,                        # primary table
    select: tuple[SelectField, ...],        # projected columns / aggregates
    joins: tuple[JoinDef, ...] = (),        # up to 3 joined tables
    where: FilterGroup | None = None,       # filter tree (AND/OR/predicates)
    group_by: tuple[ColumnRef, ...] = (),
    order_by: tuple[SortDef, ...] = (),
    limit: int | None = 1000,              # required by DefaultQueryPolicy
    version: int = 1,
)
```

**Operand types** (used in `Predicate.right`):

| Type | JSON `kind` | Description |
|---|---|---|
| `ColumnRef(alias, name)` | `"column"` | Reference to a table column |
| `ParamRef(name)` | `"param"` | Named runtime parameter |
| `ValueRef(value)` | `"value"` | Literal value (str, int, float, bool, null) |

**Predicate operators**: `=`, `!=`, `>`, `>=`, `<`, `<=`, `in`, `not_in`, `like`, `not_like`, `is_null`, `is_not_null`, `between`

**Dialects**: `Dialect.postgres`, `Dialect.mssql`

Full JSON Schema: `query_builder/schemas/queryspec.v1.json` (accessible via `importlib.resources`).

---

## Ports — What Consumers Own vs What the Library Provides

| Port | Library provides | Consumer replaces with |
|---|---|---|
| `IQueryCompiler` | `SqlAlchemyCoreCompiler` | Custom compiler (e.g., Spark SQL) |
| `IQueryExecutor` | `SqlAlchemyQueryExecutor`, `PooledSqlAlchemyQueryExecutor` | Spark, BigQuery, etc. |
| `IQueryPolicy` | `DefaultQueryPolicy`, `TableAllowlistPolicy` | Domain-specific rules |
| `ISchemaReflector` | `SqlAlchemySchemaReflector` | Mock for testing |
| `ICatalogRepository` | `InMemoryCatalogRepository` | Redis/DB-backed cache |
| `IConnectionRepository` | `InMemory...`, `CipherBacked...` | DB-backed encrypted store |
| `IDatasetRepository` | `InMemoryDatasetRepository` | DB/S3-backed store |
| `IAuditLog` | `JsonStdoutAuditLog` | DB, event bus, cloud logging |
| `ICredentialCipher` | `FernetCredentialCipher` | KMS, Vault, HSM |

**In-memory implementations are test doubles, not production components.** They lose state on restart by design — the consuming project owns persistence.

---

## Milestones Completed

| Milestone | Commit | What shipped |
|---|---|---|
| **M0** — Foundation | `4c816ff` | Domain entities, value objects, ports, errors; Google-style docstrings |
| **M1** — Compiler spike | `1f88262` | `SqlAlchemyCoreCompiler`; 14 golden tests (Postgres + MSSQL) |
| **M2** — Catalog reflection | `7ac6e43` | `SqlAlchemySchemaReflector`; `InMemoryCatalogRepository`; connect timeout; testcontainers |
| **M3** — Policy validation | `4a7fd12` | `DefaultQueryPolicy`, `TableAllowlistPolicy`; `CompileQueryUseCase` |
| **M4** — Query execution | `5a3f469` | `IQueryExecutor`; `ExecuteQueryUseCase`; `POST /queries/execute`; `create_app()` |
| **M5** — Security and audit | `2fbdab8` | `FernetCredentialCipher`; `CipherBackedConnectionRepository`; `IAuditLog`; closed-by-default allowlist; `caller_id` threading |
| **M6a** — SQLGlot + datasets | `b818b5d` | SQLGlot qualify pass; `DatasetDefinition`; `InMemoryDatasetRepository`; `SaveDatasetUseCase`; `/datasets` CRUD routes |
| **M6b** — Library consumer API | `2f39bfe` | `__init__.py` public exports (4 tiers); `queryspec.v1.json` JSON Schema; `QuerySpecCodec` with `kind` discriminators; `docs/consumer_guide.md` |

All milestones archived under `openspec/changes/archive/`.

---

## Open Work

### qa-hardening (implemented, pending commit)

All 18 tasks complete. Not yet committed.

Covers:
- `QuerySpecCodec` round-trip and `kind`-discriminator tests
- `PooledSqlAlchemyQueryExecutor` (pre-built engine variant for high-frequency callers)
- Port contract base classes (`QueryPolicyContract`, `QueryExecutorContract`, `QueryCompilerContract`) in `tests/contracts/` — consumable by downstream projects
- Unit test gaps closed: `SqlAlchemyCatalogView`, `JsonStdoutAuditLog`
- Edge-case compiler tests: `IS NULL`, `IN`, nested `OR/AND`, `count_distinct`, no-limit
- MSSQL parity tests: `TOP N`, bracket quoting, join keywords — no container required
- Integration tests: full pipeline (Postgres testcontainer), dataset round-trip, policy rejection flow

**Next action:** `git add -A && git commit "QA: hardening — integration tests, codec, pooled executor, contract classes"` then `/opsx:archive qa-hardening`

---

## Installation

```bash
# Core library (SQL generation + execution)
pip install query-builder

# With FastAPI HTTP reference implementation
pip install "query-builder[fastapi]"

# Development (tests, testcontainers, jsonschema)
pip install "query-builder[fastapi,dev]"
```

Core dependencies: `sqlalchemy>=2.0`, `cryptography>=42.0`, `sqlglot>=30.0,<31`

Python: 3.12+

---

## Key Files for Consumers

| File | Purpose |
|---|---|
| `docs/consumer_guide.md` | Minimal wiring example, error handling, port replacement table |
| `query_builder/schemas/queryspec.v1.json` | Machine-readable DSL schema for validation / SDK generation |
| `query_builder/__init__.py` | Full public API surface — all importable symbols |
| `tests/contracts/` | Port contract base classes for testing custom implementations |
