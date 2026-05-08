"""NiceGUI application entry point for U of T Dataverse Curation Tool."""

import os
from pathlib import Path

from nicegui import app
from nicegui import ui

# Import the API router from the backend module
from pydatacuration.backend.api import router as api_router

# Import the data models for application settings and setup defaults
from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.backend.models.setup_form import SetupDefaults

# Import the utility function to mount static files for the frontend
from pydatacuration.frontend.utils import mount_static_files
from pydatacuration.utils.custom_logging import setup_logging


# Create global settings instance
app_settings = AppSettings()
setup_defaults = SetupDefaults()

# Include the API router in the NiceGUI app with a prefix of /api
app.include_router(api_router, prefix='/api')


# Setup logging with your custom style
setup_logging(log_file_dir=Path(app_settings.main_dir) / 'logs', log_level=app_settings.log_level)


# ============================================================================
# Main Entrance Page
# ============================================================================
from pydatacuration.frontend.pages import index  # noqa: F401, E402, I001

# ============================================================================
# Delete Project Page
# ============================================================================
from pydatacuration.frontend.pages import delete  # noqa: F401, E402, I001

# ============================================================================
# Checklist Page
# ============================================================================
from pydatacuration.frontend.pages import checklist  # noqa: F401, E402, I001

# ============================================================================
# New Dataset Setup Page
# ============================================================================
from pydatacuration.frontend.pages import new_dataset  # noqa: F401, E402, I001

# ============================================================================
# Resume Work Page
# ============================================================================
from pydatacuration.frontend.pages import resume  # noqa: F401, E402, I001


# ============================================================================
# Run the application
# ============================================================================

if __name__ in {'__main__', '__mp_main__'}:
    # Must mount before ui.run() and before any routes that use static files
    mount_static_files(
        app, Path('pydatacuration/frontend')
    )  # FIXME: this should be more robust to different execution contexts
    ui.run(
        title=app_settings.app_title,
        favicon=app_settings.app_favicon,
        port=app_settings.app_port,
        storage_secret=str(os.urandom(16)),
        reconnect_timeout=app_settings.app_reconnect_timeout,
        reload=app_settings.app_reload,
        uvicorn_reload_dirs='pydatacuration, app.py',
    )
