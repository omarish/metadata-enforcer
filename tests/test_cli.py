from pathlib import Path

from click.testing import CliRunner

from metadata_enforcer.cli import cli


SCHEMA = """
from pathlib import Path
from metadata_enforcer.models import BooleanField, Model, TextField

class Essay(Model):
    title = TextField()
    latex = BooleanField(default=False)

    class Meta:
        field_order = ("title", "latex")

ROUTES = {Path("essays"): Essay}
"""


def _vault(tmp_path: Path, note: str) -> Path:
    (tmp_path / "schema.py").write_text(SCHEMA, encoding="utf-8")
    path = tmp_path / "essays" / "note.md"
    path.parent.mkdir(parents=True)
    path.write_text(note, encoding="utf-8")
    return tmp_path


def test_check_success(tmp_path: Path):
    root = _vault(tmp_path, "---\ntitle: Hello\nlatex: false\n---\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["check", str(root)])
    assert result.exit_code == 0
    assert "Checked 1 file(s)" in result.output


def test_check_failure(tmp_path: Path):
    root = _vault(tmp_path, "---\nlatex: true\n---\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["check", str(root)])
    assert result.exit_code == 1
    assert "ERROR" in result.output


def test_fix_mutates_file(tmp_path: Path):
    root = _vault(tmp_path, "---\ntitle: Hello\n---\n")
    note = root / "essays" / "note.md"
    runner = CliRunner()
    result = runner.invoke(cli, ["fix", str(root), "--verbose"])
    assert result.exit_code == 0
    assert "UPDATED" in result.output
    assert "latex: false" in note.read_text(encoding="utf-8")


def test_default_schema_path(tmp_path: Path):
    root = _vault(tmp_path, "---\ntitle: Hello\nlatex: false\n---\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["check", str(root)])
    assert result.exit_code == 0


def test_explicit_schema_path(tmp_path: Path):
    schema = tmp_path / "custom_schema.py"
    schema.write_text(SCHEMA, encoding="utf-8")
    notes = tmp_path / "vault"
    path = notes / "essays" / "note.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\ntitle: Hello\nlatex: false\n---\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["check", str(notes), "--schema", str(schema)],
    )
    assert result.exit_code == 0


def test_missing_schema(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(cli, ["check", str(tmp_path)])
    assert result.exit_code != 0
    assert "schema module not found" in result.output
