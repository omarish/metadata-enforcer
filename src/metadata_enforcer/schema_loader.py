from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from metadata_enforcer import models
from metadata_enforcer.enforcer import ModelMap


class SchemaLoadError(Exception):
    """Raised when a user schema module cannot be loaded or is invalid."""


def load_schema_module(path: Path) -> ModelMap:
    """Load a schema.py-style module and return its route map.

    The module must define ``ROUTES`` or ``MODEL_BY_PATH``: a mapping of
    directory paths (relative to the vault root) to concrete ``Model`` subclasses.
    """
    path = path.resolve()
    if not path.is_file():
        raise SchemaLoadError(f"schema module not found: {path}")

    module = _import_module_from_path(path)
    routes = _extract_routes(module, path)
    return _normalize_routes(routes, path)


def _import_module_from_path(path: Path) -> ModuleType:
    module_name = f"_metadata_enforcer_schema_{path.stem}_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SchemaLoadError(f"unable to load schema module: {path}")

    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses / relative patterns work if needed.
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:  # noqa: BLE001 — surface user schema errors cleanly
        sys.modules.pop(module_name, None)
        raise SchemaLoadError(f"failed to import schema module {path}: {error}") from error
    return module


def _extract_routes(module: ModuleType, path: Path) -> Any:
    if hasattr(module, "ROUTES"):
        return module.ROUTES
    if hasattr(module, "MODEL_BY_PATH"):
        return module.MODEL_BY_PATH
    raise SchemaLoadError(
        f"schema module {path} must define ROUTES or MODEL_BY_PATH"
    )


def _normalize_routes(routes: Any, path: Path) -> dict[Path, type[models.Model]]:
    if not isinstance(routes, dict):
        raise SchemaLoadError(
            f"ROUTES in {path} must be a dict of Path -> Model, got {type(routes).__name__}"
        )
    if not routes:
        raise SchemaLoadError(f"ROUTES in {path} is empty")

    normalized: dict[Path, type[models.Model]] = {}
    for key, value in routes.items():
        route = Path(key) if not isinstance(key, Path) else key
        if not isinstance(value, type) or not issubclass(value, models.Model):
            raise SchemaLoadError(
                f"ROUTES[{route!s}] in {path} must be a Model subclass, "
                f"got {type(value).__name__}"
            )
        if getattr(value, "_abstract", False):
            raise SchemaLoadError(
                f"ROUTES[{route!s}] in {path} maps to abstract model {value.__name__}"
            )
        normalized[route] = value
    return normalized
