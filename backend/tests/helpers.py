import re


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
