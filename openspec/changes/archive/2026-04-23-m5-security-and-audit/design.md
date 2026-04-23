## Context

M4 left two intentional gaps: (1) `InMemoryConnectionRepository` stores connection URLs as plaintext in a Python dict, and (2) `ExecuteQueryUseCase` writes no audit trail. Any real deployment with source-DB credentials is blocked on both. M5 fills them without changing the QuerySpec AST or compilation pipeline.

## Goals / Non-Goals

**Goals:**
- `ICredentialCipher` port + `FernetCredentialCipher` adapter — symmetric encrypt/decrypt of opaque bytes
- `CipherBackedConnectionRepository` — persists `{connection_id: encrypted_url}`, decrypts on `get_url()`
- `IAuditLog` port + two adapters (in-memory for tests, JSON-to-stdout for dev/prod)
- `TableAllowlistPolicy` closed-by-default: unknown `connection_id` → `PolicyViolation`
- `ExecuteQueryUseCase` writes audit record on success and on every caught exception
- `POST /queries/execute` accepts `caller_id`; structured `error_code` in error responses

**Non-Goals:**
- Key rotation, versioned cipher envelopes, or HSM
- Persistent audit storage (database/S3)
- Per-user quotas or rate limiting
- Frontend changes

## Decisions

### Decision 1 — `ICredentialCipher` port signature

**Chosen:**
```python
class ICredentialCipher(ABC):
    def encrypt(self, plaintext: str) -> bytes: ...
    def decrypt(self, ciphertext: bytes) -> str: ...
```

Operates on `str → bytes` (not `bytes → bytes`) because all secrets in this system are URL strings. Returning `bytes` (not `str`) for ciphertext keeps the cipher layer obviously separate from the plaintext domain. Port lives in `domain/interfaces/credential_cipher.py` — no `cryptography` import in domain.

**Layer:** port in `domain/`; `FernetCredentialCipher` in `adapters/cipher/`

### Decision 2 — `CipherBackedConnectionRepository` wraps, not replaces, the M4 port

`IConnectionRepository` interface is unchanged (`get_url`, `register`, raises `CatalogMiss`). The new adapter encrypts on `register()` and decrypts on `get_url()`. The in-memory dict now stores `bytes` values. This keeps the use case and route unchanged except for DI wiring.

No decision-gate needed: additive adapter, same port contract.

**Layer:** `infrastructure/connection/cipher_backed_connection_repository.py`

### Decision 3 — `IAuditLog` port: fire-and-forget append

**Chosen:**
```python
@dataclass(frozen=True)
class AuditEvent:
    caller_id: str
    connection_id: str
    table_names: frozenset[str]
    dialect: str
    outcome: Literal["success", "policy_violation", "compilation_error",
                     "catalog_miss", "source_error", "row_cap_exceeded"]
    row_count: int | None   # None on failure
    duration_ms: int
    timestamp: datetime

class IAuditLog(ABC):
    def append(self, event: AuditEvent) -> None: ...
```

`append()` is synchronous and non-raising — log failures MUST NOT surface to the caller. `AuditEvent` is a frozen dataclass in `domain/` (no framework imports). `caller_id` is an opaque string supplied by the HTTP layer (JWT subject in production; arbitrary string in tests).

**Layer:** `domain/interfaces/audit_log.py`, `domain/value_objects/audit_event.py`; adapters in `adapters/audit/`

### Decision 4 — `TableAllowlistPolicy` closed-by-default

Current: `approved = self._allowlists.get(conn_id); if approved is None: return` (open).
New: `if approved is None: raise PolicyViolation(f"No allowlist configured for connection '{conn_id}'")`.

This is a **behavior-breaking change** to the policy. Existing tests that pass an unknown `connection_id` must be updated. The use case and port contract (`IQueryPolicy`) are unchanged.

### Decision 5 — Audit record written in `ExecuteQueryUseCase`, not in the route

The route layer must not contain business logic. The use case is the only component with access to both `table_names` (derived from the spec) and the execution outcome. The route passes `caller_id` down as an `execute()` argument; the use case builds and appends `AuditEvent`.

### Decision 6 — `caller_id` as a plain string, not a typed principal

An `IIdentityProvider` port would be premature. `caller_id` is an opaque string the route passes in; authentication and JWT validation are M6 concerns. The `AuditEvent` stores it verbatim.

### Decision 7 — No decision-gate required

All new ports have exactly one sensible implementation. No QuerySpec AST, compilation contract, or existing port signatures change (except `execute()` gains `caller_id` parameter, which is additive).

## Risks / Trade-offs

- **`append()` swallows errors** → audit failures are logged to stderr but do not propagate. Risk: silent audit gaps. Mitigation: the JSON-stdout adapter is simple enough to be nearly infallible; a persistent backend is M6.
- **Fernet key in environment variable** → adequate for dev; production needs a secrets manager. Document in README.
- **Closed-by-default breaks existing integration tests** → any test that calls `execute()` against a connection not in the allowlist must add the connection to the allowlist. Update tests as part of M5.
- **`caller_id` is unauthenticated** → any client can claim any identity in M5. Acceptable until JWT middleware lands in M6.

## Migration Plan

1. Add `cryptography` to `pyproject.toml`
2. Implement ports and adapters bottom-up: cipher → connection repo → audit log → use case → route
3. Update `TableAllowlistPolicy` and fix affected tests
4. Update DI wiring in `create_app()`
5. Run full test suite; fix any integration test breakage from closed-by-default

Rollback: revert `table_allowlist_policy.py` to open-by-default; remove cipher and audit wiring from app factory.

## Open Questions

- Should `register()` on `IConnectionRepository` be part of the port contract or remain an implementation detail? (Propose: add to port for M5; remove if M6 replaces with a managed secrets store)
- `duration_ms` in `AuditEvent`: measure wall-clock time of `executor.execute()` only, or full `ExecuteQueryUseCase.execute()` including compile? (Propose: full use-case duration for simpler instrumentation)
