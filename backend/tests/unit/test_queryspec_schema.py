"""Validate the QuerySpec JSON Schema against representative instances."""
import json
import pathlib

import jsonschema
import pytest

_SCHEMA_PATH = pathlib.Path(__file__).parents[2] / "app" / "schemas" / "queryspec.v1.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def minimal_spec() -> dict:
    return {
        "version": 1,
        "connection_id": "prod-pg",
        "source": {"type": "inner", "table": "customers", "alias": "c", "on": []},
        "select": [
            {
                "kind": "column",
                "source": {"kind": "column", "alias": "c", "name": "id"},
                "label": "id",
            }
        ],
    }


def _validate(instance: dict, schema: dict) -> None:
    jsonschema.validate(instance=instance, schema=schema)


def test_minimal_valid_spec_passes(minimal_spec, schema):
    _validate(minimal_spec, schema)


def test_missing_connection_id_fails(minimal_spec, schema):
    del minimal_spec["connection_id"]
    with pytest.raises(jsonschema.ValidationError):
        _validate(minimal_spec, schema)


def test_bad_dialect_fails(minimal_spec, schema):
    minimal_spec["dialect"] = "oracle"
    with pytest.raises(jsonschema.ValidationError):
        _validate(minimal_spec, schema)


def test_is_null_with_non_null_right_fails(minimal_spec, schema):
    minimal_spec["where"] = {
        "op": "and",
        "items": [
            {
                "left": {"kind": "column", "alias": "c", "name": "status"},
                "op": "is_null",
                "right": {"kind": "value", "value": 1},
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        _validate(minimal_spec, schema)


def test_between_with_three_operands_fails(minimal_spec, schema):
    minimal_spec["where"] = {
        "op": "and",
        "items": [
            {
                "left": {"kind": "column", "alias": "c", "name": "age"},
                "op": "between",
                "right": [
                    {"kind": "value", "value": 1},
                    {"kind": "value", "value": 2},
                    {"kind": "value", "value": 3},
                ],
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        _validate(minimal_spec, schema)


def test_in_with_empty_array_fails(minimal_spec, schema):
    minimal_spec["where"] = {
        "op": "and",
        "items": [
            {
                "left": {"kind": "column", "alias": "c", "name": "status"},
                "op": "in",
                "right": [],
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        _validate(minimal_spec, schema)


def test_nested_filter_group_passes(minimal_spec, schema):
    minimal_spec["where"] = {
        "op": "and",
        "items": [
            {
                "op": "or",
                "items": [
                    {
                        "left": {"kind": "column", "alias": "c", "name": "status"},
                        "op": "=",
                        "right": {"kind": "value", "value": "active"},
                    },
                    {
                        "left": {"kind": "column", "alias": "c", "name": "tier"},
                        "op": "=",
                        "right": {"kind": "value", "value": "gold"},
                    },
                ],
            }
        ],
    }
    _validate(minimal_spec, schema)


def test_filter_group_with_empty_items_fails(minimal_spec, schema):
    minimal_spec["where"] = {"op": "and", "items": []}
    with pytest.raises(jsonschema.ValidationError):
        _validate(minimal_spec, schema)
