
#!/usr/bin/env -S just --justfile

# Run coverage for tests
[group: 'pytest-coverage']
run-tests:
    uv sync --dev
    uv pip install -e .
    coverage run -m pytest -v
