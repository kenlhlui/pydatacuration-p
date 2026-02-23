
#!/usr/bin/env -S just --justfile

# ─────────────────────────────────────────────────────────
# Testing & Coverage
# ─────────────────────────────────────────────────────────

# Sync dev dependencies, install package in editable mode, and run tests with coverage
run-tests:
    uv sync --dev
    uv pip install -e .
    coverage run -m pytest -v

# Run tests and generate an HTML coverage report (opens in htmlcov/)
run-tests-with-report-html:
    just run-tests
    coverage html

# ─────────────────────────────────────────────────────────
# Docker
# ─────────────────────────────────────────────────────────

# Rebuild and run containers (pass `-f` to skip all confirmation prompts)
docker-build-and-run *ARGS:
    @if [ -d ./new_dir ] && [ "{{ARGS}}" != "-f" ]; then \
        read -p "Remove ./new_dir? [y/N] " ans; \
        case "$$ans" in [Yy]*) ;; *) echo "Aborted."; exit 1 ;; esac; \
    fi
    @if [ -d ./new_dir ]; then rm -rf ./new_dir; fi
    @mkdir -p ./new_dir/db
    @if [ "{{ARGS}}" != "-f" ]; then \
        read -p "This will stop/remove containers and rebuild. Continue? [y/N] " ans; \
        case "$$ans" in [Yy]*) ;; *) echo "Aborted."; exit 1 ;; esac; \
    fi
    UID=$(id -u) GID=$(id -g) docker compose down
    UID=$(id -u) GID=$(id -g) docker compose build
    UID=$(id -u) GID=$(id -g) docker compose up --force-recreate

# ─────────────────────────────────────────────────────────
# Local Development
# ─────────────────────────────────────────────────────────

# Run the app locally with hot-reload on port 8080 (pass `-f` to skip prompts)
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
    uv run app.py

# ─────────────────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────────────────

# Remove all generated working directories (workdir, new_dir, pgadmin)
clean:
    sudo rm -rf ./workdir
    sudo rm -rf ./new_dir
    sudo rm -rf ./pgadmin

# ─────────────────────────────────────────────────────────
# Dataverse — Lifecycle
# ─────────────────────────────────────────────────────────

# Start the Dataverse stack in detached mode
start-dataverse:
    cd ./dataverse && docker compose up -d

# Stop the Dataverse stack and purge its persistent data
stop-dataverse:
    cd ./dataverse && docker compose down && sudo rm -rf ./data

# ─────────────────────────────────────────────────────────
# Dataverse — Configuration & Auth
# ─────────────────────────────────────────────────────────

# Retrieve the superuser API token from the Dataverse database
show-api-token:
    @docker exec postgres_dataverse psql -U dataverse -t -A -c "SELECT t.tokenstring FROM apitoken t JOIN authenticateduser u ON t.authenticateduser_id = u.id WHERE u.superuser = true LIMIT 1;"

# Generate dvconfig.py with the current API token baked in
dvconfig:
    #!/usr/bin/env bash
    API_TOKEN=$(just show-api-token)
    cd ./dataverse/dataverse-sample-data
    rm -rf dvconfig.py
    cp dvconfig.py.sample dvconfig.py
    sed -i "s|api_token = ''|api_token = '$API_TOKEN'|" dvconfig.py
    echo "API token has been set in dvconfig.py"

# ─────────────────────────────────────────────────────────
# Dataverse — Sample Data Publishing
# ─────────────────────────────────────────────────────────

# Create and publish a sample Dataverse collection
publish-sample-dataverse:
    just dvconfig
    cd ./dataverse/dataverse-sample-data && \
    pwd && \
    uv venv --clear && uv pip install -r requirements.txt && \
    .venv/bin/python create_dataverse.py

# Create and publish a sample dataset within the Dataverse collection
publish-sample-dataset:
    just dvconfig
    cd ./dataverse/dataverse-sample-data && \
    uv venv --clear && uv pip install -r requirements.txt && \
    .venv/bin/python create_dataset.py

# Wait for the Dataverse API, then publish both sample dataverse and dataset
publish:
    #!/usr/bin/env bash
    echo "Waiting for Dataverse API to be ready..."
    while true; do
        API_TOKEN=$(just show-api-token)
        if [ -n "$API_TOKEN" ] && curl -sf "http://localhost:8080/api/users/:me" -H "X-Dataverse-key: $API_TOKEN" | grep -q '"status":"OK"'; then
            echo "Dataverse is ready!"
            echo "Wait additional 5 seconds to ensure all services are up..."
            sleep 5
            break
        fi
        echo "Not ready yet, retrying in 5 seconds..."
        sleep 5
    done
    just publish-sample-dataverse
    just publish-sample-dataset