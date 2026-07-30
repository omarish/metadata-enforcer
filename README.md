# metadata-enforcer

## what and why?

I rely on Obsidian a lot but I also love Postgres. Without categories we cannot have freedom; without the license to enforce strict metadata validation, we cannot truly be free.

Obsidian vaults are like minds: a little mess is fine, and improvement is gradual. This tool lets you define frontmatter rules in a human-friendly way, then enforces them for real (via JSON Schema under the hood).

## What already exists

There are already metadata enforcement packages out there, but I don't think they are as intense or as "extra" as I want.

Want regexp enforcement? Sure thing. There's nothing worse than some things being `2026-07-27` and others being `2027-07-27 12:12:12.0000z`. Or, what if we want to enforce referential integrity?

Sure, we can do that too — later. See [ROADMAP.md](ROADMAP.md).

### Principles

* Sensible defaults (optional fields, `type: string` implied).
* Remain human in the config file; get JSON Schema teeth at runtime.
* This must be reliable. Our personal notes are sacred (v1 is read-only).
* Gradual improvement over greenfield perfection.

## Data model

| Concept | Meaning |
| --- | --- |
| Root | Directory you pass to the CLI |
| Row | One Markdown note (`.md`) under the scan scope |
| Columns / values | YAML frontmatter on that note |
| Schema file | `columns.yaml` — a small envelope that compiles to JSON Schema |

## How it works

In a folder, put a `columns.yaml`. You write a thin field map; the tool compiles it to [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12) and validates each note's frontmatter.

### `columns.yaml`

Top-level `schema:` is a map of **field name → field spec**. Think about each field once — including whether it's required. No separate `required:` list.

```yaml
schema:
  title: {}
  # same as: title: { type: string, required: false }

  visibility:
    enum:
      - public
      - private
    # type: string implied

  published:
    format: date
    required: true   # opt into strictness per field
```

#### Field defaults

| Key | Default |
| --- | --- |
| `required` | `false` |
| `type` | `string` |

Empty / `{}` field specs are fine. Everything else on a field should be normal JSON Schema for that property (`enum`, `pattern`, `format`, `minLength`, `default`, …). No parallel synonyms like `choices`.

The tool always compiles with:

* JSON Schema Draft 2020-12
* root `type: object`
* `additionalProperties: false`

Unknown top-level keys in `columns.yaml` (besides `schema:`) are an error in v1 — room is reserved for future collection-level rules (`unique`, `references`, …) on the [roadmap](ROADMAP.md).

v1 is **read-only**: a field may declare JSON Schema `default`, but the tool never writes into your notes.

## How to run it

This is a separate CLI, not an Obsidian plugin.

```text
metadata-enforcer [OPTIONS] ROOT

Options:
  --schema PATH     Schema file (default: ROOT/columns.yaml)
  --recursive, -r   Scan ROOT recursively for .md files
  --watch, -w       Re-run on changes; refresh the report
```

* Without `--recursive`, only `ROOT/*.md` is checked.
* With `--recursive`, subdirectories are included; `.obsidian/` is always ignored.
* One schema file per run.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | All checked notes pass |
| `1` | One or more validation or parse errors |
| `2` | Usage / config failure (missing schema, invalid envelope) |

### Example run (success)

```text
$ metadata-enforcer notes/essays
Checked 2 file(s) against notes/essays/columns.yaml
All good.
$ echo $?
0
```

### Example run (errors)

```text
$ metadata-enforcer notes/essays
notes/essays/bad.md
  /visibility: 'draft' is not one of ['public', 'private']
  /published: '2027-07-27 12:12:12.0000Z' is not a 'date'
  /extra: Additional properties are not allowed ('extra' was unexpected)

Checked 2 file(s), 1 with errors (3 issue(s))
$ echo $?
1
```

### Watch mode

```text
$ metadata-enforcer --watch notes/essays
```

Re-checks when the folder is touched and refreshes the report (stdout). A TUI may come later; the underlying artifact is a structured result either way.

### Explicit schema path

```text
$ metadata-enforcer --schema ./schemas/essays.yaml --recursive ~/vault/essays
```

## Install / develop

Python 3.10+:

```text
pip install -e .
metadata-enforcer .
```

## v1 non-goals

Deliberately not in v1 (see [ROADMAP.md](ROADMAP.md)):

* Nested multi-schema discovery
* Uniqueness / referential integrity
* Writing defaults into notes
* Init / wizard from an existing vault
* Health score
* TUI
* Obsidian plugin

## Languages

Python first. Nobody has *that* many Obsidian notes. A Go port can wait until the behavior is stable.
