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

# Lint SQL files (SQLFluff, sqlite dialect; config in .sqlfluff)
lint-sql:
    uv run sqlfluff lint mydayos

# Auto-fix SQL lint violations
fmt-sql:
    uv run sqlfluff fix mydayos --force

# Run the test suite (stdlib unittest; pytest graduates later from BACKLOG)
test:
    uv run python -m unittest discover -s tests

# Run all checks (lint + format check + tests) — CI-safe, no writes
check: lint lint-sql fmt-check test

# Session status report: where we are & what's ready to go
status:
    @echo "── my-day-os · status ─────────────────────────────"
    @git log --oneline -5
    @echo ""
    @echo "── Work queue (TODO.md — head is next up) ─────────"
    @awk '/^```csv/{f=1;next} /^```/{f=0} f' TODO.md | head -5
    @echo ""
    @echo "── Working tree ───────────────────────────────────"
    @git status --short || true
    @echo ""
    @echo "── ID high-water marks ────────────────────────────"
    @uv run python scripts/next_id.py --list

# Audit the canon: frontmatter <-> POLICY <-> ID ledger; read-only (ADR-0006 §5)
audit *args:
    uv run python scripts/audit.py {{args}}

# Fire a test macOS notification (hello-world for the preemption channel)
notify-test msg="The deli is open — ticket rail online.":
    uv run python -m mydayos.notify "{{msg}}"

# Show the next available ID in every sequence (no allocation)
ids:
    uv run python scripts/next_id.py --list

# Allocate the next ID(s) in a sequence: L, C, K, ADR, SPEC
next-id seq count="1":
    uv run python scripts/next_id.py {{seq}} --count {{count}}

# Peek a sequence's next ID without allocating it
peek-id seq:
    uv run python scripts/next_id.py {{seq}} --peek
