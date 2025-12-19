# Running tests

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
