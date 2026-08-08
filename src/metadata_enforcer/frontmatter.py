from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml


class FrontmatterError(ValueError):
    pass


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text

    closing_line = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() in {"---", "..."}
        ),
        None,
    )
    if closing_line is None:
        raise FrontmatterError("frontmatter has no closing delimiter")

    try:
        metadata = yaml.safe_load("".join(lines[1:closing_line]))
    except yaml.YAMLError as error:
        raise FrontmatterError(f"invalid YAML: {error}") from error

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, Mapping):
        raise FrontmatterError("frontmatter must contain a YAML mapping")

    return dict(metadata), "".join(lines[closing_line + 1 :])


def write_frontmatter(path: Path, metadata: Mapping[str, Any], body: str) -> None:
    dumped = yaml.safe_dump(
        dict(metadata),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).rstrip()
    path.write_text(f"---\n{dumped}\n---\n{body}", encoding="utf-8")
