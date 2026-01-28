
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