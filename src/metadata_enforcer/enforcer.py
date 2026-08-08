from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from metadata_enforcer import models
from metadata_enforcer.frontmatter import (
    FrontmatterError,
    read_frontmatter,
    write_frontmatter,
)

ModelMap = Mapping[Path, type[models.Model]]


@dataclass
class ScanResult:
    checked: int = 0
    skipped: int = 0
    changed: list[Path] = field(default_factory=list)
    errors: dict[Path, str] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def model_for_path(
    path: Path,
    root: Path,
    models_by_directory: ModelMap,
) -> type[models.Model] | None:
    """Return the model for a note path using longest-prefix directory routes.

    Routes are matched against the path relative to ``root``. If any route starts
    with ``root.name`` (e.g. ``Path("vault/essays")`` when root is ``.../vault``),
    matching also considers ``root.name / relative_path`` so vault-prefixed maps
    keep working.
    """
    relative_path = path.relative_to(root)
    routed_path = (
        Path(root.name, relative_path)
        if any(
            route.parts and route.parts[0] == root.name for route in models_by_directory
        )
        else relative_path
    )
    matching_routes = [
        route
        for route in models_by_directory
        if routed_path == route or route in routed_path.parents
    ]
    if not matching_routes:
        return None
    route = max(matching_routes, key=lambda candidate: len(candidate.parts))
    return models_by_directory[route]


def scan(
    root: Path,
    models_by_directory: ModelMap,
    *,
    fix: bool = False,
) -> ScanResult:
    result = ScanResult()

    for path in sorted(root.rglob("*.md")):
        model = model_for_path(path, root, models_by_directory)
        if model is None:
            result.skipped += 1
            continue

        result.checked += 1
        try:
            metadata, body = read_frontmatter(path)
            candidate = metadata
            if fix:
                candidate = model.apply_defaults(candidate)
                candidate = model.order_metadata(candidate)
            model.validate(candidate)
            values_changed = candidate != metadata
            order_changed = tuple(candidate) != tuple(metadata)
            if fix and (values_changed or order_changed):
                write_frontmatter(path, candidate, body)
                result.changed.append(path)
        except (FrontmatterError, models.ValidationError, OSError) as error:
            result.errors[path] = str(error)

    return result
