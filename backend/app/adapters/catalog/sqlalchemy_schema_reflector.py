import sqlalchemy as sa

from domain.errors import SourceConnectionError
from domain.interfaces.catalog_repository import CatalogView
from domain.interfaces.schema_reflector import ISchemaReflector

from .sqlalchemy_catalog_view import SqlAlchemyCatalogView

class SqlAlchemySchemaReflector(ISchemaReflector):
    """Reflects table and column schema from a live source database.

    Creates a short-lived engine per call, reflects the requested tables via
    ``MetaData.reflect``, then immediately disposes the engine.  Each table is
    aliased under its own name so that ``catalog.sa_table("customers")`` returns
    the expression for ``customers AS customers``.

    Example:
        >>> reflector = SqlAlchemySchemaReflector()
        >>> catalog = reflector.reflect(
        ...     "postgresql://user:pw@host/db",
        ...     frozenset({"customers", "transactions"}),
        ... )
        >>> catalog.sa_table("customers")
    """

    def reflect(self, url: str, table_names: frozenset[str]) -> CatalogView:
        """Reflect schema for the requested tables and return a catalog view.

        Args:
            url: Database connection URL (e.g. ``postgresql://user:pw@host/db``).
            table_names: Names of the tables to reflect.

        Returns:
            A ``SqlAlchemyCatalogView`` keyed by table name, each aliased under
            its own name.

        Raises:
            SourceConnectionError: If the database is unreachable, credentials
                are invalid, or a requested table does not exist in the source.
        """
        safe_url = sa.engine.make_url(url).render_as_string(hide_password=True)
        engine = sa.create_engine(url)
        try:
            meta = sa.MetaData()
            with engine.connect() as conn:
                meta.reflect(bind=conn, only=list(table_names))
        except Exception as exc:
            raise SourceConnectionError(
                f"Failed to reflect schema from '{safe_url}': {exc}"
            ) from exc
        finally:
            engine.dispose()

        missing = table_names - set(meta.tables)
        if missing:
            raise SourceConnectionError(
                f"Tables not found in source database: {sorted(missing)}"
            )

        aliased: dict[str, sa.sql.expression.Alias] = {
            name: meta.tables[name].alias(name) for name in table_names
        }
        return SqlAlchemyCatalogView(aliased)
