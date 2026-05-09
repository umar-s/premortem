.PHONY: test test-unit test-integration lint clean cli

test:
	uv run --with pytest --with pyyaml --with jsonschema --with click pytest; ret=$$?; [ $$ret -eq 0 ] || [ $$ret -eq 5 ]

test-unit:
	uv run --with pytest --with pyyaml --with jsonschema --with click pytest -m "not integration"

test-integration:
	uv run --with pytest --with pyyaml --with jsonschema --with click pytest -m integration

cli:
	uv run --with click --with pyyaml --with jsonschema scripts/cli.py

lint:
	uv run --with ruff ruff check scripts/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
