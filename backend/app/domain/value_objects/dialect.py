from enum import Enum


class Dialect(str, Enum):
    postgres = "postgres"
    mssql = "mssql"
