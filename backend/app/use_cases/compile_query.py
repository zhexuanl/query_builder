from domain.entities.query_spec import QuerySpec
from domain.interfaces.catalog_repository import ICatalogRepository
from domain.interfaces.query_compiler import CompiledQuery, IQueryCompiler
from domain.interfaces.query_policy import IQueryPolicy
from domain.value_objects.dialect import Dialect


class CompileQueryUseCase:
    """Orchestrates catalog resolution, policy enforcement, and SQL compilation.

    This is the primary entry point for converting a ``QuerySpec`` into a
    ``CompiledQuery``.  It chains three injected ports in order:

    1. ``ICatalogRepository.view_for`` — resolve table metadata.
    2. Each ``IQueryPolicy.validate`` — enforce governance rules.
    3. ``IQueryCompiler.compile`` — produce dialect SQL + params.

    Attributes:
        _catalog_repo: Supplies ``CatalogView`` instances for compilation.
        _policies: Ordered list of policies applied before compilation.
        _compiler: Translates the ``QuerySpec`` to SQL.

    Example:
        >>> use_case = CompileQueryUseCase(
        ...     catalog_repo=repo,
        ...     policies=[DefaultQueryPolicy(), TableAllowlistPolicy(allowlists)],
        ...     compiler=SqlAlchemyCoreCompiler(),
        ... )
        >>> result = use_case.execute(spec, Dialect.postgres)
    """

    def __init__(
        self,
        catalog_repo: ICatalogRepository,
        policies: list[IQueryPolicy],
        compiler: IQueryCompiler,
    ) -> None:
        self._catalog_repo = catalog_repo
        self._policies = policies
        self._compiler = compiler

    def execute(self, spec: QuerySpec, dialect: Dialect) -> CompiledQuery:
        """Validate and compile ``spec`` for ``dialect``.

        Args:
            spec: The validated dataset definition.
            dialect: Target SQL dialect.

        Returns:
            A ``CompiledQuery`` with the dialect SQL template and bound params.

        Raises:
            CatalogMiss: If any referenced table or column is absent from the
                catalog.
            PolicyViolation: If the spec violates any configured policy.
            CompilationError: If the compiler cannot produce valid SQL.
        """
        table_names = frozenset(
            {spec.source.table} | {j.table for j in spec.joins}
        )
        catalog = self._catalog_repo.view_for(spec.connection_id, table_names)

        for policy in self._policies:
            policy.validate(spec, catalog)

        return self._compiler.compile(spec, catalog, dialect)
