
#!/usr/bin/env -S just --justfile

# ─────────────────────────────────────────────────────────
# Testing & Coverage
# ─────────────────────────────────────────────────────────

# Sync dev dependencies, install package in editable mode, and run tests with coverage
run-tests:
    uv sync --dev
    uv pip install -e .
    uv run coverage run -m pytest -v

# Run tests and generate an HTML coverage report (opens in htmlcov/)
run-tests-with-report-html:
    just run-tests
    uv run coverage html

# Write the schema snapshots for the current SCHEMA_VERSION (tests/schema_snapshots/), after bumping it
schema-snapshot:
    -UPDATE_SCHEMA_SNAPSHOT=1 uv run pytest -q tests/test_schema_snapshot.py
    uv run pytest -q tests/test_schema_snapshot.py

# ─────────────────────────────────────────────────────────
# Docker
# ─────────────────────────────────────────────────────────

# Rebuild and run containers
# Optionally pass a profile name and/or `-f` to skip confirmation prompts (order-independent).
# Example: just docker-build-and-run postgres -f
docker-build-and-run *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail
    FORCE=0; PROFILE=""
    for arg in {{ARGS}}; do
        [[ "$arg" == "-f" ]] && FORCE=1 || PROFILE="$arg"
    done
    # Auto-detect postgres profile from .env if not explicitly set
    if [ -z "$PROFILE" ] && [ -f .env ] && grep -qE '^DB_TYPE=postgresql' .env 2>/dev/null; then
        PROFILE="postgres"
        echo "Auto-detected PostgreSQL backend from .env — using profile: postgres"
    fi
    if [ -d ./new_dir ] && [ "$FORCE" -eq 0 ]; then
        read -p "Remove ./new_dir? [y/N] " ans
        case "$ans" in [Yy]*) ;; *) echo "Aborted."; exit 1 ;; esac
    fi
    [ -d ./new_dir ] && rm -rf ./new_dir
    mkdir -p ./new_dir/db
    if [ "$FORCE" -eq 0 ]; then
        read -p "This will stop/remove containers and rebuild. Continue? [y/N] " ans
        case "$ans" in [Yy]*) ;; *) echo "Aborted."; exit 1 ;; esac
    fi
    _UID=$(id -u); _GID=$(id -g)
    env UID=$_UID GID=$_GID COMPOSE_PROFILES="$PROFILE" docker compose down --remove-orphans
    env UID=$_UID GID=$_GID COMPOSE_PROFILES="$PROFILE" docker compose build
    env UID=$_UID GID=$_GID COMPOSE_PROFILES="$PROFILE" docker compose up --force-recreate

# ─────────────────────────────────────────────────────────
# Local Development
# ─────────────────────────────────────────────────────────

# Run the app locally with hot-reload on port 9005 (pass `-f` to skip prompts)
dev-run *ARGS:
    @if [ -d ./workdir ] && [ "{{ARGS}}" != "-f" ]; then \
        read -p "Remove ./workdir? [y/N] " ans; \
        case "$$ans" in [Yy]*) ;; *) echo "Aborted."; exit 1 ;; esac; \
    fi
    @if [ -d ./workdir ]; then rm -rf ./workdir; fi
    @mkdir -p ./workdir/db
    @if [ "{{ARGS}}" != "-f" ]; then \
        read -p "This will stop/remove containers and rebuild. Continue? [y/N] " ans; \
        case "$$ans" in [Yy]*) ;; *) echo "Aborted."; exit 1 ;; esac; \
    fi
    uv sync
    uv run --env-file .env app.py

# ─────────────────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────────────────

# Remove all generated working directories (workdir, new_dir, pgadmin)
clean:
    sudo rm -rf ./workdir
    sudo rm -rf ./new_dir
    sudo rm -rf ./pgadmin
