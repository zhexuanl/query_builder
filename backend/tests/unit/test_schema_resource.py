"""Verify the QuerySpec JSON Schema is accessible as a package resource."""
import importlib.resources
import json
import pathlib


def test_schema_accessible_via_importlib_resources():
    schema_text = importlib.resources.files("query_builder").joinpath(
        "schemas/queryspec.v1.json"
    ).read_text(encoding="utf-8")
    schema = json.loads(schema_text)
    assert "$schema" in schema
    assert schema.get("title") == "QuerySpec"


def test_schema_file_exists_on_disk():
    # Fallback: verify the schema file is present on disk relative to the app package.
    schema_path = pathlib.Path(__file__).parents[2] / "app" / "schemas" / "queryspec.v1.json"
    assert schema_path.exists(), f"Schema not found at {schema_path}"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema.get("title") == "QuerySpec"
    assert "$schema" in schema
