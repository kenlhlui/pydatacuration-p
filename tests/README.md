# Running tests

## Justfile way

If you have [`just`](https://github.com/casey/just) installed, you can run the tests with coverage using the following command:

```bash
just run-tests
```

## Manual way

1. First, ensure you have `pytest` installed. With uv:

    ```bash
    uv sync --dev
    ```
2. Next, to ensure the path is set correctly when running pytests, install the package in editable mode:

    ```bash
    uv pip install -e .
    ```

3. Finally, run the tests using pytest, with coverage:

    ```bash
    coverage run -m pytest -v
    ```

4. To view the coverage report, run:

    ```bash
    coverage report
    ```

# To run the stress test, use the following command:

You will first need to create a `doi_list.txt` file in the `tests` directory with the DOIs you want to test. Each DOI should be on a new line.

You can commend out any DOIs you don't want to test by adding a `#` at the beginning of the line.

You will first need to start the tool ()

```bash
just dev-run -f
```

Then run the following command in the root directory of the project:
```bash
uv pip install -e . && uv run --env-file=.env tests/curation-run-test.py # Load the .env file to set the environment variables needed for the test
```

# End-to-end tests (Dataverse)

`tests/e2e/` runs the real curation pipeline (download, checks, Word export) against a live Dataverse instance and checks the result for each sample file in `tests/e2e/sample_data/files/`.

They run in GitHub Actions (`.github/workflows/e2e.yml`) on every pull request and on pushes to `main`. The workflow starts a throwaway Dataverse with [gdcc/dataverse-action](https://github.com/gdcc/dataverse-action), seeds it with `tests/e2e/seed_dataverse.py`, then runs the whole test suite. No local Docker is needed.

- To iterate on a branch, open a draft PR; every push re-runs the workflow.
- Follow a run from the terminal with `gh run watch`.
- Each run uploads an `e2e-workdir` artefact with the logs, `check_results.json`, the DuckDB file and the Word report.

Locally, the e2e tests are skipped unless these are set:

| Variable | Meaning |
|---|---|
| `E2E_BASE_URL` | Dataverse base URL, host only (e.g. `http://127.0.0.1:8080`) |
| `E2E_API_TOKEN` | API token that can read the draft dataset and its restricted files |
| `E2E_PID` | PID of the seeded dataset, printed by `seed_dataverse.py` |

To use another Dataverse you have access to, seed it, then run the tests with the PID it prints:

```bash
E2E_BASE_URL=... E2E_API_TOKEN=... uv run tests/e2e/seed_dataverse.py
E2E_BASE_URL=... E2E_API_TOKEN=... E2E_PID=... uv run pytest -v tests/e2e
```
