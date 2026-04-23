from abc import ABC, abstractmethod

from domain.value_objects.audit_event import AuditEvent


class IAuditLog(ABC):
    @abstractmethod
    def append(self, event: AuditEvent) -> None: ...
