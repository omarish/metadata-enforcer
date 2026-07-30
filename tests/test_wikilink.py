from metadata_enforcer.init import generate_schema
from metadata_enforcer.wikilink import unwrap_wikilink
from metadata_enforcer.validate import _normalize_for_json


def test_unwrap_wikilink_title():
    assert unwrap_wikilink("[[Home]]") == "Home"
    assert unwrap_wikilink("[[places/Home]]") == "Home"
    assert unwrap_wikilink("[[Home|at home]]") == "Home"
    assert unwrap_wikilink("[[places/Home#section|x]]") == "Home"
    assert unwrap_wikilink("plain") == "plain"
    assert unwrap_wikilink("  [[Seat 1A]]  ") == "Seat 1A"


def test_init_collapses_wikilink_and_bare_title(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    (root / "a.md").write_text(
        "---\nplace: '[[Home]]'\n---\n",
        encoding="utf-8",
    )
    (root / "b.md").write_text(
        "---\nplace: Home\n---\n",
        encoding="utf-8",
    )
    (root / "c.md").write_text(
        "---\nplace: '[[Home]]'\n---\n",
        encoding="utf-8",
    )

    schema = generate_schema(root, recursive=False)["schema"]
    # One repeated value after unwrap — not enough distinct for enum; stays {}
    # Add a second place that repeats so enum can form with titles only.
    (root / "d.md").write_text(
        "---\nplace: '[[Office]]'\n---\n",
        encoding="utf-8",
    )
    (root / "e.md").write_text(
        "---\nplace: Office\n---\n",
        encoding="utf-8",
    )

    schema = generate_schema(root, recursive=False)["schema"]
    assert schema["place"]["enum"] == ["Home", "Office"]


def test_validate_normalizes_wikilinks():
    assert _normalize_for_json({"place": "[[Home]]"}) == {"place": "Home"}
    assert _normalize_for_json({"tags": ["[[a]]", "b"]}) == {"tags": ["a", "b"]}
