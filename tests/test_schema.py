import pytest

from metadata_enforcer.schema import SchemaError, compile_schema, load_and_compile


def test_compile_defaults_and_required():
    compiled = compile_schema(
        {
            "title": {},
            "visibility": {"enum": ["public", "private"]},
            "published": {"format": "date", "required": True},
        }
    )
    assert compiled["type"] == "object"
    assert compiled["additionalProperties"] is False
    assert compiled["properties"]["title"] == {"type": "string"}
    assert compiled["properties"]["visibility"]["type"] == "string"
    assert "required" not in compiled["properties"]["published"]
    assert compiled["required"] == ["published"]


def test_compile_nullable_allows_null_without_weakening_string_rules():
    compiled = compile_schema(
        {
            "where-am-i": {"nullable": True},
            "mood": {"enum": ["High", "Medium"], "nullable": True},
        }
    )

    location = compiled["properties"]["where-am-i"]
    assert location == {
        "anyOf": [{"type": "string"}, {"type": "null"}],
    }
    mood = compiled["properties"]["mood"]
    assert mood == {
        "anyOf": [
            {"enum": ["High", "Medium"], "type": "string"},
            {"type": "null"},
        ],
    }


def test_compile_rejects_non_boolean_nullable():
    with pytest.raises(SchemaError, match="'nullable' must be a boolean"):
        compile_schema({"title": {"nullable": "yes"}})


def test_load_rejects_unknown_top_level(tmp_path):
    path = tmp_path / "columns.yaml"
    path.write_text("schema:\n  title: {}\nunique:\n  - [title]\n", encoding="utf-8")
    with pytest.raises(SchemaError, match="unknown top-level"):
        load_and_compile(path)


def test_load_rejects_raw_json_schema_shape(tmp_path):
    path = tmp_path / "columns.yaml"
    path.write_text(
        "schema:\n  properties:\n    title:\n      type: string\n",
        encoding="utf-8",
    )
    with pytest.raises(SchemaError, match="raw JSON Schema"):
        load_and_compile(path)
