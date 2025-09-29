# Container Setup for Data Curation Tool

This guide explains how to set up and run the **Data Curation Tool**
using either **Docker Compose** or **Podman Compose**. Running the tool
in a containerized environment ensures consistent dependencies, easier
configuration, and simplified management.

------------------------------------------------------------------------

## Prerequisites

-   **Docker** installed on your machine.
    👉 [Get Docker](https://www.docker.com/get-started)
-   **Docker Compose** installed.
    > Note: Docker Desktop includes Docker Compose by default.

For Podman users: - **Podman** and **podman-compose** installed.
👉 [Installation
instructions](https://github.com/containers/podman-compose)

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

### `docker-compose.yml`/`podman-compose.yml` File

1. You might change the `docker-compose.yml` or the `podman-compose.yml` file to adjust volume
   mappings and the location of the `.env` file if necessary.

    docker-compose.yml:
    ```yaml
        ...
        env_file:
        - ./.env  # Configure the path to your .env file if it's located elsewhere
        volumes:
        - ./new_dir:/app/workdir  # Configure the path on the left side of colon to your desired host directory
        ...
    ```
    podman-compose.yml:
    ```yaml
        ...
        env_file:
        - ./.env  # Configure the path to your .env file if it's located elsewhere
        volumes:
        - ./new_dir:/app/workdir:Z,U  # Configure the path on the left side of colon to your desired host directory
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

3.  Start the container:

    ``` bash
    docker compose up -d
    ```

4.  To stop the container:

    ``` bash
    docker compose down
    ```

For development purposes, you can also use the following command to build and run the container in one step:
``` bash
docker compose down && \
docker compose build && \
docker compose up
```

------------------------------------------------------------------------

## Running with Podman Compose

1. Open a terminal and navigate to the root directory of your project (where the `podman-compose.yml` file is located).

2.  Ensure `podman-compose` is installed and configured.

3.  Enable the user-level Podman socket (if not already enabled):

    ``` bash
    systemctl --user enable --now podman.socket
    ```

4.  Create the host directory specified in your `docker-compose.yml`
    under the `volumes` section. For example:

    ``` bash
    mkdir -p ./new_dir
    ```

5.  Navigate to the root directory of your project (where the
    `docker-compose.yml` file is located).

6.  Start the containers:

    ``` bash
    podman compose -f podman-compose.yml up -d
    ```

7.  To stop the containers:

    ``` bash
    podman compose down
    ```

For development purposes, you can also use the following command to
build and run the containers in one step:
``` bash
podman compose -f podman-compose.yml down && \
podman compose -f podman-compose.yml build && \
podman compose -f podman-compose.yml up
```

------------------------------------------------------------------------

## Accessing the Application
Once the containers are running, you can access the Data Curation Tool by navigating to `http://localhost:9005` in your web browser.