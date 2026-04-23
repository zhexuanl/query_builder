## ADDED Requirements

### Requirement: SqlAlchemyCoreCompiler supports an optional SQLGlot qualify pass
`SqlAlchemyCoreCompiler` SHALL accept `enable_sqlglot_qualify: bool = False` at construction. When `True`, the adapter SHALL pass the emitted SQL string through SQLGlot's qualify rewriter after each `compile()` call. Qualify errors SHALL be raised as `CompilationError`. The `IQueryCompiler` port contract is unchanged.

#### Scenario: Compiler constructed without flag behaves identically to M1–M5
- **WHEN** `SqlAlchemyCoreCompiler()` is constructed without `enable_sqlglot_qualify`
- **THEN** all existing M1 golden tests pass without modification

#### Scenario: Qualify errors from SQLGlot raise CompilationError
- **WHEN** `SqlAlchemyCoreCompiler(enable_sqlglot_qualify=True).compile(spec, catalog, dialect)` produces SQL that SQLGlot cannot qualify
- **THEN** `CompilationError` is raised with a message from SQLGlot

#### Scenario: Successful qualify does not alter the returned SQL
- **WHEN** the qualify pass runs without error
- **THEN** the `CompiledQuery.sql` value is the original SQLAlchemy-emitted string (not SQLGlot's re-rendered output) to preserve dialect fidelity
