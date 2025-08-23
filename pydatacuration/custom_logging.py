"""This module provides a simple logging setup using loguru with Rich console support."""


from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.text import Text


# Create a global Rich console instance
console = Console()
highlighter = ReprHighlighter()


def rich_sink(message) -> None:
    """Custom sink function that uses Rich console for enhanced output."""
    # Extract the message record
    record = message.record

    # Format timestamp
    timestamp = Text(record['time'].strftime('%Y-%m-%d %H:%M:%S'), style='green')

    # Format level with color
    level = record['level']
    level_styles = {
        'DEBUG': 'dim cyan',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold red',
    }
    level_text = Text(f'{level.name:<8}', style=level_styles.get(level.name, 'white'))

    # Format location info
    location = Text(f'{record["name"]}:{record["function"]}:{record["line"]}', style='dim cyan')

    # Format the actual message with syntax highlighting
    msg_text = Text(str(record['message']))
    msg_text = highlighter(msg_text)

    # Combine all parts
    console.print(timestamp, '│', level_text, '│', location, '│', msg_text)


def setup_logging(log_file_dir: Path | None = None, log_level: str = 'INFO') -> None:
    """Setup loguru configuration for the entire application with Rich console support.

    Args:
        log_file_dir: Optional directory path for log files. If provided, creates debug.log
        log_level: Minimum log level for console output (default: INFO)
    """
    # Remove default handler
    logger.remove()

    # Add Rich console handler for colorful, syntax-highlighted output
    logger.add(
        rich_sink,
        level=log_level,
        format='{message}',  # Message formatting is handled by rich_sink
    )

    # Add file handler if log directory is provided
    if log_file_dir:
        log_file_path = Path(log_file_dir) / 'debug.log'
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_file_path),
            format='{time:YYYY-MM-DD HH:mm:SS} - {name} - {level} - {message}',
            level='DEBUG',
            rotation='10 MB',
            retention='7 days',
            compression='zip',
        )


def get_logger(name: str):
    """Get the loguru logger instance.

    Note: loguru uses a singleton logger, so the name parameter is kept
    for compatibility but doesn't create separate logger instances.

    Args:
        name: Logger name (kept for compatibility)

    Returns:
        The loguru logger instance
    """
    return logger
