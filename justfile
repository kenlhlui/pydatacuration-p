
#!/usr/bin/env -S just --justfile


# Run coverage for tests

run-tests:
    uv sync --dev
    uv pip install -e .
    coverage run -m pytest -v

# Run test with coverage report (HTML)
run-tests-with-report-html:
    just run-tests
    coverage html


# Remove new_dir (with confirmation), recreate it, then rebuild and run containers
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


# Development run (with hot-reload, no docker, starts in 8080 (default) )
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

### Dataverse-specific commands ###

# Run dataverse in docker
start-dataverse:
    cd ./dataverse && docker compose up -d

# Stop dataverse in docker and remove data
stop-dataverse:
    cd ./dataverse && docker compose down && sudo rm -rf ./data

# Get API_TOKEN from dataverse container return as a string (without newline)
show-api-token:  # The @ prefix suppresses echoing that specific command.
    @docker exec postgres_dataverse psql -U dataverse -t -A -c "SELECT t.tokenstring FROM apitoken t JOIN authenticateduser u ON t.authenticateduser_id = u.id WHERE u.superuser = true LIMIT 1;"

dvconfig:
    #!/usr/bin/env bash  
    # The line above is needed to ensure the script runs with bash, which supports certain features that may not be available in other shells.
    API_TOKEN=$(just show-api-token)
    cd ./dataverse/dataverse-sample-data
    rm -rf dvconfig.py
    cp dvconfig.py.sample dvconfig.py
    sed -i "s|api_token = ''|api_token = '$API_TOKEN'|" dvconfig.py
    echo "API token has been set in dvconfig.py"

publish-sample-dataverse:
    cd ./dataverse/dataverse-sample-data && \
    uv venv --clear && uv pip install -r requirements.txt && \
    uv run create_dataverse.py
