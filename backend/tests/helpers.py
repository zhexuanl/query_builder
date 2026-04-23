import re

from domain.entities.query_spec import QuerySpec
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef


def simple_spec(
    *,
    connection_id: str = "conn-1",
    alias: str = "u",
    table: str = "users",
    columns: list[str] | None = None,
) -> QuerySpec:
    """Build a minimal valid ``QuerySpec`` for testing."""
    if columns is None:
        columns = ["id"]
    select = tuple(
        SelectField(kind="column", source=ColumnRef(alias=alias, name=col), label=col)
        for col in columns
    )
    source = JoinDef(type="inner", table=table, alias=alias, on=())
    return QuerySpec(connection_id=connection_id, source=source, select=select)


def normalize_sql(sql: str) -> str:
    """Collapse whitespace in a SQL string for stable text comparisons.

    Strips leading/trailing whitespace and replaces any internal run of
    whitespace characters (spaces, tabs, newlines) with a single space.

    Args:
        sql: Raw SQL string from a compiler or test fixture.

    Returns:
        A single-line, whitespace-normalised SQL string.

    Example:
        >>> normalize_sql("SELECT  foo  FROM\\n  bar ")
        'SELECT foo FROM bar'
    """
    return re.sub(r"\s+", " ", sql.strip())
