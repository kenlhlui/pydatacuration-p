"""NiceGUI Proof of Concept - With Production-Ready Styling.

This version uses the nicegui_styles module for exact CSS matching.
"""

# ruff: noqa: PLR1702
import os
from pathlib import Path
from urllib.parse import quote
from urllib.parse import urlparse

from nicegui import app
from nicegui import ui
from nicegui.elements.input import Input

# Import the API router from the backend module
from pydatacuration.backend.api import router as api_router
from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.backend.models.setup_form import SetupDefaults
from pydatacuration.backend.models.setup_form import SetupForm

# Import exceptions for error handling
from pydatacuration.frontend.helpers import NiceGUIHelper
from pydatacuration.frontend.helpers import back_to_main_menu_button

# Import styles and styled components
from pydatacuration.frontend.styles import apply_pdc_styles
from pydatacuration.frontend.utils import mount_static_files

# Import the typer app for CLI command execution
from pydatacuration.utils.custom_logging import setup_logging


# Import pydatacuration modules


# Create global settings instance
app_settings = AppSettings()
setup_defaults = SetupDefaults()

# Include the API router in the NiceGUI app with a prefix of /api
app.include_router(api_router, prefix='/api')


# Load environment variables
MAIN_DIR: Path = Path(app_settings.main_dir)
RES_DIR = Path(app_settings.res_dir)

# Setup logging with your custom style
setup_logging(log_file_dir=Path(app_settings.main_dir) / 'logs', log_level='DEBUG')

default_form = SetupForm(**setup_defaults.model_dump(), main_dir=app_settings.main_dir)


# ============================================================================
# Main Entrance Page
# ============================================================================
from pydatacuration.frontend.pages import index  # noqa: F401, E402

# ============================================================================
# New Dataset Setup Page
# ============================================================================
from pydatacuration.frontend.pages import new_dataset  # noqa: F401, E402


# ============================================================================
# Shared Project Table Component
# ============================================================================


async def render_project_table(
    schemas: list[dict],
    mode: str = 'resume',  # 'resume' or 'delete'
    refresh_callback=None,
) -> None:
    """Render a filterable project table.

    Args:
        schemas: List of project schemas
        mode: 'resume' for clickable rows, 'delete' for delete buttons
        refresh_callback: Optional callback to refresh the list after deletion
    """
    if not schemas:
        with ui.element('div').classes('no-projects'):
            ui.label('No projects found').classes('text-xl')
        return

    # Filters
    with ui.element('div').classes('pdc-form-section'):
        ui.label('Filters').classes('pdc-form-section-header')

        with ui.row().classes('gap-4').style('align-items: flex-end;'):
            # Search filter
            with ui.element('div').style('flex: 1; min-width: 200px;'):
                ui.label('Search').classes('pdc-form-label')
                search_input: Input = (
                    ui.input(placeholder='Search Title, DOI, ID (Versioned), URL')
                    .classes('pdc-form-input')
                    .style('width: 100%;')
                )

            # Curator filter
            with ui.element('div').style('flex: 1; min-width: 200px;'):
                ui.label('Filter by Curator').classes('pdc-form-label')
                curators = [''] + sorted(list({s.get('curator_name', '') for s in schemas if s.get('curator_name')}))
                curator_filter = (
                    ui.select(
                        options=curators,
                        value='',
                        with_input=False,
                    )
                    .classes('pdc-status-select')
                    .style('width: 100%;')
                )

            # Clear filters button
            ui.button('Clear Filters', on_click=lambda: clear_filters(search_input, curator_filter)).classes(
                'pdc-btn pdc-btn-secondary'
            )

    # Table container
    table_container = ui.column().style('width: 100%;')

    # Define render function that applies filters
    def render_filtered_table() -> None:
        # Apply filters
        filtered_schemas = schemas
        if search_input.value:
            search_term = search_input.value.lower()
            filtered_schemas = [
                s
                for s in filtered_schemas
                if search_term in str(s.get('ticket_number', '')).lower()
                or search_term in str(s.get('dataset_title', '')).lower()
                or search_term in str(s.get('dataset_pid', '')).lower()
                or search_term in str(s.get('dataset_id', '')).lower()
            ]
        if curator_filter.value:
            filtered_schemas = [s for s in filtered_schemas if s.get('curator_name') == curator_filter.value]

        table_container.clear()
        with table_container:
            ui.label(f'Found {len(filtered_schemas)} project(s)').classes('text-lg font-semibold').style(
                'margin: 20px 0;'
            )

            # Render table
            with ui.element('table').classes('pdc-checklist-table'):
                # Table Header
                with ui.element('thead'), ui.element('tr'):
                    headers = ['Ticket Number', 'Dataset Information', 'Curator', 'Project Last Modified']
                    if mode == 'delete':
                        headers.append('Action')
                    for header in headers:
                        with ui.element('th'):
                            ui.markdown(header)

                # Table Body
                with ui.element('tbody'):
                    for schema in filtered_schemas:
                        row_classes = 'clickable-row' if mode == 'resume' else ''
                        with ui.element('tr').classes(row_classes):
                            # Ticket Number
                            with ui.element('td'):
                                if mode == 'resume':
                                    with (
                                        ui.element('a')
                                        .props(f'href="/checklist?ticket_number={quote(schema["ticket_number"])}"')
                                        .style('color: #3498db; text-decoration: none; font-weight: 600;')
                                    ):
                                        ui.label(f'📋 {schema["ticket_number"]}')
                                else:
                                    ui.label(f'📋 {schema["ticket_number"]}').style('font-weight: 600;')

                            # Dataset Metadata
                            with ui.element('td'):
                                with ui.element('div'):
                                    ui.markdown(
                                        f'**Title:** {schema.get("dataset_title", "N/A")}',
                                    )
                                with ui.element('div'):
                                    ui.markdown(f'**PID:** {schema.get("dataset_pid", "N/A")} ').style(
                                        'display: inline;'
                                    )

                                with ui.element('div'):
                                    ui.markdown(
                                        f'**ID (Versioned):** {schema.get("dataset_id", "N/A")}',
                                    ).style('display: inline;')
                                with ui.element('div'):
                                    dataset_url = schema.get('dataset_url', 'N/A')
                                    parsed = urlparse(dataset_url)
                                    if parsed.scheme in {'http', 'https'}:
                                        # Use proper HTML escaping or NiceGUI's built-in link component
                                        ui.html('URL: ', sanitize=False).style('display: inline; font-weight: bold;')
                                        ui.link(dataset_url, dataset_url, new_tab=True).style('display: inline;')
                            # Curator
                            with ui.element('td'):
                                ui.label(schema.get('curator_name', 'N/A'))

                            # Last Modified
                            with ui.element('td'):
                                ui.label(schema['last_modified'])

                            # Action column (only for delete mode)
                            if mode == 'delete':
                                with ui.element('td').style('text-align: center; vertical-align: middle;'):
                                    ui.button(
                                        '🗑️ Delete',
                                        color='red',
                                        on_click=lambda s=schema: confirm_delete_project(s, refresh_callback),
                                    ).props('unelevated no-caps').classes('pdc-btn pdc-btn-danger')

    # Define clear filters function
    def clear_filters(search_inp: ui.input, curator_sel: ui.select) -> None:
        search_inp.value = ''
        curator_sel.value = ''
        render_filtered_table()

    # Connect filters to table refresh - bind directly to the function
    search_input.on_value_change(lambda e: render_filtered_table())
    curator_filter.on_value_change(lambda e: render_filtered_table())

    # Initial render
    render_filtered_table()


# ============================================================================
# Resume Work Page
# ============================================================================


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


# ============================================================================
# Delete Project Page
# ============================================================================


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

    async def refresh_project_list(main_dir: Path = MAIN_DIR):
        """Refresh the project list after deletion."""
        project_list_container.clear()
        with project_list_container:
            schemas = NiceGUIHelper.get_all_schemas(main_dir)
            await render_project_table(schemas, mode='delete', refresh_callback=refresh_project_list)

    # Initial load
    await refresh_project_list(MAIN_DIR)


def confirm_delete_project(schema: dict, refresh_callback) -> None:
    """Show confirmation dialog before deleting a project."""

    async def handle_delete() -> None:
        success, message = NiceGUIHelper.delete_project(schema.get('ticket_number'), MAIN_DIR)
        if success:
            ui.notify(message, type='positive')
            await refresh_callback()
            dialog.close()
        else:
            ui.notify(message, type='negative')
            dialog.close()

    with ui.dialog() as dialog, ui.card().style('min-width: 400px;'):
        ui.label(f'Delete project "{schema["ticket_number"]}"?').classes('text-xl font-semibold')
        ui.label('This action cannot be undone. All data will be permanently deleted.').classes('text-red-600')

        with ui.row().classes('w-full justify-end gap-2').style('margin-top: 20px;'):
            ui.button('Cancel', on_click=dialog.close).classes('pdc-btn pdc-btn-secondary')
            ui.button('Delete', color='red', on_click=handle_delete).classes('pdc-btn pdc-btn-danger')

    dialog.open()


# ============================================================================
# Checklist Page
# ============================================================================
from pydatacuration.frontend.pages import checklist  # noqa: F401, E402


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
        reconnect_timeout=30,
    )
