# Local Setup (uv)

Run the curation tool on your machine with [uv](https://docs.astral.sh/uv/), without a container. The automated tests run in this same uv environment.

## Prerequisites

| Tool | What it's for | Install |
|---|---|---|
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Installs Python and the dependencies, and runs the app | [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) |
| [FFmpeg](https://ffmpeg.org/) | Checks that audio and video files open | `sudo apt install ffmpeg` (Debian, Ubuntu, WSL) or `brew install ffmpeg` (macOS) |
| [just](https://github.com/casey/just) (optional) | Shortcuts for the commands below | [just installation guide](https://github.com/casey/just#installation) |

You don't need to install Python yourself. If your machine doesn't have Python 3.12 or later, uv downloads it.

## Set Up

Run every command from the repository root.

1. **Install the dependencies:**

   ```sh
   uv sync
   ```

   This creates `.venv/` and installs the app and its dependencies into it.

2. **Create a `.env` file** in the repository root. Its values prefill the new dataset form:

   ```dotenv
   BASE_URL=https://demo.borealisdata.ca/
   CURATOR_NAME="Paul Otlet"
   CURATOR_EMAIL=paul.otlet@example.com
   # API_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

   - **The file must exist**, even if it's empty. Without it, `uv run --env-file .env` stops with `error: No environment file found at: .env`.
   - **Put quotes around values that contain spaces**, like `CURATOR_NAME` above. If one value can't be read, uv skips the whole file with a `Failed to parse environment file` warning.
   - **`API_TOKEN` is optional.** If it's set, the app uses it whenever the token field in the form is empty. Leave it out to paste the token into the form instead.
   - **Don't commit `.env`.** It's listed in `.gitignore`.

   See the [App Settings Guide](../app_settings/README.md) for the other variables, such as `APP_PORT` and `LOG_LEVEL`.

3. **Create the working directory:**

   ```sh
   mkdir -p workdir
   ```

   The app keeps its database, logs and downloaded datasets here. If the directory doesn't exist, the app won't start, and the error mentions `main_dir` and `Path does not point to a directory`. To use another directory, set `MAIN_DIR` in `.env`.

## Run

```sh
uv run --env-file .env app.py
```

Open <http://localhost:9005>, or the port set in `APP_PORT`. To stop the app, press <kbd>Ctrl</kbd>+<kbd>C</kbd>.

Always start the app from the repository root. It looks for `.env`, `res/`, `workdir/` and its static files relative to the current directory.

To check from the terminal that the app is running:

```sh
curl http://localhost:9005/api/health
```

It returns `{"status":"ok"}`.

### With `just`

```sh
just dev-run
```

This runs `uv sync`, then `uv run --env-file .env app.py`.

> [!WARNING]
> `just dev-run` **deletes `./workdir`** before it starts, including the DuckDB database and every project in it. It asks you to confirm first. `just dev-run -f` deletes it without asking. To keep your projects, use `uv run --env-file .env app.py` instead.

## Database

The app uses DuckDB by default, and it needs no setup. The app creates the database file, `workdir/db/db.duckdb`, when you set up your first project.

To use PostgreSQL instead, add the connection details of a running server to `.env`:

```dotenv
DB_TYPE=postgresql
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/DATABASE
```

Instead of `DATABASE_URL`, you can set `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB`, plus `POSTGRES_HOST` (default `localhost`) and `POSTGRES_PORT` (default `5432`). If `DATABASE_URL` is set, the app ignores the other variables.

## Prefill the Form for Testing

To fill in the new dataset form faster while you test, add any of these to `.env`:

```dotenv
PID=doi:10.80240/FK2/FCZB4A
PROJECT_NUMBER=CUR-999
COLLECTION_ALIAS=toronto
CHECKLIST=checklist-high.yaml
FORCE_DELETE=true
CHECK_ZIP=true
```

| Variable | Form field |
|---|---|
| `PID` | Dataset PID |
| `PROJECT_NUMBER` | Project Number (letters, numbers, `-` and `_` only) |
| `COLLECTION_ALIAS` | Dataverse Collection Alias |
| `CHECKLIST` | The checklist. Use the file name of a checklist in `res/`, e.g. `checklist-high.yaml` |
| `FORCE_DELETE` | Replace existing project (if exists) |
| `CHECK_ZIP` | Unzip archive files and check contents |

The app reads `.env` when it starts. Restart it after you change the file.
