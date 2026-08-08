# metadata-enforcer

Enforce YAML frontmatter on Obsidian (or any Markdown) notes using **Django-style Python models**.

No intermediate YAML DSL. No JSON Schema. You declare fields on a `Model`, map directories to those models, and run `check` / `fix` / `watch`.

## Why

Vaults drift. Dates get written three ways. Required fields go missing. Extra keys pile up.

This tool lets you describe the shape of each note collection in plain Python — the same ergonomics as Django models — and enforce it from the CLI or as a library.

## Quick start

### Install

Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```text
make install
# or: uv tool install --force .
metadata-enforcer --help
```

From a checkout without installing:

```text
uv sync --extra dev
uv run metadata-enforcer check examples/sample-vault
```

### Define a schema

Put a `schema.py` in your vault root (or pass `--schema`):

```python
from pathlib import Path
from metadata_enforcer import models

class Essay(models.Model):
    title = models.TextField()
    latex = models.BooleanField(default=False)
    tags = models.TagsField(default=list, optional=True)

    class Meta:
        extra = models.ExtraFields.FORBID
        field_order = ("title", "tags", "latex")

ROUTES = {
    Path("essays"): Essay,
}
```

`ROUTES` maps directory prefixes (relative to the vault root) to models. Longest prefix wins, so `Path("essays/wont-publish")` can override `Path("essays")`.

`MODEL_BY_PATH` is accepted as an alias for `ROUTES`.

### Run

```text
metadata-enforcer check ~/vault
metadata-enforcer fix ~/vault          # write missing defaults + reorder fields
metadata-enforcer watch ~/vault --fix
metadata-enforcer check --schema ./my_schema.py ~/vault
```

| Command | Behavior |
| --- | --- |
| `check` | Validate only; never writes |
| `fix` | Add field defaults, apply `field_order`, validate, write if needed |
| `watch` | Re-run after `.md` changes (`--fix` optional) |

Exit codes: `0` all good · `1` validation errors · non-zero for usage/load failures.

### Example output

Fields with `default=` validate successfully even when missing from the file
(`check` applies defaults in memory). Use `fix` to write those defaults into
frontmatter and apply `field_order`.

```text
$ metadata-enforcer check examples/sample-vault
Checked 3 file(s), skipped 1 unmapped
```

```text
$ metadata-enforcer fix examples/sample-vault --verbose
UPDATED essays/needs-defaults.md
Checked 3 file(s), updated 1, skipped 1 unmapped
```

True failures (wrong types, missing required fields without defaults, forbidden
extras) print as `ERROR path: …` and exit `1`.

## Models API

```python
from metadata_enforcer import models

class Note(models.Model):
    title = models.TextField()
    published = models.DateField(optional=True)
    sync_id = models.UUIDField(description="Stable id")
    tags = models.TagsField(default=list)
    draft = models.BooleanField(default=True)
    url = models.URLField(optional=True)
    path = models.URLPathField(optional=True)

    class Meta:
        # abstract = True          # cannot be routed or instantiated
        extra = models.ExtraFields.FORBID  # allow | ignore | forbid
        field_order = ("title", "published", "tags")
        # constraints = ()         # reserved; not enforced in 2.0
```

### Field options

| Option | Meaning |
| --- | --- |
| `default=` | Value (or zero-arg callable) used by `fix` / validation when missing |
| `optional=True` | May be absent or null/blank |
| `choices=` | Allowed values after type coercion |
| `description=` | Documentation only |
| `unique=` | Reserved; **not enforced in 2.0** |

### Built-in fields

`TextField` · `BooleanField` · `DateField` · `TagsField` · `UUIDField` · `URLField` · `URLPathField`

### Extra fields policy (`Meta.extra`)

| Value | Behavior |
| --- | --- |
| `allow` (default) | Unknown keys pass through |
| `ignore` | Unknown keys dropped from the cleaned result |
| `forbid` | Unknown keys are validation errors |

### Library usage

```python
from pathlib import Path
from metadata_enforcer import load_schema_module, scan

routes = load_schema_module(Path("schema.py"))
result = scan(Path("~/vault").expanduser(), routes, fix=False)
assert result.is_valid
```

## Fix mode caveats

`fix` rewrites the YAML frontmatter block via `yaml.safe_dump`. Comments inside frontmatter and some YAML formatting will not round-trip. Note bodies are preserved.

## Sample vault

See `examples/sample-vault/` for a tiny vault with `schema.py`, essays, and projects.  
See `examples/vault_schema.py` for a richer inheritance example (abstract base, nested routes).

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md). Roadmap: [ROADMAP.md](ROADMAP.md).
