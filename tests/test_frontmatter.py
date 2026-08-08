from pathlib import Path

import pytest

from metadata_enforcer.frontmatter import (
    FrontmatterError,
    read_frontmatter,
    write_frontmatter,
)


def test_read_missing_frontmatter(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("just body\n", encoding="utf-8")
    metadata, body = read_frontmatter(path)
    assert metadata == {}
    assert body == "just body\n"


def test_read_valid_frontmatter(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("---\ntitle: Hello\n---\nBody here\n", encoding="utf-8")
    metadata, body = read_frontmatter(path)
    assert metadata == {"title": "Hello"}
    assert body == "Body here\n"


def test_read_unclosed_frontmatter(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("---\ntitle: Hello\n", encoding="utf-8")
    with pytest.raises(FrontmatterError, match="closing delimiter"):
        read_frontmatter(path)


def test_read_non_mapping(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("---\n- item\n---\n", encoding="utf-8")
    with pytest.raises(FrontmatterError, match="mapping"):
        read_frontmatter(path)


def test_round_trip_preserves_body(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("---\ntitle: A\n---\n\n# Heading\n\nBody\n", encoding="utf-8")
    metadata, body = read_frontmatter(path)
    metadata["title"] = "B"
    write_frontmatter(path, metadata, body)
    again, body_again = read_frontmatter(path)
    assert again == {"title": "B"}
    assert body_again == body
