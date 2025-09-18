# Docker Setup for Data Curation Tool

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

### `docker-compose.yml` File

1. You might change the `docker-compose.yml` file to adjust volume
   mappings and the location of the `.env` file if necessary.

```yaml
services:
  data-curation-tool:
    build: .
    image: data-curation-tool:latest
    container_name: data-curation-tool
    userns_mode: keep-id
    user: 1000:1000  # Run as non-root user (UID:GID)
    ports:
      - "9005:8000"
    env_file:
      - ./.env   # Your .env file path
    volumes:
      - ./new_dir:/app/workdir:Z,U  # Change ./new_dir (the path before the colon) to your desired directory on your host machine; ensure it exists before running the container
    restart: unless-stopped
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

------------------------------------------------------------------------

## Running with Podman Compose

1.  Ensure `podman-compose` is installed and configured.

2.  Enable the user-level Podman socket (if not already enabled):

    ``` bash
    systemctl --user enable --now podman.socket
    ```

3.  Create the host directory specified in your `docker-compose.yml`
    under the `volumes` section. For example:

    ``` bash
    mkdir -p ./new_dir
    ```

4.  Navigate to the root directory of your project (where the
    `docker-compose.yml` file is located).

5.  Start the containers:

    ``` bash
    podman compose -f podman-compose.yml up -d
    ```

6.  To stop the containers:

    ``` bash
    podman compose down
    ```

------------------------------------------------------------------------

## Accessing the Application
Once the containers are running, you can access the Data Curation Tool by navigating to `http://localhost:9005` in your web browser.