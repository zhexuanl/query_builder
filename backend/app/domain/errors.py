class QueryBuilderError(Exception):
    """Base class for all domain errors in the query builder."""


class PolicyViolation(QueryBuilderError):
    """Raised when a ``QuerySpec`` violates an entitlement or governance rule.

    Examples include accessing an un-approved table, referencing a sensitive
    column without the required permission, or using a disallowed join path.
    """


class CatalogMiss(QueryBuilderError):
    """Raised when a referenced table, column, or join edge is absent from the catalog."""


class SourceConnectionError(QueryBuilderError):
    """Raised when the platform cannot reach or authenticate against a source database."""


class CompilationError(QueryBuilderError):
    """Raised when a ``QuerySpec`` cannot be compiled to valid SQL."""
