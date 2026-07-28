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
