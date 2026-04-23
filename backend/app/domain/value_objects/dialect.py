from enum import Enum


class Dialect(str, Enum):
    """Target SQL dialect for query compilation.

    Attributes:
        postgres: PostgreSQL.
        mssql: Microsoft SQL Server.
    """

    postgres = "postgres"
    mssql = "mssql"
