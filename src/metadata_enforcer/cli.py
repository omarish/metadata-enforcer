"""CLI entrypoint for metadata-enforcer."""

from __future__ import annotations

from pathlib import Path

import click

from metadata_enforcer.enforcer import ScanResult, scan
from metadata_enforcer.schema_loader import SchemaLoadError, load_schema_module
from metadata_enforcer.watcher import WatchDependencyError, watch_markdown


ROOT_ARGUMENT = click.argument(
    "root",
    default=".",
    type=click.Path(path_type=Path, exists=True, file_okay=False, resolve_path=True),
)
SCHEMA_OPTION = click.option(
    "--schema",
    "schema_path",
    default=None,
    type=click.Path(path_type=Path, dir_okay=False),
    help="Python schema module (default: ROOT/schema.py).",
)
VERBOSE_OPTION = click.option(
    "--verbose",
    is_flag=True,
    help="Show files updated during the scan.",
)


def display_result(result: ScanResult, root: Path, *, verbose: bool = False) -> None:
    if verbose:
        for path in result.changed:
            click.echo(f"UPDATED {path.relative_to(root)}")

    for path, error in result.errors.items():
        click.echo(f"ERROR {path.relative_to(root)}: {error}", err=True)

    summary = f"Checked {result.checked} file(s)"
    if result.changed:
        summary += f", updated {len(result.changed)}"
    if result.skipped:
        summary += f", skipped {result.skipped} unmapped"
    if result.errors:
        summary += f", found {len(result.errors)} invalid"
    click.echo(summary)


def resolve_schema_path(root: Path, schema_path: Path | None) -> Path:
    if schema_path is not None:
        return schema_path.expanduser().resolve()
    return (root / "schema.py").resolve()


def run(
    root: Path,
    *,
    schema_path: Path | None = None,
    fix: bool = False,
    verbose: bool = False,
) -> ScanResult:
    path = resolve_schema_path(root, schema_path)
    try:
        routes = load_schema_module(path)
    except SchemaLoadError as error:
        raise click.ClickException(str(error)) from error

    try:
        result = scan(root, routes, fix=fix)
    except OSError as error:
        raise click.ClickException(str(error)) from error

    display_result(result, root, verbose=verbose)
    if result.checked == 0:
        raise click.ClickException("no Markdown files matched ROUTES")
    return result


@click.group()
@click.version_option(package_name="metadata-enforcer")
def cli() -> None:
    """Validate YAML frontmatter using Django-style Python models."""


@cli.command()
@ROOT_ARGUMENT
@SCHEMA_OPTION
@VERBOSE_OPTION
def check(root: Path, schema_path: Path | None, verbose: bool) -> None:
    """Check mapped Markdown files without changing them."""
    result = run(root, schema_path=schema_path, verbose=verbose)
    if not result.is_valid:
        raise SystemExit(1)


@cli.command()
@ROOT_ARGUMENT
@SCHEMA_OPTION
@VERBOSE_OPTION
def fix(root: Path, schema_path: Path | None, verbose: bool) -> None:
    """Add missing defaults and reorder fields, then validate."""
    result = run(root, schema_path=schema_path, fix=True, verbose=verbose)
    if not result.is_valid:
        raise SystemExit(1)


@cli.command()
@ROOT_ARGUMENT
@SCHEMA_OPTION
@click.option("--fix/--no-fix", default=False, help="Add defaults after file changes.")
@VERBOSE_OPTION
def watch(
    root: Path,
    schema_path: Path | None,
    fix: bool,
    verbose: bool,
) -> None:
    """Watch the vault and rerun validation after Markdown changes."""

    def rerun() -> None:
        click.echo()
        run(root, schema_path=schema_path, fix=fix, verbose=verbose)

    initial_result = run(root, schema_path=schema_path, fix=fix, verbose=verbose)
    if not initial_result.is_valid:
        click.echo("Watching despite validation errors.", err=True)

    click.echo(f"Watching {root}. Press Ctrl-C to stop.")
    try:
        watch_markdown(root, rerun)
    except WatchDependencyError as error:
        raise click.ClickException(str(error)) from error


def main() -> None:
    """Console-script entrypoint."""
    cli(prog_name="metadata-enforcer")


if __name__ == "__main__":
    main()
