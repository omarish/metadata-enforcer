"""Find Markdown notes under a root."""

from __future__ import annotations

from pathlib import Path


def iter_markdown_files(root: Path, *, recursive: bool) -> list[Path]:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"root is not a directory: {root}")

    if recursive:
        candidates = sorted(root.rglob("*.md"))
    else:
        candidates = sorted(root.glob("*.md"))

    files: list[Path] = []
    for path in candidates:
        if _is_under_obsidian(path, root):
            continue
        files.append(path)
    return files


def _is_under_obsidian(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    return ".obsidian" in relative.parts
