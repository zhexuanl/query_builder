from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class AuditEvent:
    caller_id: str
    connection_id: str
    table_names: frozenset[str]
    dialect: str
    outcome: Literal[
        "success",
        "policy_violation",
        "compilation_error",
        "catalog_miss",
        "source_error",
        "row_cap_exceeded",
    ]
    row_count: int | None
    duration_ms: int
    timestamp: datetime
