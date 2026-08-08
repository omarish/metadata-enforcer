# Development

Local setup for working on this repo. Requires **[uv](https://docs.astral.sh/uv/)** and **Python 3.10+**.

## Setup

From the repo root:

```bash
uv sync --extra dev
```

That creates `.venv`, installs the package in editable mode (code under `src/`), and pulls in pytest.

## Run the CLI

```bash
uv run metadata-enforcer check examples/sample-vault
uv run metadata-enforcer fix examples/sample-vault --verbose
uv run metadata-enforcer check --schema examples/vault_schema.py /path/to/vault
uv run metadata-enforcer watch examples/sample-vault
```

Or activate the env and call the script directly:

```bash
source .venv/bin/activate
metadata-enforcer check examples/sample-vault
```

## Tests

```bash
uv run pytest
# or
make test
```

## Layout

```text
src/metadata_enforcer/
  models/          # Django-style Model + fields
  frontmatter.py   # YAML frontmatter read/write
  enforcer.py      # path routing + scan/check/fix
  schema_loader.py # load user schema.py + ROUTES
  watcher.py       # debounced markdown watch
  cli.py           # click: check | fix | watch
examples/
  sample-vault/    # tiny vault + schema.py
  vault_schema.py  # richer inheritance example
tests/
pyproject.toml
```

## Notes

* Prefer `uv run …` so you don’t have to activate the venv.
* Editable install means edits under `src/` take effect immediately.
* After changing dependencies in `pyproject.toml`, run `uv sync --extra dev` again.
