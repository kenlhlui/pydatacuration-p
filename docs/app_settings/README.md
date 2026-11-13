# App Settings (Environment Variables)

Configuration is loaded from a `.env` file in the working directory (or via environment variables). Variable names are case-insensitive, and so are `LOG_LEVEL` values: `LOG_LEVEL=debug` works the same as `LOG_LEVEL=DEBUG`.

## Application

The table below is generated from the [`AppSettings` model]({{ repo_blob }}/pydatacuration/backend/models/app_settings.py) at build time, so it always matches the code. Each field maps to an environment variable of the same name in uppercase; for example, `app_port` is set with `APP_PORT`.

::: pydatacuration.backend.models.app_settings.AppSettings

### `LOG_LEVEL` values
See [loguru's documentation on severity levels](https://loguru.readthedocs.io/en/stable/api/logger.html#logging-levels) for more details:

| Value | Description |
|---|---|
| `TRACE` | Most verbose — low-level tracing |
| `DEBUG` | Detailed diagnostic information |
| `INFO` | General operational messages (default) |
| `SUCCESS` | Successful operation confirmations |
| `WARNING` | Unexpected but recoverable situations |
| `ERROR` | Errors that affect functionality |
| `CRITICAL` | Severe errors, application may not continue |

## Database

The table below is generated from the [`DBSettings` model]({{ repo_blob }}/pydatacuration/db/settings.py), and its names map to environment variables the same way. DuckDB is the default and needs no settings. The `POSTGRES_*` and `DATABASE_URL` settings are only used when `DB_TYPE=postgresql`.

> [!WARNING]
> PostgreSQL support isn't maintained or tested.

For setup steps, see [PostgreSQL in the Local Setup Guide](../local_setup/README.md#postgresql-alternative) or [PostgreSQL in the Container Guide](../container/README.md#postgresql).

::: pydatacuration.db.settings.DBSettings

## New Dataset Form Defaults

These settings prefill the new dataset form, so you don't have to type the same values for every project. All of them are optional, and the prefilled values can still be changed in the form. The table below is generated from the [`SetupDefaults` model]({{ repo_blob }}/pydatacuration/backend/models/setup_form.py), and its names map to environment variables the same way.

::: pydatacuration.backend.models.setup_form.SetupDefaults

## Example `.env`

```dotenv
APP_PORT=9005
LOG_LEVEL=DEBUG
MAIN_DIR=workdir
RES_DIR=res
```