## 1. Dependencies and New Ports

- [x] 1.1 Add `cryptography` to `pyproject.toml` / `requirements.txt`; verify `from cryptography.fernet import Fernet` imports cleanly
- [x] 1.2 Create `domain/interfaces/credential_cipher.py` — `ICredentialCipher` ABC with `encrypt(plaintext: str) -> bytes` and `decrypt(ciphertext: bytes) -> str`
- [x] 1.3 Create `domain/value_objects/audit_event.py` — frozen dataclass `AuditEvent` with all fields; `outcome` typed as `Literal[...]`
- [x] 1.4 Create `domain/interfaces/audit_log.py` — `IAuditLog` ABC with `append(event: AuditEvent) -> None`
- [x] 1.5 Add `register(connection_id: str, url: str) -> None` abstract method to `domain/interfaces/connection_repository.py`

## 2. Adapters and Fakes

- [x] 2.1 Create `adapters/cipher/fernet_credential_cipher.py` — `FernetCredentialCipher(key: bytes)`; validate key at construction; `encrypt`/`decrypt` via `Fernet`; wrap `InvalidToken` as `ValueError`
- [x] 2.2 Create `adapters/audit/json_stdout_audit_log.py` — `JsonStdoutAuditLog`; writes one JSON line per event; `append()` swallows all exceptions
- [x] 2.3 Create `tests/fakes/fake_credential_cipher.py` — `FakeCredentialCipher` that base64-encodes (not real encryption; predictable for tests)
- [x] 2.4 Create `tests/fakes/fake_audit_log.py` — `FakeAuditLog` with `events: list[AuditEvent]`; `append()` stores events; swallows exceptions
- [x] 2.5 Create `infrastructure/connection/cipher_backed_connection_repository.py` — `CipherBackedConnectionRepository(cipher: ICredentialCipher)`; `register()` encrypts before storage; `get_url()` decrypts; raises `CatalogMiss` for unknown IDs

## 3. Policy Change: Closed-by-Default

- [x] 3.1 Update `adapters/policy/table_allowlist_policy.py` — change `if approved is None: return` to `raise PolicyViolation(...)` for unknown connections
- [x] 3.2 Update `tests/unit/policy/test_default_query_policy.py` and `tests/unit/use_cases/` — fix any tests that relied on open-by-default behaviour
- [x] 3.3 Add test `test_unknown_connection_id_raises` in `tests/unit/policy/test_table_allowlist_policy.py` (if not already present)

## 4. ExecuteQueryUseCase: caller_id and Audit

- [x] 4.1 Update `use_cases/execute_query.py` — add `audit_log: IAuditLog` to `__init__`; add `caller_id: str` to `execute()`; record `AuditEvent` in all terminal branches (success and all exceptions); swallow `IAuditLog.append()` errors
- [x] 4.2 Update unit tests in `tests/unit/use_cases/test_execute_query.py`:
  - Success path: assert `fake_audit_log.events[0].outcome == "success"` with correct `row_count`
  - Each error path: assert correct `outcome` in audit event and exception still propagates
  - Audit log failure: assert use-case result is unaffected when `append()` raises
  - Row-cap exceeded: assert `outcome == "row_cap_exceeded"`

## 5. API Layer: caller_id and error_code

- [x] 5.1 Update `infrastructure/api/models/query_models.py` — add mandatory `caller_id: str` to `QuerySpecRequest`; add `ErrorResponse(error_code: str, detail: str | None)` Pydantic model
- [x] 5.2 Update `infrastructure/api/routes/queries.py` — pass `caller_id` to use case; return `ErrorResponse` with structured `error_code` for each exception type; `SourceConnectionError` → `error_code="SOURCE_UNAVAILABLE"` with no detail
- [x] 5.3 Update `tests/unit/api/test_queries_route.py` — assert `error_code` field in all error responses; assert `caller_id` absence returns 422

## 6. DI Wiring and Integration

- [x] 6.1 Update `infrastructure/app.py` — wire `FernetCredentialCipher` (key from env), `CipherBackedConnectionRepository`, `JsonStdoutAuditLog` into `ExecuteQueryUseCase`; done signal: `create_app(config)` returns without raising
- [x] 6.2 Update integration test `tests/integration/test_execute_query_integration.py` — register connection via `register()`, add to allowlist, assert audit event written
- [x] 6.3 Run full test suite (`pytest backend/tests/`) — all tests green before commit
