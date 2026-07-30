from pathlib import Path

import pytest

from metadata_enforcer.cli import main


def _write_fixture(root: Path) -> None:
    (root / "columns.yaml").write_text(
        """
schema:
  title: {}
  visibility:
    enum: [public, private]
  published:
    format: date
    required: true
""".lstrip(),
        encoding="utf-8",
    )
    (root / "ok.md").write_text(
        """---
title: Hello
visibility: public
published: 2026-07-27
---
Body
""",
        encoding="utf-8",
    )
    (root / "bad.md").write_text(
        """---
title: WIP
visibility: draft
published: 2027-07-27 12:12:12.0000Z
extra: true
---
Body
""",
        encoding="utf-8",
    )
    nested = root / "nested"
    nested.mkdir()
    (nested / "deep.md").write_text(
        """---
title: Deep
visibility: public
published: 2026-01-01
---
""",
        encoding="utf-8",
    )


def test_success_and_failure(tmp_path, capsys):
    root = tmp_path / "essays"
    root.mkdir()
    _write_fixture(root)

    # Only ok.md if we remove bad — use a clean dir for success
    good = tmp_path / "good"
    good.mkdir()
    (good / "columns.yaml").write_text(
        (root / "columns.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (good / "ok.md").write_text(
        (root / "ok.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    assert main([str(good)]) == 0
    out = capsys.readouterr().out
    assert "All good." in out

    assert main([str(root)]) == 1
    out = capsys.readouterr().out
    assert "bad.md" in out
    assert "/visibility" in out
    assert "/published" in out
    assert "extra" in out


def test_non_recursive_skips_nested(tmp_path):
    root = tmp_path / "essays"
    root.mkdir()
    _write_fixture(root)
    # Remove bad so only ok + nested/deep; non-recursive should only see ok
    (root / "bad.md").unlink()
    assert main([str(root)]) == 0
    assert main(["--recursive", str(root)]) == 0


def test_missing_schema_exit_2(tmp_path, capsys):
    root = tmp_path / "empty"
    root.mkdir()
    (root / "note.md").write_text("---\ntitle: x\n---\n", encoding="utf-8")
    assert main([str(root)]) == 2
    err = capsys.readouterr().err
    assert "schema not found" in err


@pytest.mark.parametrize(
    ("broken_line", "expected_column", "expected_hex", "expected_context"),
    [
        (
            b"title: Now, it\xd5s Monday morning",
            15,
            "d5",
            r"Now, it\xd5s Monday morning",
        ),
        (
            b"title: connection\xd0a connection with oneself",
            18,
            "d0",
            r"connection\xd0a connection with oneself",
        ),
        # Column numbers count Unicode characters, not UTF-8 bytes.
        (
            "title: café ".encode() + b"\xd5",
            13,
            "d5",
            r"café \xd5",
        ),
    ],
)
def test_invalid_utf8_reports_location_byte_and_context(
    tmp_path,
    capsys,
    broken_line,
    expected_column,
    expected_hex,
    expected_context,
):
    root = tmp_path / "vault"
    root.mkdir()
    (root / "columns.yaml").write_text("schema:\n  title: {}\n", encoding="utf-8")
    (root / "broken.md").write_bytes(b"---\n" + broken_line + b"\n---\nBody\n")

    assert main([str(root)]) == 1
    output = capsys.readouterr().out
    assert f"invalid UTF-8 at line 2, column {expected_column}" in output
    assert f"hex {expected_hex}" in output
    assert expected_context in output
