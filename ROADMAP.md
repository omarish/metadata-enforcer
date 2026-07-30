# Roadmap

Intentional non-goals for v1, in rough priority order.

## High priority

### `metadata-enforcer init` / wizard

Generate a starting `columns.yaml` from an existing vault:

* Scan frontmatter keys (and frequencies)
* Infer coarse types; suggest `format: date` / low-cardinality `enum`s
* Emit an all-optional field map (`required` omitted / false)
* Non-interactive first; interactive prompts later

### Health score

A single vault/folder “make the number go up” metric (e.g. % notes passing, weighted by required fields / enum compliance / unknown-key rate). Complements binary exit codes: CI stays strict; daily use can chase gradual improvement. Exact formula TBD; surface in stdout, watch, and later TUI.

## Collection-level constraints

Envelope siblings next to `schema:` (not JSON Schema keywords):

* `unique` — uniqueness across notes under the scan scope
* `references` — referential integrity (ids, paths, wiki-link targets, etc.)

Exact DSL TBD. v1 rejects unknown top-level keys so these are not silently ignored before they exist.

## Multi-schema discovery

Nested `columns.yaml` files with nearest-ancestor (or similar) rules, once single-schema runs are solid.

## Apply defaults

Opt-in command to write JSON Schema `default` values into frontmatter. Never implicit; notes stay sacred unless you ask.

## Presentation

* `--json` output of the result model
* TUI over the same result model (stdout first)

## Later / low priority

* Go port once behavior is stable
* Obsidian plugin (explicitly low priority — CLI first)
