# query-builder Consumer Guide

## Overview

`query-builder` is a Python library for compiling and executing governed SQL queries from a
structured `QuerySpec` DSL. It ships a domain model, ports (interfaces), and reference
implementations that you can replace in production.

## Installation

**Core library only** (SQL compilation, no HTTP layer):

```bash
pip install query-builder
```

**With FastAPI HTTP routes** (reference server):

```bash
pip install "query-builder[fastapi]"
```

Core dependencies: `sqlalchemy>=2.0`, `cryptography`, `sqlglot`.
`fastapi`, `uvicorn`, and `httpx` are only pulled in by the `[fastapi]` extra.

---

## Minimal Wiring Example

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

# 1. Cipher and connection repository
cipher = FernetCredentialCipher(key=Fernet.generate_key())
conn_repo = CipherBackedConnectionRepository(cipher)
conn_repo.register("prod-pg", "postgresql://user:pass@host/db")

# 2. Catalog repository (reflects schema from the live DB)
catalog_repo = InMemoryCatalogRepository(
    reflector=SqlAlchemySchemaReflector(),
    url_for={"prod-pg": "postgresql://user:pass@host/db"},
)

# 3. Policies — allowlist must cover every connection_id used
policies = [
    DefaultQueryPolicy(),
    TableAllowlistPolicy({"prod-pg": frozenset({"customers", "orders"})}),
]

# 4. Compiler and use cases
compiler = SqlAlchemyCoreCompiler()
compile_uc = CompileQueryUseCase(catalog_repo, policies, compiler)
execute_uc = ExecuteQueryUseCase(compile_uc, conn_repo, SqlAlchemyQueryExecutor())

# 5. Build a QuerySpec using the DSL
spec = QuerySpec(
    connection_id="prod-pg",
    source=JoinDef(type="inner", table="customers", alias="c", on=()),
    select=(SelectField(kind="column", source=ColumnRef("c", "name"), label="name"),),
    limit=100,
)

# 6. Compile only (no DB connection required)
compiled = compile_uc.execute(spec, Dialect.postgres)
print(compiled.sql)

# 7. Execute (requires a live DB)
rows = execute_uc.execute(spec, Dialect.postgres, caller_id="svc-etl")
for row in rows:
    print(row)
```

---

## Connection Registration and Allowlist Co-configuration

**Both** the connection repository and `TableAllowlistPolicy` must know about each
`connection_id` before execution. Missing either will raise an error.

```python
CONNECTION_ID = "prod-pg"
URL = "postgresql://user:pass@host/db"

# Register the URL (encrypted at rest in CipherBackedConnectionRepository)
conn_repo.register(CONNECTION_ID, URL)

# Configure the allowlist for the same connection_id
policy = TableAllowlistPolicy({CONNECTION_ID: frozenset({"customers", "orders"})})
```

If `TableAllowlistPolicy` has no entry for a `connection_id`, it raises
`PolicyViolation` (closed-by-default). If `conn_repo` has no entry, `CatalogMiss`
is raised before any SQL is compiled.

---

## Error Handling

All domain errors inherit from `QueryBuilderError`. Catch the specific subclass you
want to handle:

```python
from query_builder import (
    PolicyViolation, CatalogMiss, CompilationError, SourceConnectionError,
)

try:
    rows = execute_uc.execute(spec, Dialect.postgres, caller_id="svc-etl")
except PolicyViolation as exc:
    # Table not in allowlist, or connection_id has no allowlist entry.
    logger.warning("Query rejected by policy: %s", exc)
except CatalogMiss as exc:
    # Unregistered connection_id, or unknown table/column in the spec.
    logger.error("Catalog miss: %s", exc)
except CompilationError as exc:
    # QuerySpec cannot be translated to valid SQL for the requested dialect.
    logger.error("Compilation failed: %s", exc)
except SourceConnectionError as exc:
    # Could not connect to or authenticate against the source database.
    logger.error("Source DB unreachable: %s", exc)
```

---

## Replacing Reference Implementations

All reference implementations satisfy a port interface. Swap them for production
variants by injecting a different implementation at wiring time.

| Port | Library default | Swap for production |
|---|---|---|
| `IQueryCompiler` | `SqlAlchemyCoreCompiler` | Custom compiler (e.g., Spark SQL) |
| `IQueryExecutor` | `SqlAlchemyQueryExecutor` | Any DBAPI-compatible executor |
| `IQueryPolicy` | `DefaultQueryPolicy`, `TableAllowlistPolicy` | Additional domain policies |
| `ICatalogRepository` | `InMemoryCatalogRepository` | Persistent / distributed cache |
| `IConnectionRepository` | `CipherBackedConnectionRepository` | DB-backed or KMS-backed store |
| `IDatasetRepository` | `InMemoryDatasetRepository` | Persistent store (SQL, object store) |
| `IAuditLog` | *(none exported)* | DB writer or event-bus publisher |
| `ICredentialCipher` | `FernetCredentialCipher` | KMS-backed cipher |
| `ISchemaReflector` | `SqlAlchemySchemaReflector` | Custom metadata provider |

`InMemoryConnectionRepository` stores plaintext URLs and is intended **for unit
tests only**. Use `CipherBackedConnectionRepository` in production.

---

## Accessing the HTTP Layer

`create_app()` is not exported from the library root. Install the `[fastapi]` extra
and import it explicitly:

```python
from query_builder.infrastructure.app import create_app

app = create_app(...)
```
