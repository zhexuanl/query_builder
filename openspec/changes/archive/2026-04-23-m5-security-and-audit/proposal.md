## M5: Security and Audit

## Why

M4 shipped a working execute endpoint, but it stores connection URLs as plain strings in memory and logs nothing. Before this system can be used with real source databases, credentials must be encrypted at rest and every query execution must be traceable for compliance.

## What Changes

- New `ICredentialCipher` port: encrypt/decrypt sensitive connection strings; Fernet-based adapter for local/dev
- `IConnectionRepository` upgraded: replaces the M4 in-memory dict with a cipher-backed store that encrypts URLs before storage and decrypts on retrieval
- New `IAuditLog` port: append-only write of who ran what query, when, and with what outcome; in-memory adapter for unit tests, stdout/JSON adapter for dev
- `TableAllowlistPolicy` tightened: unknown `connection_id` now raises `PolicyViolation` (closed by default) instead of open by default
- `POST /queries/execute` extended: accepts `caller_id` in the request body; route passes it to the use case for audit log entries
- `ExecuteQueryUseCase` extended: writes an audit record after each execute (success or failure)

## Capabilities

### New Capabilities
- `credential-cipher`: `ICredentialCipher` port + Fernet adapter; encrypt/decrypt opaque credential blobs
- `audit-log`: `IAuditLog` port + in-memory and JSON-stdout adapters; structured append-only event records

### Modified Capabilities
- `query-execution`: `IConnectionRepository` now requires cipher-backed storage; `get_url()` decrypts on read; `register()` encrypts on write
- `query-policy`: `TableAllowlistPolicy` changes from open-by-default to closed-by-default for unknown connections
- `execute-query-use-case`: `execute()` now requires `caller_id`; writes audit record on success and failure
- `query-api`: `QuerySpecRequest` gains `caller_id` field; error responses gain structured `error_code`

## Impact

- New files: `domain/interfaces/credential_cipher.py`, `domain/interfaces/audit_log.py`, `adapters/cipher/fernet_credential_cipher.py`, `adapters/audit/json_stdout_audit_log.py`, `infrastructure/connection/cipher_backed_connection_repository.py`, `tests/fakes/fake_credential_cipher.py`, `tests/fakes/fake_audit_log.py`
- Modified: `adapters/policy/table_allowlist_policy.py`, `use_cases/execute_query.py`, `infrastructure/api/routes/queries.py`, `infrastructure/api/models/query_models.py`, `infrastructure/app.py`
- New dependency: `cryptography` (for Fernet)

## Non-goals

- Multi-key rotation or HSM integration (post-M5)
- Persistent audit log backend (database/S3 — M6)
- Per-user row quotas or billing metering
- Frontend credential management UI
- SQLGlot lint pass (M6)
