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
uv run metadata-enforcer init PATH/TO/NOTES
uv run metadata-enforcer init --recursive --force PATH/TO/NOTES
uv run metadata-enforcer PATH/TO/NOTES
uv run metadata-enforcer --recursive PATH/TO/NOTES
uv run metadata-enforcer --watch PATH/TO/NOTES
uv run metadata-enforcer --schema ./columns.yaml PATH/TO/NOTES
```

Or activate the env and call the script directly:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
metadata-enforcer PATH/TO/NOTES
```

`PATH/TO/NOTES` should contain a `columns.yaml` (unless you pass `--schema`).

### Quick smoke check

```bash
mkdir -p /tmp/me-demo
cat > /tmp/me-demo/columns.yaml <<'EOF'
schema:
  title: {}
  visibility:
    enum: [public, private]
EOF
cat > /tmp/me-demo/note.md <<'EOF'
---
title: Hello
visibility: public
---
Body
EOF

uv run metadata-enforcer /tmp/me-demo
# expect: All good. / exit 0
```

## Tests

```bash
uv run pytest
```

Tests live in `tests/` and use the `src/` layout via `pythonpath` in `pyproject.toml`.

## Layout

```text
src/metadata_enforcer/
  cli.py         # argparse entrypoint (check + init)
  init.py        # infer columns.yaml from vault
  schema.py      # columns.yaml → JSON Schema compile
  discover.py    # find .md files
  validate.py    # frontmatter + jsonschema
  report.py      # stdout formatting
  watch.py       # --watch
tests/
pyproject.toml
```

## Notes

* Prefer `uv run …` so you don’t have to activate the venv.
* Editable install means edits under `src/` take effect immediately.
* After changing dependencies in `pyproject.toml`, run `uv sync --extra dev` again.
