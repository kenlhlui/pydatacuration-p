"""The delete project page."""

# ruff: noqa: PLR1702
from pathlib import Path

from nicegui import ui

# Import the API router from the backend module
from pydatacuration.backend.models.app_settings import AppSettings

# Import exceptions for error handling
from pydatacuration.frontend.helpers import NiceGUIHelper
from pydatacuration.frontend.helpers import back_to_main_menu_button

# Import utility functions for project management pages
from pydatacuration.frontend.pages.project_table import render_project_table

# Import styles and styled components
from pydatacuration.frontend.styles import apply_pdc_styles


# Create global settings instance
app_settings = AppSettings()


# Load environment variables
MAIN_DIR: Path = Path(app_settings.main_dir)


@ui.page('/delete')
async def delete_project_page() -> None:
    """Delete project page - shows list of projects with delete buttons."""
    apply_pdc_styles()

    # Container to hold the project list (for refreshing after delete)
    container = ui.column().classes('pdc-container')

    with container:
        # Logo and Header
        ui.html(
            '<img src="/static/UTL.png" alt="University of Toronto Libraries Logo" class="utl-logo">',
            sanitize=False,
        )
        ui.label('Delete Project').classes('pdc-header')

        # Back button
        back_to_main_menu_button()

        # Warning banner
        with ui.element('div').classes('warning-banner'):
            ui.label('⚠️ Warning: Deleting a project is permanent and cannot be undone!').classes(
                'text-lg font-semibold'
            )

        # Project list container (for dynamic updates)
        project_list_container = ui.column()

    async def refresh_project_list(main_dir: Path = MAIN_DIR) -> None:
        """Refresh the project list after deletion."""
        project_list_container.clear()
        with project_list_container:
            schemas = NiceGUIHelper.get_all_schemas(main_dir)
            await render_project_table(schemas, mode='delete', refresh_callback=refresh_project_list)

    # Initial load
    await refresh_project_list(MAIN_DIR)
