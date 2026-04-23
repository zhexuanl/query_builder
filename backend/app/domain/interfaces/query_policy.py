from abc import ABC, abstractmethod

from domain.entities.query_spec import QuerySpec
from domain.interfaces.catalog_repository import CatalogView


class IQueryPolicy(ABC):
    """Port: validates a ``QuerySpec`` against a governance rule set.

    Implementations inspect the spec (and optionally the catalog) and raise
    ``PolicyViolation`` on the first rule that is violated.  Returning
    ``None`` signals that the spec passes all rules enforced by this policy.

    Policies are meant to be composed: the caller iterates a
    ``list[IQueryPolicy]`` and stops on the first violation.
    """

    @abstractmethod
    def validate(self, spec: QuerySpec, catalog: CatalogView) -> None:
        """Validate ``spec`` against this policy's rules.

        Args:
            spec: The query definition to inspect.
            catalog: The ``CatalogView`` resolved for this compilation pass.
                Structural policies that do not inspect the catalog may ignore
                this argument.

        Returns:
            ``None`` if the spec passes all rules.

        Raises:
            PolicyViolation: If any rule enforced by this policy is violated.
                The message MUST identify the rule and the offending value.
        """
