.PHONY: install test

install:
	uv tool install --force .
	uv tool update-shell

test:
	uv run pytest -q
