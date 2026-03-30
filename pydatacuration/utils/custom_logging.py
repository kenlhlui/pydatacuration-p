"""Logging setup using loguru with Rich console plus global and per-project sinks."""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.text import Text


# Console highlighter
console = Console()
highlighter = ReprHighlighter()

# Keep track of added sinks to avoid duplicates when commands run multiple times
_CONSOLE_SINK_ID: int | None = None
_GLOBAL_SINK_ID: int | None = None
_CLI_SINK_IDS: dict[Path, int] = {}


def rich_sink(message) -> None:
    """Render a log record with Rich to the terminal."""
    record = message.record
    timestamp = Text(record['time'].strftime('%Y-%m-%d %H:%M:%S'), style='green')
    level = record['level']
    level_styles = {
        'DEBUG': 'dim cyan',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold red',
    }
    level_text = Text(f'{level.name:<8}', style=level_styles.get(level.name, 'white'))
    location = Text(f'{record["name"]}:{record["function"]}:{record["line"]}', style='dim cyan')
    msg_text = highlighter(Text(str(record['message'])))
    console.print(timestamp, '│', level_text, '│', location, '│', msg_text)


def setup_global_logging(log_file_dir: Path | None = None, log_level: str = 'INFO') -> None:
    """Configure console + global file sink.

    Args:
        log_file_dir (Path | None): Directory for the global log file (debug.log).
        log_level (str): Minimum level for console output.

    Returns:
        None: Adds console sink and an optional global file sink.
    """
    global _CONSOLE_SINK_ID, _GLOBAL_SINK_ID
    logger.remove()
    _CONSOLE_SINK_ID = logger.add(rich_sink, level=log_level, format='{message}')

    if log_file_dir:
        path = Path(log_file_dir) / 'debug.log'
        path.parent.mkdir(parents=True, exist_ok=True)
        _GLOBAL_SINK_ID = logger.add(
            str(path),
            format='{time:YYYY-MM-DD HH:mm:ss} | {name}:{function}:{line} | {level} | {message}',
            level='DEBUG',
            rotation='10 MB',
            retention='14 days',
            enqueue=True,
        )


def add_cli_run_logging(cli_log_dir: Path) -> Path:
    """Attach a per-project file sink (e.g., <project>/log_files/debug.log).

    Args:
        cli_log_dir (Path): Project-specific log directory.

    Returns:
        Path: The path to the CLI project log file.
    """
    path = Path(cli_log_dir) / 'debug.log'
    if cli_log_dir not in _CLI_SINK_IDS:
        path.parent.mkdir(parents=True, exist_ok=True)
        _CLI_SINK_IDS[cli_log_dir] = logger.add(
            str(path),
            format='{time:YYYY-MM-DD HH:mm:ss} | {name}:{function}:{line} | {level} | {message}',
            level='DEBUG',
            rotation='10 MB',
            retention='14 days',
            enqueue=True,
        )
    return path


def setup_logging(log_file_dir: Path | None = None, log_level: str = 'DEBUG') -> None:
    """Backward-compatible wrapper (kept so existing imports keep working).

    Args:
        log_file_dir (Path | None): Directory for a single log file.
        log_level (str): Console log level.

    Returns:
        None: Calls setup_global_logging.
    """
    setup_global_logging(log_file_dir=log_file_dir, log_level=log_level)
