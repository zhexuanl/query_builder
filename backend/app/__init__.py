# Tier 1: DSL types — consumers construct these
from .domain.entities.query_spec import QuerySpec
from .domain.value_objects.dialect import Dialect
from .domain.value_objects.filters import FilterGroup, Predicate
from .domain.value_objects.query_parts import JoinDef, SelectField, SortDef
from .domain.value_objects.refs import ColumnRef, ParamRef, ValueRef
from .domain.value_objects.serialisation import QuerySpecCodec

# Tier 2: Errors — consumers catch these
from .domain.errors import (
    CatalogMiss,
    CompilationError,
    DatasetNotFound,
    PolicyViolation,
    QueryBuilderError,
    SourceConnectionError,
)

# Tier 3: Ports — consumers implement or inject these
from .domain.interfaces.audit_log import IAuditLog
from .domain.interfaces.catalog_repository import CatalogView, ICatalogRepository
from .domain.interfaces.connection_repository import IConnectionRepository
from .domain.interfaces.credential_cipher import ICredentialCipher
from .domain.interfaces.dataset_repository import IDatasetRepository
from .domain.interfaces.query_compiler import CompiledQuery, IQueryCompiler
from .domain.interfaces.query_executor import IQueryExecutor
from .domain.interfaces.query_policy import IQueryPolicy

# Tier 4: Reference implementations — consumers use or replace these
from .adapters.catalog.sqlalchemy_schema_reflector import SqlAlchemySchemaReflector
from .adapters.cipher.fernet_credential_cipher import FernetCredentialCipher
from .adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from .adapters.executor.sqlalchemy_query_executor import SqlAlchemyQueryExecutor
from .adapters.policy.default_query_policy import DefaultQueryPolicy
from .adapters.policy.table_allowlist_policy import TableAllowlistPolicy
from .infrastructure.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from .infrastructure.connection.cipher_backed_connection_repository import (
    CipherBackedConnectionRepository,
)
from .infrastructure.connection.in_memory_connection_repository import (
    InMemoryConnectionRepository,
)
from .infrastructure.dataset.in_memory_dataset_repository import InMemoryDatasetRepository
from .use_cases.compile_query import CompileQueryUseCase
from .use_cases.execute_query import ExecuteQueryUseCase
from .use_cases.get_dataset import GetDatasetUseCase
from .use_cases.save_dataset import SaveDatasetUseCase

__all__ = [
    # Tier 1
    "QuerySpec",
    "Dialect",
    "FilterGroup",
    "Predicate",
    "JoinDef",
    "SelectField",
    "SortDef",
    "ColumnRef",
    "ParamRef",
    "ValueRef",
    "QuerySpecCodec",
    # Tier 2
    "QueryBuilderError",
    "PolicyViolation",
    "CompilationError",
    "CatalogMiss",
    "SourceConnectionError",
    "DatasetNotFound",
    # Tier 3
    "IAuditLog",
    "CatalogView",
    "ICatalogRepository",
    "IConnectionRepository",
    "ICredentialCipher",
    "IDatasetRepository",
    "CompiledQuery",
    "IQueryCompiler",
    "IQueryExecutor",
    "IQueryPolicy",
    # Tier 4
    "SqlAlchemySchemaReflector",
    "FernetCredentialCipher",
    "SqlAlchemyCoreCompiler",
    "SqlAlchemyQueryExecutor",
    "DefaultQueryPolicy",
    "TableAllowlistPolicy",
    "InMemoryCatalogRepository",
    "CipherBackedConnectionRepository",
    "InMemoryConnectionRepository",
    "InMemoryDatasetRepository",
    "CompileQueryUseCase",
    "ExecuteQueryUseCase",
    "GetDatasetUseCase",
    "SaveDatasetUseCase",
]
