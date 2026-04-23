import re
from dataclasses import dataclass

_IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def _require_identifier(value: str, field: str) -> None:
    """Validate that a string is a safe SQL identifier.

    Args:
        value: The string to validate.
        field: Human-readable field name used in the error message.

    Raises:
        ValueError: If ``value`` does not match ``[a-zA-Z_][a-zA-Z0-9_]*``.
    """
    if not _IDENTIFIER_RE.match(value):
        raise ValueError(f"{field} must be a valid SQL identifier, got: {value!r}")


@dataclass(frozen=True)
class ColumnRef:
    """A reference to a single column identified by its table alias and column name.

    Attributes:
        alias: Table alias in the query (e.g. ``"c"`` for customers).
        name: Column name (e.g. ``"customer_id"``).

    Raises:
        ValueError: If ``alias`` or ``name`` is not a valid SQL identifier.

    Example:
        >>> ref = ColumnRef(alias="c", name="customer_id")
        >>> str(ref)
        'c.customer_id'
    """

    alias: str
    name: str

    def __post_init__(self) -> None:
        _require_identifier(self.alias, "ColumnRef.alias")
        _require_identifier(self.name, "ColumnRef.name")

    def __str__(self) -> str:
        return f"{self.alias}.{self.name}"


@dataclass(frozen=True)
class ParamRef:
    """A named runtime parameter whose value is supplied at execution time.

    Parameters are never inlined into SQL — the compiler always emits a
    bound-parameter placeholder for them.

    Attributes:
        name: Parameter name; must be a valid SQL identifier.

    Raises:
        ValueError: If ``name`` is not a valid SQL identifier.
    """

    name: str

    def __post_init__(self) -> None:
        _require_identifier(self.name, "ParamRef.name")


@dataclass(frozen=True)
class ValueRef:
    """A literal scalar value embedded in the query spec.

    The compiler parameterises all ``ValueRef`` instances — they are never
    interpolated as raw strings.  ``None`` compiles to a SQL ``NULL`` literal.

    Attributes:
        value: The scalar value, or ``None`` for SQL ``NULL``.
    """

    value: str | int | float | bool | None


type Operand = ColumnRef | ParamRef | ValueRef
