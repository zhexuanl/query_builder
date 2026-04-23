## Library Consumer API: Public Surface, DSL Schema, and Connection Contract

## Why

The query builder is consumed as a library, but it currently has no defined public API surface: no `__init__.py` exports, no formal schema for the `QuerySpec` DSL, and no documented contract for how consumers wire up connection management. A consuming project has no authoritative answer to "what do I import?", "what JSON shape do I POST?", or "how do I register a connection?". This change defines and ships that surface.

## What Changes

- `query_builder/__init__.py` — explicit public exports: all domain types, ports, reference implementations, use cases; anything not exported is private implementation detail
- `QuerySpec` JSON Schema (`schemas/queryspec.v1.json`) — machine-readable DSL schema consumers can use to validate inputs, generate SDKs, or document their integration
- Connection management contract — documented lifecycle: register → resolve → execute; `IConnectionRepository` extension point with `CipherBackedConnectionRepository` as the secure default and `InMemoryConnectionRepository` as the test double
- Consumer integration guide (`docs/consumer_guide.md`) — minimal wiring example: instantiate use cases, register a connection, execute a query, handle errors
- `pyproject.toml` restructured — `query-builder` as an importable package with optional `[fastapi]` extra; FastAPI routes are opt-in, not required

## Capabilities

### New Capabilities
- `library-package`: proper package exports via `__init__.py`; `pyproject.toml` with optional `[fastapi]` extra; type stubs for IDE support
- `queryspec-dsl-schema`: JSON Schema v7 for `QuerySpec` and all nested value objects; versioned at `v1`; ships with the package
- `connection-management-contract`: documented consumer contract for connection registration, URL resolution, and cipher integration; `InMemoryConnectionRepository` as test double, `CipherBackedConnectionRepository` as production default

### Modified Capabilities
- `query-api`: FastAPI routes moved to optional extra; `create_app()` remains but is not imported at library root level

## Impact

- New files: `backend/app/__init__.py` (rewritten with explicit exports), `backend/app/schemas/queryspec.v1.json`, `docs/consumer_guide.md`
- Modified: `pyproject.toml` (optional extras), top-level package structure
- No changes to domain types, ports, use cases, or adapters

## Non-goals

- SDK generation for other languages (JSON Schema enables it; generation is out of scope)
- Versioned API compatibility guarantees beyond v1 schema
- Plugin/extension system
- CLI tooling
