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