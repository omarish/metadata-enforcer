# Roadmap

Post-2.0 ideas, in rough priority order. 2.0 ships Django-style models, path routing, and `check` / `fix` / `watch`.

## Collection-level constraints

Field option `unique=True` and `Meta.constraints` are declared but not enforced yet.

* Uniqueness across notes under a route (e.g. unique `sync_id`)
* Cross-field constraints on a single note
* Referential integrity (ids, paths, wiki-link targets)

## More field types

* `IntegerField` / `FloatField`
* `DateTimeField`
* `EnumField` convenience wrapper
* Custom field subclassing docs + examples

## Schema ergonomics

* Optional `schema.py` generation from observed frontmatter (starter only)
* Multiple schema modules / package layouts
* Typed route helpers

## Presentation

* `--json` output of `ScanResult`
* Health score (% notes passing)
* TUI over the same result model

## Later / low priority

* Go port once behavior is stable
* Obsidian plugin (CLI first)
