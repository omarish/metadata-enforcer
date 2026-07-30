from pathlib import Path

from metadata_enforcer.cli import main
from metadata_enforcer.init import generate_schema
from metadata_enforcer.schema import compile_schema
from metadata_enforcer.validate import check_notes


def _note(path: Path, frontmatter: str) -> None:
    path.write_text(f"---\n{frontmatter}---\nBody\n", encoding="utf-8")


def test_generate_infers_enum_date_and_optional_string(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    _note(
        root / "a.md",
        "title: Alpha\nvisibility: public\npublished: 2026-07-27\n",
    )
    _note(
        root / "b.md",
        "title: Beta\nvisibility: private\npublished: 2026-01-01\n",
    )
    _note(
        root / "c.md",
        "title: Gamma\nvisibility: public\n",
    )

    envelope = generate_schema(root, recursive=False)
    schema = envelope["schema"]

    assert schema["title"] == {}
    assert schema["visibility"]["enum"] == ["private", "public"]
    assert schema["published"] == {"format": "date"}
    assert "required" not in schema["visibility"]
    assert "type" not in schema["title"]


def test_init_cli_writes_columns_yaml(tmp_path: Path, capsys):
    root = tmp_path / "vault"
    root.mkdir()
    _note(root / "a.md", "status: draft\n")
    _note(root / "b.md", "status: published\n")

    assert main(["init", str(root)]) == 0
    out = root / "columns.yaml"
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "schema:" in text
    assert "status:" in text
    assert "Wrote" in capsys.readouterr().out

    assert main(["init", str(root)]) == 2  # refuse overwrite
    assert main(["init", "--force", str(root)]) == 0


def test_generated_schema_accepts_nulls_and_all_observed_types(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    _note(
        root / "a.md",
        "where-am-i:\nscore: 1\npublished: 2026-07-27\nmixed: text\n",
    )
    _note(
        root / "b.md",
        "where-am-i: Home\nscore: 1.5\npublished:\nmixed: 42\n",
    )

    envelope = generate_schema(root, recursive=False)
    schema = envelope["schema"]

    assert schema["where-am-i"] == {"nullable": True}
    assert schema["score"] == {"type": "number"}
    assert schema["published"] == {"format": "date", "nullable": True}
    assert schema["mixed"] == {"type": ["integer", "string"]}

    compiled = compile_schema(schema)
    result = check_notes(
        root,
        root / "columns.yaml",
        compiled,
        recursive=False,
    )
    assert result.ok, result.errors
