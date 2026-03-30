"""The resume project page."""

# ruff: noqa: PLR1702
from pathlib import Path

from nicegui import ui

# Import the API router from the backend module
from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.backend.models.setup_form import SetupDefaults

# Import exceptions for error handling
from pydatacuration.frontend.helpers import NiceGUIHelper
from pydatacuration.frontend.helpers import back_to_main_menu_button

# Import utility functions for project management pages
from pydatacuration.frontend.pages.project_table import render_project_table

# Import styles and styled components
from pydatacuration.frontend.styles import apply_pdc_styles


# Create global settings instance
app_settings = AppSettings()
setup_defaults = SetupDefaults()


# Load environment variables
MAIN_DIR: Path = Path(app_settings.main_dir)


@ui.page('/resume')
async def resume_work_page() -> None:
    """Resume work page - shows list of existing projects."""
    apply_pdc_styles()

    with ui.column().classes('pdc-container'):
        # Logo and Header
        ui.html(
            '<img src="/static/UTL.png" alt="University of Toronto Libraries Logo" class="utl-logo">',
            sanitize=False,
        )
        ui.label('Resume Project').classes('pdc-header')

        # Back button
        back_to_main_menu_button()

        # Get all schemas/projects
        schemas = NiceGUIHelper.get_all_schemas(MAIN_DIR)

        # Render project table
        await render_project_table(schemas, mode='resume')
