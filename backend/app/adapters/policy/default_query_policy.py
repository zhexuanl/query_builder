from domain.entities.query_spec import QuerySpec
from domain.errors import PolicyViolation
from domain.interfaces.catalog_repository import CatalogView
from domain.interfaces.query_policy import IQueryPolicy

_MAX_JOINS = 3
_MAX_LIMIT = 10_000


class DefaultQueryPolicy(IQueryPolicy):
    """Enforces v1 structural rules on every ``QuerySpec``.

    Rules:
    - Maximum ``_MAX_JOINS`` joined tables.
    - Row limit is required and must not exceed ``_MAX_LIMIT``.
    - All ``SelectField.label`` values must be unique.
    - All table aliases (source + joins) must be unique.
    """

    def validate(self, spec: QuerySpec, catalog: CatalogView) -> None:
        """Validate structural rules.

        Args:
            spec: The query definition to inspect.
            catalog: Unused by this policy.

        Raises:
            PolicyViolation: On the first structural rule that is violated.
        """
        self._check_join_count(spec)
        self._check_limit(spec)
        self._check_duplicate_labels(spec)
        self._check_duplicate_aliases(spec)

    def _check_join_count(self, spec: QuerySpec) -> None:
        if len(spec.joins) > _MAX_JOINS:
            raise PolicyViolation(
                f"Query exceeds the maximum of {_MAX_JOINS} joins "
                f"({len(spec.joins)} provided)"
            )

    def _check_limit(self, spec: QuerySpec) -> None:
        if spec.limit is None:
            raise PolicyViolation(
                f"Query must specify an explicit row limit (maximum {_MAX_LIMIT})"
            )
        if spec.limit > _MAX_LIMIT:
            raise PolicyViolation(
                f"Query limit {spec.limit} exceeds the maximum of {_MAX_LIMIT} rows"
            )

    def _check_duplicate_labels(self, spec: QuerySpec) -> None:
        seen: set[str] = set()
        for field in spec.select:
            if field.label in seen:
                raise PolicyViolation(
                    f"Duplicate output label '{field.label}' in SELECT"
                )
            seen.add(field.label)

    def _check_duplicate_aliases(self, spec: QuerySpec) -> None:
        seen: set[str] = {spec.source.alias}
        for join in spec.joins:
            if join.alias in seen:
                raise PolicyViolation(
                    f"Duplicate table alias '{join.alias}' — each join must use a unique alias"
                )
            seen.add(join.alias)
