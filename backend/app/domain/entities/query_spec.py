from dataclasses import dataclass

from ..value_objects.filters import FilterGroup
from ..value_objects.query_parts import JoinDef, SelectField, SortDef
from ..value_objects.refs import ColumnRef

_VERSION = 1


@dataclass(frozen=True)
class QuerySpec:
    """Aggregate root representing the full intent of a dataset definition.

    ``QuerySpec`` is immutable once constructed.  SQL is never stored here;
    the compiler derives it from this spec at runtime.

    Attributes:
        connection_id: ID of the source database connection to query.
        source: Primary table, expressed as a ``JoinDef`` with an empty ``on``.
        select: Ordered output columns and aggregates.  Order is preserved in
            the compiled ``SELECT`` list.
        joins: Additional tables joined to the source.  Capped at 3 in v1
            by the policy layer; the domain enforces no hard limit.
        where: Optional top-level filter tree.
        group_by: Columns to group by when aggregates are present.
        order_by: Sort directives referencing labels in ``select``.
        limit: Maximum rows returned.  ``None`` means no limit.  Defaults to
            ``1000`` as a safe default; set explicitly to ``None`` to disable.
        version: Schema version of this spec; used for forward-compatibility.

    Raises:
        ValueError: If ``connection_id`` is empty, ``select`` is empty, ``limit``
            is non-positive, or a non-aggregate ``select`` field is missing from
            ``group_by`` when aggregates are present.

    Example:
        >>> from domain.value_objects.refs import ColumnRef
        >>> from domain.value_objects.query_parts import JoinDef, SelectField
        >>> source = JoinDef(type="inner", table="customers", alias="c", on=())
        >>> field = SelectField(kind="column", source=ColumnRef("c", "id"), label="id")
        >>> spec = QuerySpec(connection_id="conn-1", source=source, select=(field,))
    """

    connection_id: str
    source: JoinDef
    select: tuple[SelectField, ...]
    joins: tuple[JoinDef, ...] = ()
    where: FilterGroup | None = None
    group_by: tuple[ColumnRef, ...] = ()
    order_by: tuple[SortDef, ...] = ()
    limit: int | None = 1000
    version: int = _VERSION

    def __post_init__(self) -> None:
        if not self.connection_id:
            raise ValueError("QuerySpec.connection_id must not be empty")
        if not self.select:
            raise ValueError("QuerySpec must select at least one field")
        if self.limit is not None and self.limit <= 0:
            raise ValueError("QuerySpec.limit must be a positive integer")
        self._validate_group_by()

    def _validate_group_by(self) -> None:
        """Enforce that non-aggregate select fields appear in group_by when aggregates are present.

        Also validates that every group_by column references a known table alias.

        Raises:
            ValueError: On missing group_by entry or unknown alias.
        """
        has_agg = any(f.kind == "agg" for f in self.select)
        if not has_agg:
            return
        known_aliases = self.all_table_aliases
        grouped = set(self.group_by)
        for col in self.group_by:
            if col.alias not in known_aliases:
                raise ValueError(
                    f"group_by column '{col}' references unknown alias '{col.alias}'"
                )
        for f in self.select:
            if f.kind == "column" and f.source not in grouped:
                raise ValueError(
                    f"Column '{f.source}' must appear in group_by because aggregates are present"
                )

    @property
    def all_table_aliases(self) -> frozenset[str]:
        """All table aliases in scope: the source alias plus every join alias.

        Returns:
            A frozenset of alias strings.
        """
        return frozenset({self.source.alias} | {j.alias for j in self.joins})

    @property
    def is_aggregating(self) -> bool:
        """Return ``True`` if any select field is an aggregate.

        Returns:
            Boolean indicating whether the query uses aggregation.
        """
        return any(f.kind == "agg" for f in self.select)
