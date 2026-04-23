## ADDED Requirements

### Requirement: SQLGlot qualify pass catches ambiguous column references before execution
When enabled, the compiler SHALL pass the SQLAlchemy-emitted SQL string through SQLGlot's qualify rewriter after compilation. If SQLGlot raises a parse or qualify error, the compiler MUST raise `CompilationError` with a message identifying the ambiguity. The qualify pass MUST run after SQLAlchemy emits the SQL and MUST NOT alter the SQL returned to the caller if qualification succeeds.

#### Scenario: Unqualified column reference raises CompilationError
- **WHEN** the compiled SQL contains a column reference that SQLGlot cannot resolve to a specific table and the qualify pass is enabled
- **THEN** `CompilationError` is raised before `CompiledQuery` is returned

#### Scenario: Fully qualified SQL passes qualify without error
- **WHEN** the compiled SQL has all column references qualified to their source table alias and the qualify pass is enabled
- **THEN** `CompilationError` is not raised and `CompiledQuery` is returned normally

#### Scenario: Qualify pass disabled by default
- **WHEN** `SqlAlchemyCoreCompiler` is constructed without specifying `enable_sqlglot_qualify`
- **THEN** SQLGlot is not invoked and the qualify pass does not run

#### Scenario: Qualify pass enabled via constructor flag
- **WHEN** `SqlAlchemyCoreCompiler(enable_sqlglot_qualify=True)` is constructed
- **THEN** the qualify pass runs on every `compile()` call
