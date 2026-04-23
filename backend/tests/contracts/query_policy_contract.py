"""Contract test base class for IQueryPolicy implementations.

To test a custom IQueryPolicy, subclass ``QueryPolicyContract`` and
override the ``policy``, ``valid_spec``, and ``invalid_spec`` fixtures.
"""
import pytest

from domain.errors import PolicyViolation
from domain.interfaces.query_policy import IQueryPolicy


class QueryPolicyContract:
    """Abstract contract test suite for IQueryPolicy.

    Subclasses must override the ``policy``, ``valid_spec``, and
    ``invalid_spec`` fixtures.  The base tests verify that all implementations
    share the same observable behaviour.
    """

    @pytest.fixture
    def policy(self) -> IQueryPolicy:
        raise NotImplementedError("Subclass must provide an IQueryPolicy instance")

    @pytest.fixture
    def valid_spec(self):
        raise NotImplementedError("Subclass must provide a spec that passes the policy")

    @pytest.fixture
    def invalid_spec(self):
        raise NotImplementedError("Subclass must provide a spec that violates the policy")

    @pytest.fixture
    def catalog(self):
        from tests.fakes.in_memory_catalog import make_catalog
        return make_catalog(("c", "customers", ["id"]))

    def test_valid_spec_returns_none(self, policy, valid_spec, catalog):
        result = policy.validate(valid_spec, catalog)
        assert result is None

    def test_violation_raises_not_returns(self, policy, invalid_spec, catalog):
        with pytest.raises(PolicyViolation):
            policy.validate(invalid_spec, catalog)
