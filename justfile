# justfile — task runner for my-day-os Python code.
# Scope: Python project code only (uv + ruff). Run `just` to list recipes.

# List available recipes
default:
    @just --list

# Install/sync dependencies from pyproject.toml + uv.lock
sync:
    uv sync

# Lint Python code
lint:
    uv run ruff check .

# Lint and auto-fix what Ruff can fix
lint-fix:
    uv run ruff check . --fix

# Format Python code
fmt:
    uv run ruff format .

# Check formatting without writing changes
fmt-check:
    uv run ruff format . --check

# Run all checks (lint + format check) — CI-safe, no writes
check: lint fmt-check

# Show the next available ID in every sequence (no allocation)
ids:
    uv run python scripts/next_id.py --list

# Allocate the next ID(s) in a sequence: L, C, K, ADR, SPEC
next-id seq count="1":
    uv run python scripts/next_id.py {{seq}} --count {{count}}

# Peek a sequence's next ID without allocating it
peek-id seq:
    uv run python scripts/next_id.py {{seq}} --peek
