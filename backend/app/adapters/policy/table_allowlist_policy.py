from collections.abc import Mapping

from domain.entities.query_spec import QuerySpec
from domain.errors import PolicyViolation
from domain.interfaces.catalog_repository import CatalogView
from domain.interfaces.query_policy import IQueryPolicy


class TableAllowlistPolicy(IQueryPolicy):
    """Enforces per-connection table entitlements.

    Each connection may have an approved set of table names.  Any table
    referenced in the spec that is absent from the allowlist raises
    ``PolicyViolation``.  If ``connection_id`` has no entry in ``allowlists``
    all tables are permitted (open-by-default; M5 will tighten this).

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
            return  # unknown connection → open by default

        all_tables = {spec.source.table} | {j.table for j in spec.joins}
        for table in all_tables:
            if table not in approved:
                raise PolicyViolation(
                    f"Table '{table}' is not approved for connection '{spec.connection_id}'"
                )
