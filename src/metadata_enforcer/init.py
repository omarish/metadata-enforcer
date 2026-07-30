"""Generate a starting columns.yaml by scanning note frontmatter."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import frontmatter
import yaml

from metadata_enforcer.discover import iter_markdown_files
from metadata_enforcer.wikilink import unwrap_wikilink

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATE_TIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"  # coarse ISO-ish
)

# Suggest enum when distinct string values are few and the field is reused.
_ENUM_MAX_DISTINCT = 10
_ENUM_MIN_OCCURRENCES = 2
_ENUM_MAX_VALUE_LEN = 64


def generate_schema(
    root: Path,
    *,
    recursive: bool,
) -> dict[str, Any]:
    """Return a columns.yaml envelope inferred from notes under root."""
    files = iter_markdown_files(root, recursive=recursive)
    values_by_key: dict[str, list[Any]] = defaultdict(list)

    for path in files:
        try:
            post = frontmatter.load(path)
        except Exception:  # noqa: BLE001 — skip unreadable notes during init
            continue
        metadata = post.metadata
        if not isinstance(metadata, dict):
            continue
        for key, value in metadata.items():
            if not isinstance(key, str) or not key:
                continue
            values_by_key[key].append(_normalize_value(value))

    if not values_by_key:
        raise ValueError(
            f"no frontmatter keys found under {root}"
            + (" (recursive)" if recursive else "")
        )

    # Most frequent keys first — nicer first draft.
    ordered = sorted(
        values_by_key.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )

    schema: dict[str, Any] = {}
    for name, values in ordered:
        schema[name] = _infer_field_spec(values)

    return {"schema": schema}


def write_schema_file(
    envelope: dict[str, Any],
    out: Path,
    *,
    force: bool,
) -> None:
    if out.exists() and not force:
        raise FileExistsError(
            f"refusing to overwrite {out} (pass --force to replace)"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        envelope,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )
    # Prefer block lists for enums; safe_dump is fine.
    out.write_text(text, encoding="utf-8")


def _infer_field_spec(values: list[Any]) -> dict[str, Any]:
    nullable = any(value is None for value in values)
    non_null_values = [value for value in values if value is not None]
    if not non_null_values:
        return {"nullable": True}

    kinds = [_classify(v) for v in non_null_values]
    kind_counts = Counter(kinds)
    dominant, _ = kind_counts.most_common(1)[0]

    spec: dict[str, Any] = {}

    if dominant == "boolean" and set(kinds) <= {"boolean"}:
        spec["type"] = "boolean"
        return _with_nullable(spec, nullable)
    if dominant == "integer" and set(kinds) <= {"integer"}:
        spec["type"] = "integer"
        return _with_nullable(spec, nullable)
    if dominant in {"integer", "number"} and set(kinds) <= {"integer", "number"}:
        spec["type"] = "number"
        return _with_nullable(spec, nullable)
    if dominant == "array" and set(kinds) <= {"array"}:
        spec["type"] = "array"
        return _with_nullable(spec, nullable)
    if dominant == "object" and set(kinds) <= {"object"}:
        spec["type"] = "object"
        return _with_nullable(spec, nullable)

    # Dates are formatted only when every non-null value has the same shape.
    if dominant == "date" and set(kinds) <= {"date"}:
        return _with_nullable({"format": "date"}, nullable)
    if dominant == "date-time" and set(kinds) <= {"date-time"}:
        return _with_nullable({"format": "date-time"}, nullable)

    # Default string — omit type (dialect default)
    string_values = [
        string
        for value in non_null_values
        if (string := _as_string(value)) is not None
    ]
    distinct = sorted(set(string_values))
    # Enum only when values repeat (avoids turning unique titles into enums).
    if (
        len(string_values) >= _ENUM_MIN_OCCURRENCES
        and 1 < len(distinct) <= _ENUM_MAX_DISTINCT
        and len(distinct) < len(string_values)
        and all(len(s) <= _ENUM_MAX_VALUE_LEN for s in distinct)
        and set(kinds) == {"string"}
    ):
        return _with_nullable({"enum": distinct}, nullable)

    json_types = sorted({_json_type(kind) for kind in kinds})
    if json_types == ["string"]:
        return _with_nullable({}, nullable)
    if set(json_types) == {"integer", "number"}:
        return _with_nullable({"type": "number"}, nullable)
    return _with_nullable({"type": json_types}, nullable)


def _classify(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, datetime):
        return "date-time"
    if isinstance(value, date):
        return "date"
    if isinstance(value, str):
        if _DATE_RE.match(value):
            return "date"
        if _DATE_TIME_RE.match(value):
            return "date-time"
        return "string"
    return "string"


def _json_type(kind: str) -> str:
    if kind in {"date", "date-time"}:
        return "string"
    return kind


def _with_nullable(spec: dict[str, Any], nullable: bool) -> dict[str, Any]:
    if nullable:
        spec["nullable"] = True
    return spec


def _as_string(value: Any) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (dict, list)):
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _normalize_value(value: Any) -> Any:
    """Unwrap wiki-links (and nested list items) before inference."""
    if isinstance(value, list):
        return [_normalize_value(v) for v in value]
    if isinstance(value, str):
        return unwrap_wikilink(value)
    return value
