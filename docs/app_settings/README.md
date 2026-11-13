# App Settings (Environment Variables)

Configuration is loaded from a `.env` file in the working directory (or via environment variables). All variable names are case-insensitive, except for the values of `LOG_LEVEL`.

## Settings

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

## Example `.env`

```dotenv
APP_PORT=9005
LOG_LEVEL=DEBUG
MAIN_DIR=workdir
RES_DIR=res
```