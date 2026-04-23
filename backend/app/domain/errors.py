class QueryBuilderError(Exception):
    """Base for all domain errors."""


class PolicyViolation(QueryBuilderError):
    """A query spec violated an entitlement or governance rule."""


class CatalogMiss(QueryBuilderError):
    """A referenced table, column, or join edge was not found in the catalog."""


class SourceConnectionError(QueryBuilderError):
    """Could not reach or authenticate against the source DB."""


class CompilationError(QueryBuilderError):
    """The query spec could not be compiled to SQL."""
