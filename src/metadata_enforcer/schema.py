"""Load columns.yaml envelopes and compile the human dialect to JSON Schema."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# If these appear as keys under schema:, the user likely pasted raw JSON Schema.
_RAW_JSON_SCHEMA_ROOT_KEYS = frozenset(
    {
        "$schema",
        "$id",
        "properties",
        "additionalProperties",
        "patternProperties",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "if",
        "then",
        "else",
        "dependentRequired",
        "dependentSchemas",
    }
)


class SchemaError(Exception):
    """Invalid columns.yaml envelope or field map."""


def load_envelope(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SchemaError(f"schema not found: {path}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SchemaError(f"invalid YAML in {path}: {exc}") from exc

    if data is None:
        raise SchemaError(f"empty schema file: {path}")
    if not isinstance(data, dict):
        raise SchemaError(f"schema envelope must be a mapping: {path}")

    unknown = set(data) - {"schema"}
    if unknown:
        keys = ", ".join(sorted(unknown))
        raise SchemaError(
            f"unknown top-level key(s) in {path}: {keys}. "
            "v1 only supports 'schema:'. "
            "See ROADMAP.md for future keys like unique/references."
        )
    if "schema" not in data:
        raise SchemaError(f"missing top-level 'schema:' in {path}")

    field_map = data["schema"]
    if not isinstance(field_map, dict):
        raise SchemaError(f"'schema:' must be a mapping of field names: {path}")

    suspicious = sorted(_RAW_JSON_SCHEMA_ROOT_KEYS & set(field_map))
    if suspicious:
        raise SchemaError(
            f"'schema:' in {path} looks like raw JSON Schema "
            f"(found {', '.join(suspicious)}). "
            "Use a field map: schema:\\n  title: {{}}\\n  visibility:\\n    enum: [public, private]"
        )

    return data


def compile_schema(field_map: dict[str, Any]) -> dict[str, Any]:
    """Compile human field map → Draft 2020-12 object schema."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, spec in field_map.items():
        if not isinstance(name, str) or not name:
            raise SchemaError(f"invalid field name: {name!r}")

        if spec is None:
            spec = {}
        if not isinstance(spec, dict):
            raise SchemaError(
                f"field {name!r} must be a mapping of constraints, got {type(spec).__name__}"
            )

        required_flag = spec.get("required", False)
        if not isinstance(required_flag, bool):
            raise SchemaError(f"field {name!r}: 'required' must be a boolean")
        nullable = spec.get("nullable", False)
        if not isinstance(nullable, bool):
            raise SchemaError(f"field {name!r}: 'nullable' must be a boolean")

        prop = deepcopy(spec)
        prop.pop("required", None)
        prop.pop("nullable", None)
        if "type" not in prop:
            prop["type"] = "string"
        if nullable:
            prop = {"anyOf": [prop, {"type": "null"}]}

        properties[name] = prop
        if required_flag:
            required.append(name)

    compiled: dict[str, Any] = {
        "$schema": JSON_SCHEMA_DIALECT,
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        compiled["required"] = required
    return compiled


def load_and_compile(path: Path) -> dict[str, Any]:
    envelope = load_envelope(path)
    return compile_schema(envelope["schema"])
