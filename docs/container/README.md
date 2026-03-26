# Container Setup for dataset curation tool

This guide explains how to set up and run the **dataset curation tool**
using **Docker Compose**. Running the tool
in a containerized environment ensures consistent dependencies, easier
configuration, and simplified management.

------------------------------------------------------------------------

## Prerequisites

-   **Docker** installed on your machine.
    👉 [Get Docker](https://www.docker.com/get-started)
-   **Docker Compose** installed.
    > Note: Docker Desktop includes Docker Compose by default.

------------------------------------------------------------------------

## Configuration

### `.env` File
1.  In the root directory of your project, create a `.env` file to store
    environment variables.

2.  Add the following variables and update them with your own values:

    ``` Dotenv
    API_TOKEN=your_api_token_here  # e.g., XXXX-XXXX-XXXX-XXXX
    BASE_URL=dataverse_base_url_here  # e.g., https://demo.borealisdata.ca/
    CURATOR_NAME=Your Name  # e.g., Paul Otlet
    CURATOR_EMAIL=your_email@example.com  # e.g., paul.otlet@example.com
    ```

3.  Make sure the environment variables match your setup before
    proceeding.

### Database Backend

The tool supports two database backends: **DuckDB** (default, file-based) and **PostgreSQL**
(server-based). Configure which one to use via the `.env` file.

#### DuckDB (Default)

No additional configuration is required. DuckDB stores data in local files inside the
`workdir` volume. This is the recommended option for simple setups.

```dotenv
# DB_TYPE defaults to duckdb — no entry needed, or set explicitly:
DB_TYPE=duckdb
```

#### PostgreSQL

To use PostgreSQL, set `DB_TYPE=postgresql` and provide the connection details.
When running with **Docker Compose**, a PostgreSQL service is available via the
`postgres` profile (see [Running with Docker Compose](#running-with-docker-compose)).

```dotenv
DB_TYPE=postgresql

# Option A — single connection URL (takes priority over individual variables below)
DATABASE_URL=postgresql+psycopg://curation:curation@postgres:5432/curation

# Option B — individual connection parameters
POSTGRES_USER=curation
POSTGRES_PASSWORD=curation
POSTGRES_HOST=postgres   # use 'localhost' if connecting to an external instance
POSTGRES_PORT=5432
POSTGRES_DB=curation
```

> **Note:** When using Docker Compose with the built-in `postgres` service, set
> `POSTGRES_HOST=postgres` (the service name). If you connect to an external
> PostgreSQL instance, replace it with the appropriate hostname or IP address.

### `docker-compose.yml` File

1. You might change the `docker-compose.yml` file to adjust volume
   mappings and the location of the `.env` file if necessary.

    docker-compose.yml:
    ```yaml
        ...
        env_file:
        - ./.env  # Configure the path to your .env file if it's located elsewhere
        volumes:
        - ./new_dir:/app/workdir  # Configure the path on the left side of colon to your desired host directory
        - ./res:/app/res  # Configure the path for the res directory
        ...
    ```
------------------------------------------------------------------------

## Running with Docker Compose

1.  Open a terminal and navigate to the root directory of your project
    (where the `docker-compose.yml` file is located).

2.  Create the host directory specified in your `docker-compose.yml`
    under the `volumes` section. For example:

    ``` bash
    mkdir -p ./new_dir
    ```

3. The res folder should contain necessary resources. If it does not exist, create it:

    ``` bash
    mkdir -p ./res
    ```
    It should have the following files:
    ```
    common_file_formats.yaml
    check-list_template_high.yaml
    check-list_template_medium.yaml
    ```

4.  Start the container:

    ``` bash
    docker compose up -d
    ```

    To also start the bundled **PostgreSQL** and **pgAdmin** services (required when
    `DB_BACKEND=postgresql` is set), add the `--profile postgres` flag:

    ``` bash
    docker compose --profile postgres up -d
    ```

    pgAdmin will be available at `http://localhost:5050` (default credentials:
    `curation@example.com` / `curation`).

5.  To stop the container:

    ``` bash
    docker compose down
    ```

For development purposes, you can also use the following command to build and run the container in one step:
``` bash
docker compose down && \
docker compose build && \
docker compose up
```

## Accessing the Application
Once the containers are running, you can access the dataset curation tool by navigating to `http://localhost:9005` in your web browser.