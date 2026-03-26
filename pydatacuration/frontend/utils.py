"""Utility functions for the frontend."""

from pathlib import Path

from loguru import logger
from nicegui import App


def mount_static_files(app: App, static_path: Path) -> None:
    """Mount static files from the frontend directory."""
    # Determine the correct path to static files
    # must be done before ui.run() and before any routes that use static files
    if not static_path.exists():
        static_path = Path(__file__).parent / 'pydatacuration' / 'frontend'

    if static_path.exists():
        # Add static files route
        app.add_static_files('/static', str(static_path))
        logger.info('✓ Static files mounted:', static_path.absolute())
    else:
        logger.warning('⚠ WARNING: Static directory not found!')
        logger.warning('Looked for:', static_path.absolute())
