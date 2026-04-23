from dataclasses import dataclass
from typing import Literal

from .filters import Predicate
from .refs import ColumnRef, _require_identifier


@dataclass(frozen=True)
class JoinDef:
    """Describes a single table join, or the primary source table when ``on`` is empty.

    Attributes:
        type: Join variant — ``"inner"`` or ``"left"``.
        table: Qualified table name as it appears in the source database
            (e.g. ``"customers"`` or ``"dbo.orders"``).  May include a schema
            prefix; no identifier validation is applied here because the catalog
            layer owns table name resolution.
        alias: Short SQL alias assigned to the table in this query.  Must be a
            valid SQL identifier.
        on: Predicates that form the ``ON`` clause.  Empty tuple is valid for
            the primary source table.

    Raises:
        ValueError: If ``table`` is empty or ``alias`` is not a valid SQL
            identifier.
    """

    type: Literal["inner", "left"]
    table: str
    alias: str
    on: tuple[Predicate, ...]

    def __post_init__(self) -> None:
        if not self.table:
            raise ValueError("JoinDef.table must not be empty")
        _require_identifier(self.alias, "JoinDef.alias")


@dataclass(frozen=True)
class SelectField:
    """A single output column — either a plain column reference or an aggregate.

    Attributes:
        kind: ``"column"`` for a direct column projection, ``"agg"`` for an
            aggregate expression.
        source: The column being projected or aggregated.
        label: Output alias used in ``SELECT ... AS <label>``.  Must be a
            valid SQL identifier.
        func: Aggregate function name; required when ``kind="agg"``, forbidden
            when ``kind="column"``.

    Raises:
        ValueError: On ``kind``/``func`` mismatch or an invalid ``label``.
    """

    kind: Literal["column", "agg"]
    source: ColumnRef
    label: str
    func: Literal["count", "count_distinct", "sum", "avg", "min", "max"] | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.label, "SelectField.label")
        if self.kind == "agg" and self.func is None:
            raise ValueError("SelectField with kind='agg' requires func to be set")
        if self.kind == "column" and self.func is not None:
            raise ValueError("SelectField with kind='column' must not set func")


@dataclass(frozen=True)
class SortDef:
    """A sort directive referencing an output label from ``SelectField``.

    Attributes:
        label: Must match a ``SelectField.label`` in the enclosing ``QuerySpec``.
        direction: ``"asc"`` (default) or ``"desc"``.

    Raises:
        ValueError: If ``label`` is not a valid SQL identifier.
    """

    label: str
    direction: Literal["asc", "desc"] = "asc"

    def __post_init__(self) -> None:
        _require_identifier(self.label, "SortDef.label")
