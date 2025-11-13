"""NiceGUI Proof of Concept - With Production-Ready Styling.

This version uses the nicegui_styles module for exact CSS matching.
"""

# ruff: noqa: PLR1702
import asyncio
import os
from pathlib import Path

import orjson
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from nicegui import app
from nicegui import app as nicegui_app
from nicegui import ui
from nicegui.elements.input import Input
from sqlmodel import SQLModel

from pydatacuration.custom_logging import logger
from pydatacuration.custom_logging import setup_logging

# Import pydatacuration modules
from pydatacuration.directory_manager import DirectoryManager
from pydatacuration.duck_db import DuckDB
from pydatacuration.frontend.helpers import NiceGUIHelper
from pydatacuration.frontend.helpers import back_to_main_menu_button
from pydatacuration.frontend.helpers import priority_options
from pydatacuration.frontend.helpers import status_options

# Import styles and styled components
from pydatacuration.frontend.styles import apply_pdc_styles
from pydatacuration.frontend.styles import create_checklist_select
from pydatacuration.frontend.styles import create_info_grid
from pydatacuration.frontend.styles import create_priority_badge
from pydatacuration.frontend.styles import create_status_select
from pydatacuration.main import CtxObj

# Import the typer app for CLI command execution
from pydatacuration.main import run_all
from pydatacuration.sqlmodels import DuckDBmodels


# Load environment variables
load_dotenv(override=True)
MAIN_DIR: Path = Path(os.getenv('MAIN_DIR', 'workdir'))

# Setup logging with your custom style
setup_logging(log_file_dir=MAIN_DIR / 'logs', log_level='DEBUG')

# temp: set up the RES_DIR constant
RES_DIR = Path('res')


# ============================================================================
# Data Models
# ============================================================================


class SetupRequest(SQLModel):
    """Setup form data model."""

    pid: str
    base_url: str | None = None
    api_token: str | None = None
    ticket_number: str
    curator_name: str
    curator_email: str
    main_dir: str = 'workdir'
    force_del: bool = False
    check_zip: bool = True
    checklist: str = 'high'
    collection_alias: str | None = None


# ============================================================================
# Main Entrance Page
# ============================================================================


@ui.page('/')
async def main_page() -> None:
    """Main entrance page to start new project, resume work, or delete project."""
    apply_pdc_styles()

    # Add custom CSS for main page
    ui.add_head_html("""
    <style>
        /* Center everything on the page */
        .nicegui-content {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 100vh !important;
            padding: 20px !important;
        }
        .main-container {
            max-width: 1000px;
            width: 90%;
            background-color: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            align-items: center;
        }
        .main-container > * {
            width: 100%;
        }
        body {
            background: #1E3765 !important;
            min-height: 100vh;
        }
        .option-card {
            background-color: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 35px;
            margin: 0;
            cursor: pointer;
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .option-card:hover {
            border-color: #3498db;
            background-color: #ebf3fd;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.2);
        }
        .option-title {
            font-size: 1.4rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 12px;
        }
        .option-description {
            color: #6c757d;
            font-size: 1rem;
        }
        .icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }
        .options-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-bottom: 25px;
        }
        .resume-container {
            display: flex;
            justify-content: center;
            width: 100%;
            margin-top: 0;
        }
        .resume-card {
            width: 70%;
            max-width: 600px;
        }
        @media (max-width: 768px) {
            .options-grid {
                grid-template-columns: 1fr;
            }
            .resume-card {
                width: 100%;
            }
        }
    </style>
    """)

    with ui.column().classes('main-container'):
        # Logo and Header container (centered)
        with ui.element('div').style('text-align: center; width: 100%;'):
            ui.html(
                '<img src="/static/UTL.png" '
                'alt="University of Toronto Libraries Logo" '
                'style="height: 60px; width: auto; margin: 8px auto; display: block;">',
                sanitize=False,
            )
            ui.html(
                '<h1 style="color: #1E3765; font-size: 2.6rem; margin-bottom: 10px; margin-top: 10px;">'
                '<b>Data Curation Tool</b></h1>',
                sanitize=False,
            )

        # Top row options
        with ui.element('div').classes('options-grid'):
            # New Project Option
            with ui.element('div').classes('option-card').on('click', lambda: ui.navigate.to('/new')):
                ui.html('<div class="icon">📁</div>', sanitize=False)
                ui.html('<div class="option-title">New Project</div>', sanitize=False)
                ui.html(
                    '<div class="option-description">Start a new curation process for a new project</div>',
                    sanitize=False,
                )

            # Delete Project Option
            with ui.element('div').classes('option-card').on('click', lambda: ui.navigate.to('/delete')):
                ui.html('<div class="icon">🗑️</div>', sanitize=False)
                ui.html('<div class="option-title">Delete Project</div>', sanitize=False)
                ui.html('<div class="option-description">Delete a project from the database</div>', sanitize=False)

        # Resume Work Option (centered)
        with (
            ui.element('div').classes('resume-container'),
            ui.element('div').classes('option-card resume-card').on('click', lambda: ui.navigate.to('/resume')),
        ):
            ui.html('<div class="icon">✏️</div>', sanitize=False)
            ui.html('<div class="option-title">Resume Project</div>', sanitize=False)
            ui.html('<div class="option-description">Continue working on an existing project</div>', sanitize=False)


# ============================================================================
# New Dataset Setup Page
# ============================================================================


@ui.page('/new')
async def new_dataset_page() -> None:
    """New dataset setup page with exact CSS matching your current design."""
    # Enable the session storage for form persistence
    await ui.context.client.connected()

    # Apply our custom CSS
    apply_pdc_styles()

    with ui.column().classes('pdc-container').style('width: 100%; max-width: 800px;'):
        # Logo
        ui.html(
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">',
            sanitize=False,
        )

        # Header
        ui.label('Data Curation Tool').classes('pdc-header')

        # Messages
        error_msg = ui.label().classes('hidden')
        success_msg = ui.label().classes('hidden')

        # Form state - automatically persisted
        # Initialize with environment variable defaults
        default_form_data = {
            'pid': '',
            'ticket_number': '',
            'collection_alias': '',
            'base_url': os.getenv('BASE_URL', ''),
            'api_token': os.getenv('API_TOKEN', ''),
            'curator_name': os.getenv('CURATOR_NAME', ''),
            'curator_email': os.getenv('CURATOR_EMAIL', ''),
            'main_dir': str(MAIN_DIR.resolve()),
            'force_del': False,
            'check_zip': True,
            'checklist': 'high',
        }

        # Get existing form data or create new
        form_data = app.storage.tab.setdefault('setup_form', default_form_data)

        # Update empty fields with environment variable defaults
        for key, default_value in default_form_data.items():
            if key not in form_data or not form_data.get(key):
                form_data[key] = default_value

        # Dataset Information Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Dataset Information').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Dataset Persistent Identifier (PID) *').classes('pdc-form-label')
                ui.input(placeholder='doi:10.5683/SP2/... or hdl:1902.1/...').classes(
                    'pdc-form-input w-full'
                ).bind_value(form_data, 'pid').style('width: 100%')
                ui.label('Enter the DOI or Handle of the dataset').classes('pdc-form-helper')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Dataverse Base URL *').classes('pdc-form-label')
                ui.input(placeholder='https://demo.borealisdata.ca/').classes('pdc-form-input w-full').bind_value(
                    form_data, 'base_url'
                ).style('width: 100%')
                ui.label('Base URL of the Dataverse installation').classes('pdc-form-helper')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('API Token *').classes('pdc-form-label')
                ui.input(
                    placeholder='Enter your Dataverse API token', password=True, password_toggle_button=True
                ).classes('pdc-form-input w-full').bind_value(form_data, 'api_token').style('width: 100%')
                ui.label('Your Dataverse API token (will be hidden)').classes('pdc-form-helper')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Ticket Number *').classes('pdc-form-label')
                ui.input(placeholder='TICKET-123').classes('pdc-form-input w-full').bind_value(
                    form_data, 'ticket_number'
                ).style('width: 100%')
                ui.label('Ticket number for the curation report').classes('pdc-form-helper')

        # Curator Information Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Curator Information').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Curator Name *').classes('pdc-form-label')
                ui.input(placeholder='Enter your name').classes('pdc-form-input w-full').bind_value(
                    form_data, 'curator_name'
                ).style('width: 100%')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Curator Email *').classes('pdc-form-label')
                ui.input(placeholder='Enter your email').classes('pdc-form-input w-full').bind_value(
                    form_data, 'curator_email'
                ).style('width: 100%')

        # Directory Settings Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Directory Settings').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Main Directory Path').classes('pdc-form-label')
                ui.input(placeholder='workdir').classes('pdc-form-input w-full').bind_value(
                    form_data, 'main_dir'
                ).style('width: 100%')
                ui.label('The main (base) directory for project files').classes('pdc-form-helper')

        # Checklist Selection Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Checklist Selection').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.element('div').classes('pdc-form-group'):
                # Use our custom checklist select with styling
                create_checklist_select(
                    current_value=form_data.get('checklist', 'high'),
                    on_change=lambda e: form_data.update({'checklist': e.value}),
                ).style('width: 100%')
                ui.label('Select the checklist level for this curation task').classes('pdc-form-helper')

        # Processing Options Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%;'):
            ui.label('Processing Options').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.row().classes('gap-4'):
                ui.checkbox('Force delete existing project', value=form_data.get('force_del', False)).bind_value(
                    form_data, 'force_del'
                )

                ui.checkbox('Unzip and check contents of zip files', value=form_data.get('check_zip', True)).bind_value(
                    form_data, 'check_zip'
                )

            with ui.element('div').classes('pdc-form-group'):
                ui.label('Dataverse Collection Alias').classes('pdc-form-label')
                ui.input(placeholder='Enter dataverse collection alias').classes('pdc-form-input w-full').bind_value(
                    form_data, 'collection_alias'
                ).style('width: 100%')

        # Action buttons
        with ui.element('div').classes('pdc-actions'):
            start_button = ui.button(
                'Start Curation Process',
                on_click=lambda: handle_setup_submit(
                    form_data, error_msg, success_msg, loading_spinner, start_button, reset_button, back_button
                ),
            ).classes('pdc-btn pdc-btn-primary')

            reset_button = ui.button(
                'Reset Form', on_click=lambda: reset_form(form_data, default_form_data, reset_button)
            ).classes('pdc-btn pdc-btn-secondary')

            back_button = ui.button('Back', on_click=lambda: handle_back_navigation(back_button), color='red').classes(
                'pdc-btn pdc-btn-secondary'
            )

        # Loading indicator
        with ui.element('div').classes('pdc-loading hidden') as loading_spinner:
            ui.element('div').classes('pdc-loading-spinner')
            ui.label('Running curation process...')


@app.post('/setup')
async def setup(request: SetupRequest) -> JSONResponse:
    """Process the setup form and run pydatacuration CLI command.

    Args:
        request (SetupRequest): Setup form data matching CLI parameters

    Returns:
        JSONResponse: Result of the curation process
    """
    try:
        # Validate required fields
        if not request.pid or not request.pid.strip():
            logger.error(f'Validation failed: PID is missing or empty. Received: "{request.pid}"')
            raise HTTPException(status_code=400, detail='PID is required')
        if not request.ticket_number or not request.ticket_number.strip():
            logger.error(f'Validation failed: Ticket number is missing or empty. Received: "{request.ticket_number}"')
            raise HTTPException(status_code=400, detail='Ticket number is required')
        if not request.curator_name or not request.curator_name.strip():
            logger.error(f'Validation failed: Curator name is missing or empty. Received: "{request.curator_name}"')
            raise HTTPException(status_code=400, detail='Curator name is required')
        if not request.curator_email or not request.curator_email.strip():
            logger.error(f'Validation failed: Curator email is missing or empty. Received: "{request.curator_email}"')
            raise HTTPException(status_code=400, detail='Curator email is required')

        # Create context object
        ctx_obj = CtxObj(main_dir=Path(request.main_dir))

        # Store state variables
        dir_manager = DirectoryManager(request.ticket_number, request.main_dir)
        app.state.work_dir = dir_manager.project_dir
        app.state.base_url = request.base_url

        # Create a minimal mock context with the obj
        # We create a simple object that has the required .obj attribute
        class MockContext:
            def __init__(self, obj: CtxObj) -> None:
                self.obj: CtxObj = obj

        ctx = MockContext(ctx_obj)

        # Run in a thread pool to avoid blocking the event loop
        # This is necessary because run_all uses asyncio.run() internally
        loop = asyncio.get_event_loop()

        def run_curation() -> None:
            """Run the curation in a separate thread."""
            run_all(
                ctx=ctx,
                pid=request.pid,
                base_url=request.base_url or '',
                api_token=request.api_token or '',
                ticket_number=request.ticket_number,
                force_del=request.force_del,
                check_zip=request.check_zip,
                collection_alias=request.collection_alias,
                curator_name=request.curator_name,
                curator_email=request.curator_email,
                open_dir=False,
                checklist=request.checklist,
            )

        # Execute in thread pool to avoid event loop conflicts
        await loop.run_in_executor(None, run_curation)

        url = f'/checklist?ticket_number={request.ticket_number}'
        return JSONResponse(content={'success': True, 'redirect_url': url})

    except Exception as e:
        logger.error(f'Curation failed: {e}', exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


async def handle_setup_submit(
    form_data: dict,
    error_msg: ui.label,
    success_msg: ui.label,
    loading_spinner: ui.element,
    start_button: ui.button,
    reset_button: ui.button,
    back_button: ui.button,
) -> None:
    """Handle form submission."""
    # Validation
    required_fields = ['pid', 'base_url', 'api_token', 'ticket_number', 'curator_name', 'curator_email']
    missing = [f for f in required_fields if not form_data.get(f)]

    if missing:
        error_msg.set_text(f'Missing required fields: {", ".join(missing)}')
        error_msg.classes(remove='hidden', add='pdc-error')
        return

    # Disable all buttons and show loading
    start_button.set_enabled(False)
    reset_button.set_enabled(False)
    back_button.set_enabled(False)
    loading_spinner.classes(remove='hidden')
    error_msg.classes(add='hidden')
    success_msg.classes(add='hidden')

    try:
        # In production, call your FastAPI /setup endpoint
        response = await setup(SetupRequest(**form_data))
        response_data = orjson.loads(response.body)
        ui.notify(f'Setup returned: {response_data}', type='info')

        # Show success
        success_msg.set_text('Curation process completed successfully!')
        success_msg.classes(remove='hidden', add='pdc-success')

        # Redirect using the redirect_url from response
        if response_data.get('redirect_url'):
            ui.navigate.to(response_data['redirect_url'])
        else:
            ui.navigate.to(f'/checklist?ticket_number={form_data["ticket_number"]}')

    except Exception as e:
        error_msg.set_text(f'Error: {str(e)}')
        error_msg.classes(remove='hidden', add='pdc-error')
    finally:
        # Re-enable all buttons and hide loading
        start_button.set_enabled(True)
        reset_button.set_enabled(True)
        back_button.set_enabled(True)
        loading_spinner.classes(add='hidden')


def reset_form(form_data: dict, default_form_data: dict, reset_button: ui.button) -> None:
    """Reset form to defaults."""
    # Disable button during reset
    reset_button.set_enabled(False)
    form_data.update(default_form_data)
    ui.notify('Form reset to defaults', type='info')
    # Re-enable button
    reset_button.set_enabled(True)


def handle_back_navigation(back_button: ui.button) -> None:
    """Handle back button navigation."""
    # Disable button during navigation
    back_button.set_enabled(False)
    ui.navigate.to('/')


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
    with ui.element('div').classes('pdc-form-section').style('width: 100%; margin-bottom: 20px;'):
        ui.label('Filters').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

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
                            ui.html(header, sanitize=False)

                # Table Body
                with ui.element('tbody'):
                    for schema in filtered_schemas:
                        row_classes = 'clickable-row' if mode == 'resume' else ''
                        with ui.element('tr').classes(row_classes):
                            # Ticket Number
                            with ui.element('td'):
                                if mode == 'resume':
                                    ui.html(
                                        f'<a href="/checklist?ticket_number={schema["ticket_number"]}" '
                                        f'style="color: #3498db; text-decoration: none; font-weight: 600;">'
                                        f'📋 {schema["ticket_number"]}</a>',
                                        sanitize=False,
                                    )
                                else:
                                    ui.label(f'📋 {schema["ticket_number"]}').style('font-weight: 600;')

                            # Dataset Metadata
                            with ui.element('td'):
                                ui.html(f'<strong>Title:</strong> {schema.get("dataset_title", "N/A")}', sanitize=False)  # noqa: E501
                                ui.html(f'<strong>PID:</strong> {schema.get("dataset_pid", "N/A")}', sanitize=False)
                                ui.html(
                                    f'<strong>ID (Versioned):</strong> {schema.get("dataset_id", "N/A")}',
                                    sanitize=False,
                                )  # noqa: E501
                                ui.html(
                                    f'<strong>URL:</strong> <a href="{schema.get("dataset_url", "N/A")}" target="_blank">{schema.get("dataset_url", "N/A")}</a>',
                                    sanitize=False,
                                )  # noqa: E501
                            # Curator
                            with ui.element('td'):
                                ui.label(schema.get('curator_name', 'N/A'))

                            # Last Modified
                            with ui.element('td'):
                                ui.label(schema['last_modified']).style('color: #7f8c8d;')

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
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">',
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
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">',
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
        success, message = NiceGUIHelper.delete_project(schema.get('name'), MAIN_DIR)
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


@ui.page('/checklist')
async def checklist_page(ticket_number: str) -> None:
    """Checklist page with exact styling match."""
    apply_pdc_styles()

    # Initialize the duckdb connection for this ticket number
    dir_manager = DirectoryManager(ticket_number, MAIN_DIR, RES_DIR)
    duck_db = DuckDB(schema_name=ticket_number, db_file=dir_manager.db_path)
    helpers = NiceGUIHelper(duck_db, ticket_number)

    # Load metadata from database
    project_metadata = duck_db.read_project_metadata_record()
    checklist_type: str | None = project_metadata.get('checklist_type')

    # Load checklist items
    checklist_items = helpers.get_checklist_items()

    # Load checklist results from database
    check_results = duck_db.read_check_results()

    with ui.column().classes('pdc-container'):
        # Logo
        ui.html(
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">',
            sanitize=False,
        )

        # Header, with dynamic checklist type
        checklist_name = f'{checklist_type.title()}-Level ' if checklist_type else ''
        ui.label(f'{checklist_name}Curation Checklist').classes('pdc-header')

        # Metadata Display using our helper function
        create_info_grid(
            project_metadata,
            [
                ('ticket_number', 'Ticket number'),
                ('curator_name', 'Curator name'),
                ('curator_email', 'Curator email'),
                ('dataset_title', 'Dataset title'),
                ('dataset_pid', 'Dataset persistent identifier'),
                ('dataset_id', 'Dataset ID (versioned)'),
                ('dataset_url', 'Dataset access URL'),
                ('dataset_path', 'Dataset Path'),
            ],
        )

        # # Status Legend  # (commented out for cleaner UI); can be re-enabled for other content if needed
        # with ui.element('div').classes('pdc-status-legend'):
        #     ui.label('Status Explanation').classes('text-xl font-semibold')
        #     with ui.element('div').classes('pdc-status-list'):
        #         for code, meaning in [
        #             ('P', 'Passed'),
        #             ('F', 'Follow-up'),
        #             ('TBD', 'To Be Determined'),
        #             ('NA', 'Not Applicable'),
        #         ]:
        #             with ui.element('div').classes('pdc-status-item'):
        #                 ui.label(f'{code}:').classes('pdc-status-code')
        #                 ui.label(f' {meaning}')

        # Filters Section
        with ui.element('div').classes('pdc-form-section').style('width: 100%; margin-bottom: 20px;'):
            ui.label('Filters').classes('text-lg font-semibold text-gray-700').style('margin-bottom: 12px;')

            with ui.row().classes('gap-4').style('align-items: flex-end;'):
                # Status filter
                with ui.element('div').style('flex: 1; min-width: 200px;'):
                    ui.label('Filter by Status').classes('pdc-form-label')
                    status_filter = (
                        ui.select(
                            options=status_options(),
                            value='',
                            with_input=False,
                        )
                        .classes('pdc-status-select')
                        .style('width: 100%;')
                    )

                # Priority filter
                with ui.element('div').style('flex: 1; min-width: 200px;'):
                    ui.label('Filter by Priority').classes('pdc-form-label')
                    priority_filter = (
                        ui.select(
                            options=priority_options(),
                            value='',
                            with_input=False,
                        )
                        .classes('pdc-status-select')
                        .style('width: 100%;')
                    )

                # Clear filters button
                ui.button('Clear Filters', on_click=lambda: clear_filters(status_filter, priority_filter)).classes(
                    'pdc-btn pdc-btn-secondary'
                )

        # Table container that will be refreshed when filters change
        table_container = ui.column().style('width: 100%;')

        # Define clear filters function
        async def clear_filters(status_sel: ui.select, priority_sel: ui.select) -> None:
            status_sel.value = ''
            priority_sel.value = ''
            # Explicitly trigger a refresh after clearing
            await render_filtered_table()

        # Define render function that applies filters
        async def render_filtered_table() -> None:
            # Reload checklist items from database to get latest changes
            fresh_items = helpers.get_checklist_items()

            table_container.clear()
            with table_container:
                await render_checklist_table(
                    duck_db,
                    fresh_items,
                    check_results,
                    ticket_number,
                    status_filter=status_filter.value,
                    priority_filter=priority_filter.value,
                    refresh_callback=render_filtered_table,
                )

        # Connect filters to table refresh
        status_filter.on('update:model-value', render_filtered_table)
        priority_filter.on('update:model-value', render_filtered_table)

        # Initial render
        await render_filtered_table()

        # Action Buttons
        with ui.element('div').classes('pdc-actions'):
            ui.button(
                'Save Curation Log (Word)', on_click=lambda: NiceGUIHelper.export_word_button(duck_db, dir_manager)
            ).classes('pdc-btn pdc-btn-primary')

            ui.button('Calculate Time Spent', on_click=lambda: helpers.calculate_total_time(checklist_items)).classes(
                'pdc-btn pdc-btn-calculate'
            )

            ui.button('Export YAML', on_click=lambda: NiceGUIHelper.export_yaml_button(duck_db, dir_manager)).classes(
                'pdc-btn pdc-btn-secondary'
            )

            ui.button('New Dataset', on_click=helpers.confirm_new_dataset).classes('pdc-btn pdc-btn-danger')


async def render_checklist_table(  # noqa: PLR0913
    duckdb_instance: DuckDB,
    checklist_items: list,
    check_results: dict[str, str],
    ticket_number: str,
    status_filter: str = '',
    priority_filter: str = '',
    refresh_callback: None = None,
) -> None:
    """Render checklist table with exact styling.

    Args:
        duckdb_instance: DuckDB instance
        checklist_items: List of checklist items
        check_results: Dictionary of check results
        ticket_number: Ticket number
        status_filter: Filter by status (empty string means no filter)
        priority_filter: Filter by priority (empty string means no filter)
        refresh_callback: Optional callback function to refresh the UI after updates
    """
    # Internal helper functions for creating UI components
    helpers = NiceGUIHelper(duckdb_instance, ticket_number, refresh_callback)

    # Apply filters to checklist items
    filtered_items = checklist_items
    if status_filter:
        filtered_items = [item for item in filtered_items if item.status == status_filter]
    if priority_filter:
        filtered_items = [item for item in filtered_items if item.priority.lower() == priority_filter.lower()]

    with ui.element('table').classes('pdc-checklist-table'):
        # Table Header
        with ui.element('thead'), ui.element('tr'):
            for header in [
                'ID',
                'Action Item',
                'Information Location',
                'Status',
                "Curator's Comments",
                'Priority',
                'Time Spent',
            ]:
                with ui.element('th'):
                    ui.html(header, sanitize=False)

        # Table Body
        with ui.element('tbody'):
            current_section = None
            for item in filtered_items:
                # Section header row
                if item.section != current_section:
                    current_section = item.section
                    with ui.element('tr'), ui.element('td').props('colspan=7').classes('pdc-section-header'):
                        ui.html(item.section, sanitize=False)

                # Item row
                with ui.element('tr').props(f'data-item-id="{item.id}"'):
                    # ID
                    with ui.element('td').classes('pdc-item-id'):
                        ui.html(item.id, sanitize=False)

                    # Action & Instructions
                    with ui.element('td').classes('details-cell'):
                        with ui.element('div').classes('pdc-action-item'):
                            ui.html(item.action, sanitize=False)
                        if item.instructions:
                            with ui.element('div').classes('pdc-instructions-header'):
                                ui.html('Guidance:', sanitize=False)
                            ui.markdown(item.instructions).classes('pdc-instructions')

                    # Information Location
                    with (
                        ui.element('td').classes('information-location-column'),
                        ui.element('div').classes('pdc-info-location-container'),
                    ):  # noqa: E501
                        if item.information_location:
                            ui.markdown(item.information_location).classes('pdc-static-info-location')
                        if item.automated_check_ids:
                            for ac_id in item.automated_check_ids:
                                result: dict | None = duckdb_instance.sql_read_row(
                                    DuckDBmodels(ticket_number).check_results(),
                                    'check_id',
                                    ac_id,
                                )
                                # Render the 'results' item, if it exists
                                if result and result.get('results') and len(result['results']) > 0:
                                    # Use the scrollable container class from nicegui_styles.py
                                    # Only render the grey scrollable box if there are results
                                    with ui.element('div').classes('pdc-dynamic-check-results'):
                                        render_check_results(result['results'], result['unit'], ac_id)

                    # Status
                    with ui.element('td'):
                        create_status_select(
                            item.id,
                            item.status or '',
                            on_change=lambda e, iid=item.id: helpers.handle_status_change(iid, e.value),
                        )

                    # Comments
                    with ui.element('td'):
                        ui.textarea(value=item.comments or '', placeholder="Curator's comments...").classes(
                            'pdc-comments-input'
                        ).on(
                            'change',
                            lambda e, iid=item.id: helpers.handle_comments_change(iid, e.sender.value),
                        )

                    # Priority
                    with ui.element('td'), ui.element('div').classes('pdc-priority-badge-container'):
                        create_priority_badge(item.priority)

                    # Time Spent with Timer
                    with (
                        ui.element('td'),
                        ui.row().classes('gap-1').style('align-items: center;'),
                    ):
                        time_input = (
                            ui.input(value=item.time_spent or '', placeholder='MM:SS')
                            .classes('pdc-time-input')
                            .on('change', lambda e, iid=item.id: helpers.handle_time_change(iid, e.sender.value))
                            .props('maxlength=5')
                            .style('flex: 1; min-width: 60px;')
                        )

                        # Single toggle timer button
                        # Create a closure-safe callback
                        def create_timer_callback(item_id: str, time_inp: ui.input) -> ui.button:
                            timer_btn = (
                                ui.button(icon='play_arrow')
                                .props('flat dense round size=sm color=positive')
                                .tooltip('Start/Stop Timer')
                            )
                            timer_btn.on('click', lambda: helpers.toggle_timer(item_id, time_inp, timer_btn))
                            return timer_btn

                        create_timer_callback(item.id, time_input)


def render_check_results(results, result_name: str, check_id: str) -> None:
    """Render check results based on their type (list, dict, or other).

    Args:
        results (Any): The results data to render (can be list, dict, or other types).
        result_name (str): The name of the result to display as a sub-label.
        check_id (str): The check identifier to display as a label.

    """
    # Use the pdc-check-result class from nicegui_styles.py instead of inline styles
    with ui.element('div').classes('pdc-check-result'):
        # Header with check ID - using pdc-static-info-location class
        ui.label(f'{check_id}').classes('pdc-check-result-header')

        if isinstance(results, list):
            # Show count description
            ui.label(f'{len(results)} {result_name} found').classes('pdc-check-description')

            # Use pdc-check-details-list class for the numbered list
            with ui.element('ol').classes('pdc-check-details-list'):
                for item in results:
                    with ui.element('li').classes('result-item'):
                        if isinstance(item, dict):
                            # If list contains dicts, render key-value pairs
                            ui.html(
                                '<br>'.join([f'<strong>{k}:</strong> {v}' for k, v in item.items()]),
                                sanitize=False,
                            )
                        else:
                            ui.label(str(item))

        elif isinstance(results, dict):
            # Show count description
            ui.label(f'{len(results)} {result_name} found').classes('pdc-check-description')

            # Use pdc-check-details-list class for the numbered list
            with ui.element('ol').classes('pdc-check-details-list'):
                for key, value in results.items():
                    with ui.element('li').classes('result-item'):
                        ui.html(f'<strong>{key}:</strong> {value}', sanitize=False)

        else:
            # Render as plain text for other types
            ui.label(str(results)).classes('pdc-check-description')


# ============================================================================
# Health Check Endpoint
# ============================================================================


@ui.page('/health')
def health_check() -> dict:
    """Health check endpoint."""
    return {'status': 'ok'}


# ============================================================================
# Static Files Setup - Must be BEFORE ui.run()
# ============================================================================

# Mount static files from your existing frontend directory
# Determine the correct path to static files
static_path = Path('pydatacuration/frontend')
if not static_path.exists():
    static_path = Path(__file__).parent / 'pydatacuration' / 'frontend'

if static_path.exists():
    # Add static files route
    nicegui_app.add_static_files('/static', str(static_path))
    logger.info('✓ Static files mounted:', static_path.absolute())
else:
    logger.warning('⚠ WARNING: Static directory not found!')
    logger.warning('Looked for:', static_path.absolute())


# ============================================================================
# Run the application
# ============================================================================

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title='PyDataCuration - Styled POC', favicon='🔬', port=8080, storage_secret=str(os.urandom(16)))
