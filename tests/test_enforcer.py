from pathlib import Path

from metadata_enforcer.enforcer import model_for_path, scan
from metadata_enforcer.models import BooleanField, Model, TextField


class Essay(Model):
    title = TextField()
    latex = BooleanField(default=False)

    class Meta:
        field_order = ("title", "latex")


class NestedEssay(Essay):
    pass


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_longest_prefix_routing(tmp_path: Path):
    routes = {
        Path("essays/wont-publish"): NestedEssay,
        Path("essays"): Essay,
    }
    nested = tmp_path / "essays" / "wont-publish" / "a.md"
    plain = tmp_path / "essays" / "b.md"
    _write(nested, "---\ntitle: A\n---\n")
    _write(plain, "---\ntitle: B\n---\n")

    assert model_for_path(nested, tmp_path, routes) is NestedEssay
    assert model_for_path(plain, tmp_path, routes) is Essay
    assert model_for_path(tmp_path / "other" / "c.md", tmp_path, routes) is None


def test_scan_skips_unmapped_and_reports_errors(tmp_path: Path):
    routes = {Path("essays"): Essay}
    _write(tmp_path / "essays" / "ok.md", "---\ntitle: Ok\n---\n")
    _write(tmp_path / "essays" / "bad.md", "---\nlatex: true\n---\n")
    _write(tmp_path / "notes" / "skip.md", "---\ntitle: Skip\n---\n")

    result = scan(tmp_path, routes)
    assert result.checked == 2
    assert result.skipped == 1
    assert not result.is_valid
    assert any("title" in msg for msg in result.errors.values())


def test_fix_writes_defaults_and_order(tmp_path: Path):
    routes = {Path("essays"): Essay}
    path = tmp_path / "essays" / "note.md"
    _write(path, "---\nlatex: true\ntitle: Hello\n---\nBody\n")

    result = scan(tmp_path, routes, fix=True)
    assert result.is_valid
    assert path in result.changed
    text = path.read_text(encoding="utf-8")
    # field_order puts title before latex
    assert text.index("title:") < text.index("latex:")
    assert "Body" in text


def test_fix_adds_missing_default(tmp_path: Path):
    routes = {Path("essays"): Essay}
    path = tmp_path / "essays" / "note.md"
    _write(path, "---\ntitle: Hello\n---\n")

    result = scan(tmp_path, routes, fix=True)
    assert result.is_valid
    assert "latex: false" in path.read_text(encoding="utf-8")


def test_check_does_not_write(tmp_path: Path):
    routes = {Path("essays"): Essay}
    path = tmp_path / "essays" / "note.md"
    original = "---\ntitle: Hello\n---\n"
    _write(path, original)

    result = scan(tmp_path, routes, fix=False)
    assert result.is_valid
    assert result.changed == []
    assert path.read_text(encoding="utf-8") == original
