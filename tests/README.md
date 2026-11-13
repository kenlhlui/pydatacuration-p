# Testing

The project has four kinds of tests:

| Type | What it checks | Where | Runs in CI |
|---|---|---|---|
| [Unit tests](#unit-tests) | Each module on its own, with no network: file checks, unzipping, the database and its migrations, the Dataverse client and utilities | `tests/test_*.py` | Yes |
| [End-to-end tests](#end-to-end-tests-dataverse) | The full curation pipeline (download, checks, Word export) against a real Dataverse | `tests/e2e/` | Yes |
| [Smoke test](#smoke-test) | The app starts and responds | Manual | No |
| [Stress test](#stress-test) | Many datasets sent to a running app, one after another | `tests/curation-run-test.py` | No |

## Set Up

From the repository root:

```sh
uv sync
mkdir -p workdir
```

- `uv sync` installs the test tools (pytest and coverage) and the app itself, in editable mode. You don't need a separate `uv pip install -e .`.
- `workdir/` must exist before the tests run. Some modules create `AppSettings()` when they're imported, and it stops with a `Path does not point to a directory` error if `MAIN_DIR` is missing.

## Unit Tests

```sh
uv run pytest
```

To measure coverage as well:

```sh
uv run coverage run -m pytest -v
uv run coverage report
```

With [`just`](https://github.com/casey/just), `just run-tests` syncs the dependencies and runs the tests with coverage. `just run-tests-with-report-html` also writes an HTML report to `htmlcov/`.

**Skipped tests are expected.** pytest also collects the end-to-end tests, and skips them unless `E2E_BASE_URL`, `E2E_API_TOKEN` and `E2E_PID` are set. To leave them out entirely, as the CI `unit` job does, add `--ignore=tests/e2e`.

`tests/test_schema_snapshot.py` compares the database schema with the saved snapshots in `tests/schema_snapshots/`. After you bump `SCHEMA_VERSION`, follow the [Database Schema Version guide](https://kenlhlui.github.io/pydatacuration-p/db_schema_version/).

## Smoke Test

Check that the app starts and responds. First set up `.env` and `workdir/` as in the [Local Setup guide](https://kenlhlui.github.io/pydatacuration-p/local_setup/), then start the app:

```sh
uv run --env-file .env app.py
```

In another terminal:

```sh
curl http://localhost:9005/api/health
```

It returns `{"status":"ok"}`. Then open <http://localhost:9005> and check that the home page loads. If you changed `APP_PORT`, use that port instead of `9005`.

To fill in the new dataset form faster while you test by hand, set the [New Dataset Form Defaults](https://kenlhlui.github.io/pydatacuration-p/app_settings/#new-dataset-form-defaults) in `.env`.

## End-to-End Tests (Dataverse)

`tests/e2e/` runs the real curation pipeline (download, checks, Word export) against a live Dataverse instance and checks the result for each sample file in `tests/e2e/sample_data/files/`.

They run in GitHub Actions ([`.github/workflows/tests.yml`](https://github.com/kenlhlui/pydatacuration-p/blob/main/.github/workflows/tests.yml)) on every pull request and on pushes to `main`. The `unit` job runs first. Only if it passes does the `e2e` job start a throwaway Dataverse with [gdcc/dataverse-action](https://github.com/gdcc/dataverse-action), seed it with `tests/e2e/seed_dataverse.py`, and run `tests/e2e`. No local Docker is needed.

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

```sh
E2E_BASE_URL=... E2E_API_TOKEN=... uv run tests/e2e/seed_dataverse.py
E2E_BASE_URL=... E2E_API_TOKEN=... E2E_PID=... uv run pytest -v tests/e2e
```

Some sample files are audio and video, so [FFmpeg](https://ffmpeg.org/) must be installed. The CI job installs it.

## Stress Test

`tests/curation-run-test.py` sends each dataset in `tests/doi_list.txt` to the running app's `/api/run-curation` endpoint, one after another, and logs how long each one takes.

1. **Create `tests/doi_list.txt`** with one PID per line, for example `doi:10.80240/FK2/FCZB4A`. Lines that contain `#` are skipped, so you can comment out a dataset. The file is listed in `.gitignore`.
2. **Set up `.env`.** Every dataset uses the same [New Dataset Form Defaults](https://kenlhlui.github.io/pydatacuration-p/app_settings/#new-dataset-form-defaults), such as `BASE_URL` and `CURATOR_NAME`. The script numbers the projects `CUR-001`, `CUR-002` and so on.
3. **Start the app:**

    ```sh
    uv run --env-file .env app.py
    ```

4. **In another terminal, run the script:**

    ```sh
    uv run --env-file .env tests/curation-run-test.py
    ```
