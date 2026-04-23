import re
from typing import Any

import sqlalchemy as sa
import sqlglot
from sqlalchemy.dialects import mssql, postgresql
from sqlglot.errors import SqlglotError

from domain.entities.query_spec import QuerySpec
from domain.errors import CatalogMiss, CompilationError
from domain.interfaces.catalog_repository import CatalogView
from domain.interfaces.query_compiler import CompiledQuery, IQueryCompiler
from domain.value_objects.dialect import Dialect
from domain.value_objects.filters import FilterGroup, Predicate
from domain.value_objects.query_parts import SelectField
from domain.value_objects.refs import ColumnRef, Operand, ParamRef, ValueRef

_SA_DIALECTS: dict[Dialect, Any] = {
    Dialect.postgres: postgresql.dialect(),
    Dialect.mssql: mssql.dialect(),
}

_SQLGLOT_DIALECTS: dict[Dialect, str] = {
    Dialect.postgres: "postgres",
    Dialect.mssql: "tsql",
}

# SQLAlchemy with render_postcompile=True emits %(name)s-style named placeholders.
# Substitute them with a numeric literal so SQLGlot sees parseable SQL.
_BIND_PARAM_RE = re.compile(r"%\(\w+\)s")


def _sqlglot_qualify(sql: str, dialect: Dialect) -> None:
    """Parse ``sql`` with SQLGlot and raise ``CompilationError`` on failure.

    Bound parameter placeholders are substituted with a literal before parsing
    so that SQLGlot sees valid SQL syntax. The original SQL is not modified.

    Raises:
        CompilationError: If SQLGlot cannot parse the SQL string.
    """
    parseable = _BIND_PARAM_RE.sub("1", sql)
    sqlglot_dialect = _SQLGLOT_DIALECTS[dialect]
    try:
        sqlglot.parse_one(parseable, dialect=sqlglot_dialect, error_level=sqlglot.ErrorLevel.RAISE)
    except SqlglotError as exc:
        raise CompilationError(f"SQLGlot qualification failed: {exc}") from exc


class SqlAlchemyCoreCompiler(IQueryCompiler):
    """Translates a ``QuerySpec`` to dialect SQL using SQLAlchemy Core.

    Uses ``CatalogView`` to resolve table aliases and columns into SQLAlchemy
    expression objects.  Wraps any ``CatalogMiss`` in ``CompilationError`` so
    callers see a single error type for all compilation failures.

    Args:
        enable_sqlglot_qualify: When ``True``, the emitted SQL is passed
            through SQLGlot's parser after each ``compile()`` call.  Parse
            failures raise ``CompilationError``.  Disabled by default.
    """

    def __init__(self, enable_sqlglot_qualify: bool = False) -> None:
        self._enable_sqlglot_qualify = enable_sqlglot_qualify

    def compile(
        self,
        spec: QuerySpec,
        catalog: CatalogView,
        dialect: Dialect,
    ) -> CompiledQuery:
        """Compile ``spec`` to a ``CompiledQuery`` for ``dialect``.

        Args:
            spec: The validated dataset definition.
            catalog: Provides SQLAlchemy table and column objects for all
                aliases referenced in ``spec``.
            dialect: Target SQL dialect.

        Returns:
            A ``CompiledQuery`` with the SQL template and bound params.

        Raises:
            CompilationError: On any unknown alias, unknown column, or
                internal compilation failure.
        """
        try:
            result = self._compile(spec, catalog, dialect)
        except CatalogMiss as exc:
            raise CompilationError(str(exc)) from exc
        if self._enable_sqlglot_qualify:
            _sqlglot_qualify(result.sql, dialect)
        return result

    def _compile(
        self,
        spec: QuerySpec,
        catalog: CatalogView,
        dialect: Dialect,
    ) -> CompiledQuery:
        label_exprs: dict[str, Any] = {}
        columns: list[Any] = []
        for field in spec.select:
            expr = _render_select_field(field, catalog)
            label_exprs[field.label] = expr
            columns.append(expr)

        from_clause = _render_from(spec, catalog)
        stmt = sa.select(*columns).select_from(from_clause)

        if spec.where:
            stmt = stmt.where(_render_filter(spec.where, catalog))

        if spec.group_by:
            stmt = stmt.group_by(
                *[catalog.column(c.alias, c.name) for c in spec.group_by]
            )

        if spec.order_by:
            stmt = stmt.order_by(*[
                (sa.desc if s.direction == "desc" else sa.asc)(label_exprs[s.label])
                for s in spec.order_by
            ])

        if spec.limit is not None:
            stmt = stmt.limit(spec.limit)

        sa_dialect = _SA_DIALECTS[dialect]
        compiled = stmt.compile(
            dialect=sa_dialect,
            compile_kwargs={"render_postcompile": True},
        )
        return CompiledQuery(
            sql=str(compiled),
            params=dict(compiled.params),
            dialect=dialect,
        )


def _render_select_field(field: SelectField, catalog: CatalogView) -> Any:
    """Render a ``SelectField`` to a labelled SQLAlchemy expression.

    Args:
        field: The field definition to render.
        catalog: Used to resolve the source column.

    Returns:
        A SQLAlchemy ``Label`` wrapping either a column or aggregate function.

    Raises:
        CompilationError: If ``field.func`` is set to an unknown value.
    """
    col = catalog.column(field.source.alias, field.source.name)
    if field.kind == "column":
        return col.label(field.label)
    match field.func:
        case "count":
            return sa.func.count(col).label(field.label)
        case "count_distinct":
            return sa.func.count(col.distinct()).label(field.label)
        case "sum":
            return sa.func.sum(col).label(field.label)
        case "avg":
            return sa.func.avg(col).label(field.label)
        case "min":
            return sa.func.min(col).label(field.label)
        case "max":
            return sa.func.max(col).label(field.label)
        case _:
            raise CompilationError(f"Unknown aggregate function: {field.func!r}")


def _render_from(spec: QuerySpec, catalog: CatalogView) -> Any:
    """Build the FROM clause including all chained joins.

    Args:
        spec: The query definition.
        catalog: Resolves table aliases to SQLAlchemy objects.

    Returns:
        A SQLAlchemy ``FromClause`` (table alias or chained join).
    """
    from_clause = catalog.sa_table(spec.source.alias)
    for join in spec.joins:
        join_table = catalog.sa_table(join.alias)
        on_parts = [_render_predicate(p, catalog) for p in join.on]
        on_clause = sa.and_(*on_parts) if on_parts else sa.true()
        if join.type == "left":
            from_clause = from_clause.outerjoin(join_table, on_clause)
        else:
            from_clause = from_clause.join(join_table, on_clause)
    return from_clause


def _operand(o: Operand, catalog: CatalogView) -> Any:
    """Render a single operand as a SQLAlchemy expression or Python scalar.

    ``ValueRef`` returns the raw Python scalar so that SQLAlchemy names the
    generated ``BindParameter`` after the comparison column, producing
    readable param names (e.g. ``status_1``) rather than ``param_1``.

    Args:
        o: The operand to render.
        catalog: Used to resolve ``ColumnRef`` values.

    Returns:
        A SQLAlchemy expression, a ``BindParameter``, or a Python scalar.
    """
    if isinstance(o, ColumnRef):
        return catalog.column(o.alias, o.name)
    if isinstance(o, ParamRef):
        return sa.bindparam(o.name)
    return o.value


def _render_predicate(pred: Predicate, catalog: CatalogView) -> Any:
    """Render a single ``Predicate`` to a SQLAlchemy boolean expression.

    Args:
        pred: The predicate to render.
        catalog: Used to resolve column references.

    Returns:
        A SQLAlchemy boolean expression.
    """
    left = catalog.column(pred.left.alias, pred.left.name)
    match pred.op:
        case "is_null":
            return left.is_(None)
        case "is_not_null":
            return left.isnot(None)
        case "in":
            return left.in_([_operand(r, catalog) for r in pred.right])
        case "not_in":
            return left.not_in([_operand(r, catalog) for r in pred.right])
        case "between":
            lo, hi = pred.right
            return left.between(_operand(lo, catalog), _operand(hi, catalog))
        case "like":
            return left.like(_operand(pred.right, catalog))
        case "not_like":
            return left.not_like(_operand(pred.right, catalog))
        case "=":
            return left == _operand(pred.right, catalog)
        case "!=":
            return left != _operand(pred.right, catalog)
        case ">":
            return left > _operand(pred.right, catalog)
        case ">=":
            return left >= _operand(pred.right, catalog)
        case "<":
            return left < _operand(pred.right, catalog)
        case "<=":
            return left <= _operand(pred.right, catalog)
        case _:
            raise CompilationError(f"Unknown operator: {pred.op!r}")


def _render_filter(node: FilterGroup | Predicate, catalog: CatalogView) -> Any:
    """Recursively render a filter tree to a SQLAlchemy boolean expression.

    Args:
        node: A ``FilterGroup`` or leaf ``Predicate``.
        catalog: Passed through to ``_render_predicate``.

    Returns:
        A SQLAlchemy ``and_``/``or_`` clause or a leaf comparison expression.
    """
    if isinstance(node, Predicate):
        return _render_predicate(node, catalog)
    children = [_render_filter(item, catalog) for item in node.items]
    return sa.and_(*children) if node.op == "and" else sa.or_(*children)
