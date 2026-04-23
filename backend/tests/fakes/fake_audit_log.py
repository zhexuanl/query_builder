from domain.interfaces.audit_log import IAuditLog
from domain.value_objects.audit_event import AuditEvent


class FakeAuditLog(IAuditLog):
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)
