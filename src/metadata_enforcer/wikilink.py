"""Obsidian wiki-link helpers."""

from __future__ import annotations

import re

# [[Note]], [[folder/Note]], [[Note#heading]], [[Note|alias]], [[folder/Note#x|alias]]
_WIKILINK_RE = re.compile(
    r"^\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]$"
)


def unwrap_wikilink(value: str) -> str:
    """If value is a wiki-link, return the note title; otherwise return value unchanged.

    Title = last path segment of the link target (not the optional display alias).
    """
    match = _WIKILINK_RE.fullmatch(value.strip())
    if not match:
        return value
    target = match.group(1).strip()
    if not target:
        return value
    return target.split("/")[-1].strip()
