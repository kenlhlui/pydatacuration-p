
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


# Remove workdir (with confirmation), recreate it, then rebuild and run containers
docker-build-and-run *ARGS:
    @if [ -d ./workdir ] && [ "{{ARGS}}" != "-f" ]; then \
        read -p "Remove ./workdir? [y/N] " ans; \
        case "$$ans" in [Yy]*) ;; *) echo "Aborted."; exit 1 ;; esac; \
    fi
    @if [ -d ./workdir ]; then rm -rf ./workdir; fi
    @mkdir -p ./workdir
    @if [ "{{ARGS}}" != "-f" ]; then \
        read -p "This will stop/remove containers and rebuild. Continue? [y/N] " ans; \
        case "$$ans" in [Yy]*) ;; *) echo "Aborted."; exit 1 ;; esac; \
    fi
    docker compose down
    docker compose build
    docker compose up
