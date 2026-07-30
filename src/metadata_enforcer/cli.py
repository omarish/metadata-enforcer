"""CLI entrypoint for metadata-enforcer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from metadata_enforcer.init import generate_schema, write_schema_file
from metadata_enforcer.report import format_report
from metadata_enforcer.schema import SchemaError, load_and_compile
from metadata_enforcer.validate import check_notes
from metadata_enforcer.watch import watch_and_report


def build_check_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="metadata-enforcer",
        description="Enforce Obsidian frontmatter metadata via columns.yaml",
    )
    parser.add_argument(
        "root",
        type=Path,
        help="Directory of Markdown notes to check",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Schema file (default: ROOT/columns.yaml)",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Scan ROOT recursively for .md files",
    )
    parser.add_argument(
        "--watch",
        "-w",
        action="store_true",
        help="Re-run on changes and refresh the report",
    )
    return parser


def build_init_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="metadata-enforcer init",
        description="Infer a starting columns.yaml from existing note frontmatter",
    )
    parser.add_argument(
        "root",
        type=Path,
        help="Directory of Markdown notes to scan",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Scan ROOT recursively for .md files",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path (default: ROOT/columns.yaml)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite an existing schema file",
    )
    return parser


def run_check(root: Path, schema_path: Path, *, recursive: bool) -> int:
    try:
        compiled = load_and_compile(schema_path)
    except SchemaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        result = check_notes(root, schema_path, compiled, recursive=recursive)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    sys.stdout.write(format_report(result))
    return 0 if result.ok else 1


def run_init(
    root: Path,
    *,
    recursive: bool,
    out: Path,
    force: bool,
) -> int:
    try:
        envelope = generate_schema(root, recursive=recursive)
        write_schema_file(envelope, out, force=force)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    field_count = len(envelope.get("schema") or {})
    print(f"Wrote {out} ({field_count} field(s)). Review, then tighten as needed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv and argv[0] == "init":
        return _main_init(argv[1:])
    return _main_check(argv)


def _main_check(argv: list[str]) -> int:
    parser = build_check_parser()
    args = parser.parse_args(argv)

    root: Path = args.root
    err = _require_dir(root)
    if err is not None:
        return err

    schema_path: Path = args.schema if args.schema is not None else root / "columns.yaml"

    if args.watch:

        def _once() -> int:
            return run_check(root, schema_path, recursive=args.recursive)

        return watch_and_report(root, _once, recursive=args.recursive)

    return run_check(root, schema_path, recursive=args.recursive)


def _main_init(argv: list[str]) -> int:
    parser = build_init_parser()
    args = parser.parse_args(argv)

    root: Path = args.root
    err = _require_dir(root)
    if err is not None:
        return err

    out: Path = args.out if args.out is not None else root / "columns.yaml"
    return run_init(root, recursive=args.recursive, out=out, force=args.force)


def _require_dir(root: Path) -> int | None:
    if not root.exists():
        print(f"error: root does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2
    return None


if __name__ == "__main__":
    raise SystemExit(main())
