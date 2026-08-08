from pathlib import Path

import pytest

from metadata_enforcer.models import Model, TextField
from metadata_enforcer.schema_loader import SchemaLoadError, load_schema_module


SCHEMA_OK = """
from pathlib import Path
from metadata_enforcer.models import Model, TextField

class Note(Model):
    title = TextField()

ROUTES = {
    Path("notes"): Note,
}
"""

SCHEMA_MODEL_BY_PATH = """
from pathlib import Path
from metadata_enforcer.models import Model, TextField

class Note(Model):
    title = TextField()

MODEL_BY_PATH = {
    Path("notes"): Note,
}
"""

SCHEMA_ABSTRACT = """
from pathlib import Path
from metadata_enforcer.models import Model, TextField

class Note(Model):
    title = TextField()
    class Meta:
        abstract = True

ROUTES = {Path("notes"): Note}
"""


def test_load_routes(tmp_path: Path):
    path = tmp_path / "schema.py"
    path.write_text(SCHEMA_OK, encoding="utf-8")
    routes = load_schema_module(path)
    assert Path("notes") in routes
    assert issubclass(routes[Path("notes")], Model)


def test_accepts_model_by_path_alias(tmp_path: Path):
    path = tmp_path / "schema.py"
    path.write_text(SCHEMA_MODEL_BY_PATH, encoding="utf-8")
    routes = load_schema_module(path)
    assert Path("notes") in routes


def test_missing_file(tmp_path: Path):
    with pytest.raises(SchemaLoadError, match="not found"):
        load_schema_module(tmp_path / "missing.py")


def test_missing_routes(tmp_path: Path):
    path = tmp_path / "schema.py"
    path.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(SchemaLoadError, match="ROUTES or MODEL_BY_PATH"):
        load_schema_module(path)


def test_rejects_abstract_model(tmp_path: Path):
    path = tmp_path / "schema.py"
    path.write_text(SCHEMA_ABSTRACT, encoding="utf-8")
    with pytest.raises(SchemaLoadError, match="abstract"):
        load_schema_module(path)
