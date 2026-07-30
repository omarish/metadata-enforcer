"""Validate note frontmatter against a compiled JSON Schema."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import frontmatter
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError as JsonSchemaError

from metadata_enforcer.discover import iter_markdown_files
from metadata_enforcer.wikilink import unwrap_wikilink

_UNEXPECTED_PROP = re.compile(r"\('([^']+)' was unexpected\)")


@dataclass
class Issue:
    path: str
    instance_path: str
    message: str
    validator: str


@dataclass
class CheckResult:
    root: str
    schema: str
    files_checked: int
    ok: bool
    errors: list[Issue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_validator(compiled_schema: dict[str, Any]) -> Draft202012Validator:
    try:
        Draft202012Validator.check_schema(compiled_schema)
    except JsonSchemaError as exc:
        raise ValueError(f"compiled schema is invalid: {exc}") from exc
    # Assert formats (date, date-time, …) — annotation-only is useless for enforcement.
    return Draft202012Validator(
        compiled_schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


def check_notes(
    root: Path,
    schema_path: Path,
    compiled_schema: dict[str, Any],
    *,
    recursive: bool,
) -> CheckResult:
    validator = make_validator(compiled_schema)
    files = iter_markdown_files(root, recursive=recursive)
    errors: list[Issue] = []

    for path in files:
        errors.extend(_validate_file(path, validator))

    return CheckResult(
        root=str(root),
        schema=str(schema_path),
        files_checked=len(files),
        ok=not errors,
        errors=errors,
    )


def _validate_file(path: Path, validator: Draft202012Validator) -> list[Issue]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        post = frontmatter.loads(text)
    except UnicodeDecodeError as exc:
        return [
            Issue(
                path=str(path),
                instance_path="",
                message=_format_decode_error(raw, exc),
                validator="encoding",
            )
        ]
    except Exception as exc:  # noqa: BLE001 — surface parse failures as issues
        return [
            Issue(
                path=str(path),
                instance_path="",
                message=f"failed to parse frontmatter: {exc}",
                validator="parse",
            )
        ]

    metadata = post.metadata
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        return [
            Issue(
                path=str(path),
                instance_path="",
                message="frontmatter must be a mapping",
                validator="parse",
            )
        ]

    metadata = _normalize_for_json(metadata)

    issues: list[Issue] = []
    for err in sorted(validator.iter_errors(metadata), key=_error_sort_key):
        issues.append(
            Issue(
                path=str(path),
                instance_path=_instance_path(err),
                message=err.message,
                validator=err.validator or "unknown",
            )
        )
    return issues


def _format_decode_error(raw: bytes, error: UnicodeDecodeError) -> str:
    """Render an invalid UTF-8 byte with a useful source location and context."""
    line_start = raw.rfind(b"\n", 0, error.start) + 1
    line_end = raw.find(b"\n", error.end)
    if line_end == -1:
        line_end = len(raw)

    line = raw[line_start:line_end]
    line_number = raw.count(b"\n", 0, error.start) + 1
    column = len(raw[line_start:error.start].decode("utf-8", errors="replace")) + 1

    # Keep the context readable for very long lines while preserving the bad byte.
    relative_start = error.start - line_start
    context_start = max(0, relative_start - 40)
    context_end = min(len(line), relative_start + max(1, error.end - error.start) + 40)
    context = line[context_start:context_end].decode(
        "utf-8",
        errors="backslashreplace",
    )
    if context_start:
        context = "…" + context
    if context_end < len(line):
        context += "…"

    offending = raw[error.start:error.end].hex(" ")
    return (
        f"invalid UTF-8 at line {line_number}, column {column} "
        f"(byte {error.start}, hex {offending}): {error.reason}; "
        f'near "{context}"'
    )


def _instance_path(err: Any) -> str:
    parts = [str(p) for p in err.absolute_path]
    if not parts and err.validator == "additionalProperties":
        match = _UNEXPECTED_PROP.search(err.message or "")
        if match:
            parts = [match.group(1)]
    if not parts:
        return ""
    return "/" + "/".join(parts)


def _error_sort_key(err: Any) -> list[str]:
    path = _instance_path(err)
    return path.split("/") if path else [""]


def _normalize_for_json(value: Any) -> Any:
    """Normalize frontmatter for JSON Schema: dates → strings, [[wikilinks]] → titles."""
    if isinstance(value, dict):
        return {k: _normalize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_for_json(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return unwrap_wikilink(value)
    return value
