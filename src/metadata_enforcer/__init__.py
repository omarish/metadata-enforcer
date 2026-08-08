"""metadata-enforcer: validate Obsidian frontmatter with Django-style models."""

from metadata_enforcer import models
from metadata_enforcer.enforcer import ScanResult, model_for_path, scan
from metadata_enforcer.frontmatter import FrontmatterError, read_frontmatter, write_frontmatter
from metadata_enforcer.models import ValidationError
from metadata_enforcer.schema_loader import SchemaLoadError, load_schema_module

__version__ = "2.0.0"

__all__ = [
    "FrontmatterError",
    "ScanResult",
    "SchemaLoadError",
    "ValidationError",
    "__version__",
    "load_schema_module",
    "model_for_path",
    "models",
    "read_frontmatter",
    "scan",
    "write_frontmatter",
]
