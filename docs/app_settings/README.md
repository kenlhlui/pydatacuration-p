# App Settings (Environment Variables)

Configuration is loaded from a `.env` file in the working directory (or via environment variables). All variable names are case-insensitive, except for the values of `LOG_LEVEL`.

See the (AppSettings model in `app_settings.py`)[pydatacuration/backend/models/app_settings.py] for the full list of available configuration options and their default values. 

Below is a summary of the key environment variables you can set to customize the behavior of the application.

## Application

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | `9005` | Port the application listens on |
| `APP_TITLE` | `Dataverse Curation review Tool` | Display title of the application |
| `APP_FAVICON` | `🔬` | Favicon / icon shown in the UI |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging verbosity (see values below) |

### `LOG_LEVEL` values
See [loguru's documentation on severity levels]((https://loguru.readthedocs.io/en/stable/api/logger.html#logging-levels)) for more details:
| Value | Description |
|---|---|
| `TRACE` | Most verbose — low-level tracing |
| `DEBUG` | Detailed diagnostic information |
| `INFO` | General operational messages (default) |
| `SUCCESS` | Successful operation confirmations |
| `WARNING` | Unexpected but recoverable situations |
| `ERROR` | Errors that affect functionality |
| `CRITICAL` | Severe errors, application may not continue |

## Directories

| Variable | Default | Description |
|---|---|---|
| `MAIN_DIR` | `workdir` | Main working directory (must exist) |
| `RES_DIR` | `res` | Resources directory (must exist) |

## Example `.env`

```dotenv
APP_PORT=9005
LOG_LEVEL=DEBUG
MAIN_DIR=workdir
RES_DIR=res
```