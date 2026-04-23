import json
import sys

from domain.interfaces.audit_log import IAuditLog
from domain.value_objects.audit_event import AuditEvent


class JsonStdoutAuditLog(IAuditLog):
    def append(self, event: AuditEvent) -> None:
        try:
            record = {
                "caller_id": event.caller_id,
                "connection_id": event.connection_id,
                "table_names": sorted(event.table_names),
                "dialect": event.dialect,
                "outcome": event.outcome,
                "row_count": event.row_count,
                "duration_ms": event.duration_ms,
                "timestamp": event.timestamp.isoformat(),
            }
            print(json.dumps(record), file=sys.stdout)
        except Exception:
            pass
