# U of T Dataverse dataset curation tool

> [!WARNING]
> This tool is under active development and is not yet production-ready. Please use it at your own risk.

A dataset curation tool for Dataverse repositories, with a web interface.

<img src="docs/full-tool-demo.gif" alt="The full curation tool demo" width="70%" height="70%">

## 🚀 Quick Start

### Prerequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [FFmpeg](https://ffmpeg.org/), to check audio and video files (Optional, but recommended)

### ⚙️ Setup & Run
From the repository root:
```sh
uv sync
touch .env  # then add your settings, see the guide below
mkdir -p workdir
uv run --env-file .env app.py
```
Then open <http://localhost:9005>.

Refer to the [Local Setup Guide](docs/local_setup/README.md) for the `.env` settings, PostgreSQL, and `just dev-run`.

### Options
#### 📂 Custom Status Options
See the [Custom Status Options Guide](docs/custom_status_options/README.md) for instructions on how to define and use custom status options.
#### 🌱 Environment Variables
See the [App Settings (Environment Variables) Guide](docs/app_settings/README.md) for instructions on how to configure the application using environment variables.

## 🐋 Docker

> [!CAUTION]
> The container setup isn't covered by the automated tests and may be out of date.

### Prerequisites
- **Docker** and **Docker Compose** installed
  - 👉 [Get Docker](https://www.docker.com/get-started)
  - Note: Docker Desktop includes Docker Compose by default

### ⚙️ Setup & Run
Refer to the [Container Guide](docs/container/README.md) for detailed setup instructions.

> [!NOTE]
> Or if you have just installed, then you can simply run:
> ```sh
> just docker-build-and-run -f # The -f flag skips the confirmation prompt for removing existing './workdir'
> or
> just docker-build-and-run postgres -f # To include the postgres profile
> ```



### 🏗️ Development Mode
For development with rebuild and reloading the container, run:
```sh
docker compose down && docker compose build && docker compose up
```

To clean up the folders, run:
```sh
just clean
```
This will delete the `./workdir`, `./new_dir/` and `./pgadmin/` folders,

## 🧪 Validating the Checklist
See the [Checklist Validator CLI Guide](docs/checklist/README.md) for instructions on how to validate the checklist using the command line interface (CLI).

## 🗄️ Changing the Database Schema
The database layout has its own version number, separate from the app version. See the [Database Schema Version Guide](docs/db_schema_version/README.md) for how to change the schema, upgrade a database, and how the version check works.

## ⬆️ Bump the version
Prerequisites:
1. [Commitizen](https://commitizen-tools.github.io/commitizen/)

This repository has set up [Commitizen](https://commitizen-tools.github.io/commitizen/) for automatic version bumping. To bump the version, run the following command in the main branch:
```sh
cz bump
```
Test the version bumping by running:
```sh
cz bump --dry-run
```