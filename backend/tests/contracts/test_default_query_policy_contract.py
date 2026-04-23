"""Smoke-check: DefaultQueryPolicy satisfies QueryPolicyContract."""
import pytest

from adapters.policy.default_query_policy import DefaultQueryPolicy
from domain.entities.query_spec import QuerySpec
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef
from tests.contracts.query_policy_contract import QueryPolicyContract


class TestDefaultQueryPolicyContract(QueryPolicyContract):
    @pytest.fixture
    def policy(self):
        return DefaultQueryPolicy()

    @pytest.fixture
    def valid_spec(self):
        return QuerySpec(
            connection_id="conn-1",
            source=JoinDef(type="inner", table="customers", alias="c", on=()),
            select=(SelectField(kind="column", source=ColumnRef("c", "id"), label="id"),),
            limit=100,
        )

    @pytest.fixture
    def invalid_spec(self):
        # limit=None violates DefaultQueryPolicy
        return QuerySpec(
            connection_id="conn-1",
            source=JoinDef(type="inner", table="customers", alias="c", on=()),
            select=(SelectField(kind="column", source=ColumnRef("c", "id"), label="id"),),
            limit=None,
        )
