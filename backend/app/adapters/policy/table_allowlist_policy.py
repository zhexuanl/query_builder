from collections.abc import Mapping

from domain.entities.query_spec import QuerySpec
from domain.errors import PolicyViolation
from domain.interfaces.catalog_repository import CatalogView
from domain.interfaces.query_policy import IQueryPolicy


class TableAllowlistPolicy(IQueryPolicy):
    """Enforces per-connection table entitlements (closed-by-default).

    Behaviour: every ``connection_id`` referenced in a ``QuerySpec`` MUST have an
    explicit entry in the ``allowlists`` mapping, and every table in the spec MUST
    appear in that entry's approved set.  A ``connection_id`` absent from the mapping
    is rejected — there is no implicit "allow-all" fallback.

    Consumers MUST configure an entry for every ``connection_id`` registered in
    ``IConnectionRepository``.  Forgetting to do so raises ``PolicyViolation`` on
    the first execution attempt against that connection.

    Any table referenced in the spec that is absent from the allowlist also raises
    ``PolicyViolation``.

    Attributes:
        _allowlists: Mapping of ``connection_id`` → approved table names.
    """

    def __init__(self, allowlists: Mapping[str, frozenset[str]]) -> None:
        self._allowlists = allowlists

    def validate(self, spec: QuerySpec, catalog: CatalogView) -> None:
        """Validate that all referenced tables are approved for the connection.

        Args:
            spec: The query definition to inspect.
            catalog: Unused by this policy.

        Raises:
            PolicyViolation: If any table in the spec is not in the allowlist.
        """
        approved = self._allowlists.get(spec.connection_id)
        if approved is None:
            raise PolicyViolation(
                f"No allowlist configured for connection '{spec.connection_id}'"
            )

        all_tables = {spec.source.table} | {j.table for j in spec.joins}
        for table in all_tables:
            if table not in approved:
                raise PolicyViolation(
                    f"Table '{table}' is not approved for connection '{spec.connection_id}'"
                )
