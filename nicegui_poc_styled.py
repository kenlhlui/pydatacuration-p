"""NiceGUI Proof of Concept - With Production-Ready Styling.

This version uses the nicegui_styles module for exact CSS matching.
"""

# ruff: noqa: PLR1702
import asyncio
import os
import re
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import JSONResponse
import markdown2
import orjson
import yaml
from dotenv import load_dotenv
from nicegui import app
from nicegui import app as nicegui_app
from nicegui import ui
from pydantic import BaseModel, ValidationError

# Import our custom styling
from nicegui_styles import apply_pdc_styles
from nicegui_styles import create_checklist_select
from nicegui_styles import create_info_grid
from nicegui_styles import create_priority_badge
from nicegui_styles import create_status_select
from pydatacuration.custom_logging import logger
from pydatacuration.custom_logging import setup_logging

# Import pydatacuration modules
from pydatacuration.directory_manager import DirectoryManager
from pydatacuration.duck_db import DuckDB


# Load environment variables
load_dotenv(override=True)
MAIN_DIR: Path = Path(os.getenv('MAIN_DIR', 'workdir'))

# Setup logging with your custom style
setup_logging(log_file_dir=MAIN_DIR / 'logs', log_level='DEBUG')


# ============================================================================
# Data Models
# ============================================================================


class SetupRequest(BaseModel):
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


class ChecklistItem(BaseModel):
    """Checklist item model.

    Args:
    id (str): item identifier
    action (str): description of the action
    instructions (str): detailed instructions
    priority (str): priority level
    section (str): section this item belongs to (optional)
    automated_check_ids (list[str]): list of automated check IDs that map to this item
    information_location (str): location where information can be found
    check_type (str): type of check (manual/automated)
    status (str): current status of the item
    comments (str): curator comments
    time_spent (str): time spent on this item
    """

    id: str
    action: str
    instructions: str
    priority: str
    section: str = ''
    automated_check_ids: list[str] | None = []
    information_location: str = ''
    check_type: str = ''
    status: str | None = None
    comments: str | None = None
    time_spent: str | None = None


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
                'style="height: 60px; width: auto; margin: 8px auto; display: block;">', sanitize=False
            )
            ui.html(
                '<h1 style="color: #1E3765; font-size: 2.6rem; margin-bottom: 10px; margin-top: 10px;">'
                '<b>Data Curation Tool</b></h1>', sanitize=False
            )

        # Top row options
        with ui.element('div').classes('options-grid'):
            # New Project Option
            with ui.element('div').classes('option-card').on('click', lambda: ui.navigate.to('/new-dataset')):
                ui.html('<div class="icon">📁</div>', sanitize=False)
                ui.html('<div class="option-title">New Project</div>', sanitize=False)
                ui.html('<div class="option-description">Start a new curation process for a new project</div>', sanitize=False)

            # Delete Project Option
            with ui.element('div').classes('option-card').on('click', lambda: ui.navigate.to('/delete-project')):
                ui.html('<div class="icon">🗑️</div>', sanitize=False)
                ui.html('<div class="option-title">Delete Project</div>', sanitize=False)
                ui.html('<div class="option-description">Delete a project from the database</div>', sanitize=False)

        # Resume Work Option (centered)
        with (
            ui.element('div').classes('resume-container'),
            ui.element('div').classes('option-card resume-card').on('click', lambda: ui.navigate.to('/resume-work')),
        ):
            ui.html('<div class="icon">✏️</div>', sanitize=False)
            ui.html('<div class="option-title">Resume Work</div>', sanitize=False)
            ui.html('<div class="option-description">Continue working on an existing project</div>', sanitize=False)


# ============================================================================
# New Dataset Setup Page
# ============================================================================


@ui.page('/new-dataset')
async def new_dataset_page() -> None:
    """New dataset setup page with exact CSS matching your current design."""
    # Apply our custom CSS
    apply_pdc_styles()

    with ui.column().classes('pdc-container').style('width: 100%; max-width: 800px;'):
        # Logo
        ui.html(
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">', sanitize=False
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
        form_data = app.storage.user.setdefault('setup_form', {})

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
            ui.button(
                'Start Curation Process',
                on_click=lambda: handle_setup_submit(form_data, error_msg, success_msg, loading_spinner),
            ).classes('pdc-btn pdc-btn-primary')

            ui.button('Reset Form', on_click=lambda: reset_form(form_data, default_form_data)).classes('pdc-btn pdc-btn-secondary')

            ui.button('Back', on_click=lambda: ui.navigate.to('/'), color='red').classes('pdc-btn pdc-btn-secondary')

        # Loading indicator
        with ui.element('div').classes('pdc-loading hidden') as loading_spinner:
            ui.element('div').classes('pdc-loading-spinner')
            ui.label('Running curation process...')

async def run_command(command: str) -> dict:
    """Run a command and return the result with real-time output streaming to logger.

    Args:
        command (str): Command to run

    Returns:
        dict: Command result with stdout, stderr, and return code
    """
    try:
        logger.info('🚀 Starting the CLI application')

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_lines = []
        stderr_lines = []

        def strip_ansi_codes(text: str) -> str:
            """Remove ANSI escape codes from text."""
            ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
            return ansi_escape.sub('', text)

        async def read_stream(stream, lines_list, log_func):
            """Read stream line by line and log in real-time."""
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded_line = line.decode().rstrip()
                if decoded_line:  # Only log non-empty lines
                    lines_list.append(decoded_line)
                    # Strip ANSI codes before logging to prevent double formatting
                    clean_line = strip_ansi_codes(decoded_line)
                    if clean_line.strip():  # Only log if there's content after stripping
                        log_func(f'[CLI] {clean_line}')

        # Create tasks to read both streams concurrently
        stdout_task = asyncio.create_task(read_stream(process.stdout, stdout_lines, logger.info))
        stderr_task = asyncio.create_task(read_stream(process.stderr, stderr_lines, logger.error))

        # Wait for both streams to complete
        await asyncio.gather(stdout_task, stderr_task)

        # Wait for process to finish
        return_code = await process.wait()

        result = {
            'stdout': '\n'.join(stdout_lines),
            'stderr': '\n'.join(stderr_lines),
            'return_code': return_code,
            'success': return_code == 0,
        }

        logger.info(f'✅ Command completed with return code: {return_code}')
        return result

    except Exception as e:
        error_msg = f'❌ Command execution failed: {str(e)}'
        logger.error(error_msg)
        return {'stdout': '', 'stderr': error_msg, 'return_code': -1, 'success': False}

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

        # Build the command to run pydatacuration CLI
        cmd_parts = [
            'python',
            '-m',
            'pydatacuration.main',
            'all',
            '--pid',
            f'"{request.pid}"',
            '--ticket-number',
            f'"{request.ticket_number}"',
            '--curator-name',
            f'"{request.curator_name}"',
            '--curator-email',
            f'"{request.curator_email}"',
        ]

        # Add base URL if provided
        if request.base_url and request.base_url.strip():
            cmd_parts.extend(['--base-url', f'"{request.base_url}"'])

        # Add API token if provided
        if request.api_token and request.api_token.strip():
            cmd_parts.extend(['--api-token', f'"{request.api_token}"'])

        # Add optional flags
        if request.force_del:
            cmd_parts.append('--force-del')
        else:
            cmd_parts.append('--no-force-del')

        if request.check_zip:
            cmd_parts.append('-z')
        else:
            cmd_parts.append('-nz')

        # Add checklist type
        if request.checklist:
            cmd_parts.extend(['--checklist', request.checklist])

        # Join command parts
        cmd = ' '.join(cmd_parts)

        # Store state variables using DirectoryManager
        dir_manager = DirectoryManager(request.ticket_number, request.main_dir)
        app.state.work_dir = dir_manager.project_dir
        app.state.base_url = request.base_url
        # Run the command
        result = await run_command(cmd)

        if result['success']:
            url = f'/checklist?ticket_number={request.ticket_number}'
            return JSONResponse(content={'success': True, 'redirect_url': url})
        # Extract the last meaningful error message from CLI output
        error_details = []
        if result['stderr']:
            error_details.append(f'CLI Error: {result["stderr"].strip()}')
        if result['stdout']:
            # Look for error patterns in stdout (CLI logs errors there too)
            stdout_lines = result['stdout'].strip().split('\n')
            for line in reversed(stdout_lines):
                clean_line = line.strip()
                if 'error' in clean_line.lower() or 'aborting' in clean_line.lower() or 'failed' in clean_line.lower():
                    error_details.append(f'CLI Message: {clean_line}')
                    break

        error_message = '. '.join(error_details) if error_details else 'Curation command failed'
        logger.error(f'Command failed with return code {result["return_code"]}: {error_message}')
        raise HTTPException(status_code=400, detail=error_message)
    except ValidationError as e:
        logger.error(f'Pydantic validation error: {e}')
        logger.error(f'Validation errors details: {e.errors()}')
    except HTTPException as e:
        logger.error(f'HTTP exception: status={e.status_code}, detail={e.detail}')
        raise e
    except Exception as e:
        logger.error(f'Unexpected error in setup endpoint: {e}', exc_info=True)
    return JSONResponse(content={'success': False, 'message': 'Unexpected error occurred'})


async def handle_setup_submit(form_data: dict, error_msg, success_msg, loading_spinner) -> None:
    """Handle form submission."""
    # Validation
    required_fields = ['pid', 'base_url', 'api_token', 'ticket_number', 'curator_name', 'curator_email']
    missing = [f for f in required_fields if not form_data.get(f)]

    if missing:
        error_msg.set_text(f'Missing required fields: {", ".join(missing)}')
        error_msg.classes(remove='hidden', add='pdc-error')
        return

    # Show loading
    loading_spinner.classes(remove='hidden')
    error_msg.classes(add='hidden')
    success_msg.classes(add='hidden')

    try:
        # In production, call your FastAPI /setup endpoint
        response = await setup(SetupRequest(**form_data))
        response_data = orjson.loads(response.body)
        ui.notify(f'Setup returned: {response_data}', type='info')

        # Store metadata (replaces sessionStorage)
        app.storage.user['ds_metadata'] = {
            'dataset_pid': form_data['pid'],
            'curator_name': form_data['curator_name'],
            'curator_email': form_data['curator_email'],
            'ticket_number': form_data['ticket_number'],
        }

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
        loading_spinner.classes(add='hidden')


def reset_form(form_data: dict, default_form_data: dict) -> None:
    """Reset form to defaults."""
    form_data.update(default_form_data)
    ui.notify('Form reset to defaults', type='info')

# ============================================================================
# Resume Work Page
# ============================================================================


@ui.page('/resume-work')
async def resume_work_page() -> None:
    """Resume work page - shows list of existing projects."""
    apply_pdc_styles()

    # Add custom CSS for project list
    ui.add_head_html("""
    <style>
        .project-list-container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        .project-card {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .project-card:hover {
            border-color: #3498db;
            box-shadow: 0 4px 12px rgba(52, 152, 219, 0.15);
            transform: translateY(-2px);
        }
        .project-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .project-ticket {
            font-size: 1.2rem;
            font-weight: 600;
            color: #2c3e50;
        }
        .project-date {
            color: #7f8c8d;
            font-size: 0.9rem;
        }
        .project-info {
            color: #34495e;
            margin: 5px 0;
        }
        .project-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            margin-right: 8px;
        }
        .badge-high {
            background-color: #e74c3c;
            color: white;
        }
        .badge-medium {
            background-color: #f39c12;
            color: white;
        }
        .no-projects {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
        }
    </style>
    """)

    with ui.column().classes('project-list-container'):
        # Logo and Header
        ui.html(
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">', sanitize=False
        )
        ui.label('Resume Work - Select a Project').classes('pdc-header')

        # Back button
        ui.button('← Back to Main Menu', on_click=lambda: ui.navigate.to('/')).classes('pdc-btn pdc-btn-secondary')

        ui.separator()

        # Get all schemas/projects
        schemas = get_all_schemas()

        if not schemas:
            with ui.element('div').classes('no-projects'):
                ui.label('No existing projects found').classes('text-xl')
                ui.label('Start a new project from the main menu').classes('text-sm')
        else:
            ui.label(f'Found {len(schemas)} project(s)').classes('text-lg font-semibold').style('margin: 20px 0;')

            # Display project cards
            for schema in schemas:
                with (
                    ui.element('div')
                    .classes('project-card')
                    .on('click', lambda s=schema: ui.navigate.to(f'/checklist?ticket_number={s["display_name"]}'))
                ):
                    with ui.element('div').classes('project-header'):
                        ui.html(f'<span class="project-ticket">📋 {schema["display_name"]}</span>', sanitize=False)
                        ui.html(f'<span class="project-date">{schema["last_modified"]}</span>', sanitize=False)

                    # Checklist type badge
                    badge_class = 'badge-high' if schema.get('checklist_type') == 'high' else 'badge-medium'
                    ui.html(
                        f'<span class="project-badge {badge_class}">'
                        f'{schema.get("checklist_type", "unknown").upper()}-LEVEL</span>', sanitize=False
                    )

                    # Project info
                    if schema.get('curator_name'):
                        ui.html(f'<div class="project-info">👤 Curator: {schema["curator_name"]}</div>', sanitize=False)
                    if schema.get('dataset_title') and schema['dataset_title'] != 'N/A':
                        ui.html(f'<div class="project-info">📄 Dataset: {schema["dataset_title"]}</div>', sanitize=False)


# ============================================================================
# Delete Project Page
# ============================================================================


@ui.page('/delete-project')
async def delete_project_page() -> None:
    """Delete project page - shows list of projects with delete buttons."""
    apply_pdc_styles()

    # Add custom CSS for delete page
    ui.add_head_html("""
    <style>
        .delete-list-container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        .delete-card {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .delete-card-info {
            flex-grow: 1;
        }
        .warning-banner {
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
    </style>
    """)

    # Container to hold the project list (for refreshing after delete)
    container = ui.column().classes('delete-list-container')

    with container:
        # Logo and Header
        ui.html(
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">', sanitize=False
        )
        ui.label('Delete Project').classes('pdc-header')

        # Back button
        ui.button('← Back to Main Menu', on_click=lambda: ui.navigate.to('/')).classes('pdc-btn pdc-btn-secondary')

        # Warning banner
        with ui.element('div').classes('warning-banner'):
            ui.label('⚠️ Warning: Deleting a project is permanent and cannot be undone!').classes(
                'text-lg font-semibold'
            )

        ui.separator()

        # Project list container (for dynamic updates)
        project_list_container = ui.column()

    async def refresh_project_list():
        """Refresh the project list."""
        project_list_container.clear()
        with project_list_container:
            schemas = get_all_schemas()

            if not schemas:
                with ui.element('div').classes('no-projects'):
                    ui.label('No projects found').classes('text-xl')
            else:
                ui.label(f'Found {len(schemas)} project(s)').classes('text-lg font-semibold').style('margin: 20px 0;')

                for schema in schemas:
                    with ui.element('div').classes('delete-card'):
                        with ui.element('div').classes('delete-card-info'):
                            ui.html(f'<span class="project-ticket">📋 {schema["display_name"]}</span>', sanitize=False)
                            ui.html(f'<span class="project-date">Last modified: {schema["last_modified"]}</span>', sanitize=False)

                            if schema.get('curator_name'):
                                ui.html(f'<div class="project-info">👤 Curator: {schema["curator_name"]}</div>', sanitize=False)

                        # Delete button
                        ui.button(
                            '🗑️ Delete', on_click=lambda s=schema: confirm_delete_project(s, refresh_project_list)
                        ).classes('pdc-btn pdc-btn-danger').style('margin-left: 15px;')

    # Initial load
    await refresh_project_list()


def confirm_delete_project(schema: dict, refresh_callback) -> None:
    """Show confirmation dialog before deleting a project."""

    async def handle_delete():
        success, message = delete_schema(schema['name'])
        if success:
            ui.notify(message, type='positive')
            await refresh_callback()
            dialog.close()
        else:
            ui.notify(message, type='negative')
            dialog.close()

    with ui.dialog() as dialog, ui.card().style('min-width: 400px;'):
        ui.label(f'Delete project "{schema["display_name"]}"?').classes('text-xl font-semibold')
        ui.label('This action cannot be undone. All data will be permanently deleted.').classes('text-red-600')

        with ui.row().classes('w-full justify-end gap-2').style('margin-top: 20px;'):
            ui.button('Cancel', on_click=dialog.close).classes('pdc-btn pdc-btn-secondary')
            ui.button('Delete', on_click=handle_delete).classes('pdc-btn pdc-btn-danger')

    dialog.open()


# ============================================================================
# Checklist Page
# ============================================================================


@ui.page('/checklist')
async def checklist_page(ticket_number: str | None = None) -> None:
    """Checklist page with exact styling match."""
    apply_pdc_styles()

    # Get metadata from storage
    metadata = app.storage.user.get('ds_metadata', {})
    checklist_type = app.storage.user.get('setup_form', {}).get('checklist', 'high')

    # Load checklist data
    checklist_items = await load_checklist_from_duckdb(ticket_number)

    with ui.column().classes('pdc-container'):
        # Logo
        ui.html(
            '<img src="/static/UTL.png" '
            'alt="University of Toronto Libraries Logo" '
            'class="pdc-logo" '
            'style="height: 60px; width: auto; margin: 8px;">', sanitize=False
        )

        # Header
        ui.label(f'{checklist_type.title()}-Level Curation Checklist').classes('pdc-header')

        # Metadata Display using our helper function
        create_info_grid(
            metadata,
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

        # Status Legend
        with ui.element('div').classes('pdc-status-legend'):
            ui.label('Status Explanation').classes('text-xl font-semibold')
            with ui.element('div').classes('pdc-status-list'):
                for code, meaning in [
                    ('P', 'Passed'),
                    ('F', 'Follow-up'),
                    ('TBD', 'To Be Determined'),
                    ('NA', 'Not Applicable'),
                ]:
                    with ui.element('div').classes('pdc-status-item'):
                        ui.label(f'{code}:').classes('pdc-status-code')
                        ui.label(f' {meaning}')

        # Checklist Table
        await render_checklist_table(checklist_items, ticket_number)

        # Action Buttons
        with ui.element('div').classes('pdc-actions'):
            ui.button('Save Curation Log (Word)', on_click=lambda: save_curation_report(checklist_items)).classes(
                'pdc-btn pdc-btn-primary'
            )

            ui.button('Calculate Time Spent', on_click=lambda: calculate_total_time(checklist_items)).classes(
                'pdc-btn pdc-btn-calculate'
            )

            ui.button('Export YAML', on_click=lambda: export_yaml(checklist_items)).classes('pdc-btn pdc-btn-secondary')

            ui.button('New Dataset', on_click=confirm_new_dataset).classes('pdc-btn pdc-btn-danger')


async def render_checklist_table(items: list[ChecklistItem], ticket_number: str) -> None:  # noqa: PLR1702
    """Render checklist table with exact styling."""
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

            for item in items:
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
                            ui.html(item.instructions, sanitize=False).classes('pdc-instructions')

                    # Information Location
                    with (
                        ui.element('td').classes('information-location-column'),
                        ui.element('div').classes('pdc-info-location-container'),
                    ):  # noqa: E501
                        if item.information_location:
                            ui.html(item.information_location, sanitize=False).classes('pdc-static-info-location')

                    # Status
                    with ui.element('td'):
                        create_status_select(
                            item.id,
                            item.status or '',
                            on_change=lambda e, iid=item.id: handle_status_change(iid, e.value, ticket_number),
                        )

                    # Comments
                    with ui.element('td'):
                        ui.textarea(value=item.comments or '', placeholder="Curator's comments...").classes(
                            'pdc-comments-input'
                        ).on(
                            'change', lambda e, iid=item.id: handle_comments_change(iid, e.sender.value, ticket_number)
                        )

                    # Priority
                    with ui.element('td'), ui.element('div').classes('pdc-priority-badge-container'):
                        create_priority_badge(item.priority)

                    # Time Spent
                    with ui.element('td'):
                        ui.input(value=item.time_spent or '', placeholder='MM:SS').classes('pdc-time-input').on(
                            'change', lambda e, iid=item.id: handle_time_change(iid, e.sender.value, ticket_number)
                        ).props('maxlength=5')


# ============================================================================
# Database Helper Functions (from app.py)
# ============================================================================


def get_all_schemas() -> list[dict]:
    """Get all available schemas (projects) from DuckDB.

    Returns:
        list[dict]: List of schemas with metadata
    """
    try:
        db_dir = Path(MAIN_DIR) / 'db'
        db_file = db_dir / 'duckdb.db'

        if not db_file.exists():
            return []

        # Create a DuckDB instance to get schemas
        duck_db = DuckDB(schema_name='temp', db_file=db_file)
        schema_names = duck_db.get_all_schema_names()

        # Get additional metadata for each schema
        schemas_with_metadata = []
        for schema_name in schema_names:
            try:
                # Try to get project metadata for last modified date
                schema_duck_db = DuckDB(schema_name=schema_name, db_file=db_file)
                metadata = schema_duck_db.read_project_metadata_record()

                last_modified = 'Unknown'
                if metadata and 'log_last_update_date' in metadata:
                    last_modified = metadata['log_last_update_date']
                elif metadata and 'log_init_date' in metadata:
                    last_modified = metadata['log_init_date']

                # Prune the schema, removing the prefixes
                schema_name_display = schema_name.replace('duckdb.', '').replace('"', '')

                schemas_with_metadata.append(
                    {
                        'display_name': schema_name_display,
                        'name': schema_name,
                        'last_modified': last_modified,
                        'checklist_type': metadata.get('checklist_type', 'unknown'),
                        'has_metadata': bool(metadata and metadata.get('dataset_pid')),
                        'curator_name': metadata.get('curator_name', ''),
                        'dataset_title': metadata.get('dataset_title', 'N/A'),
                    }
                )
            except Exception as e:
                print(f'Could not get metadata for schema {schema_name}: {e}')
                schema_name_display = schema_name.replace('duckdb.', '').replace('"', '')
                schemas_with_metadata.append(
                    {
                        'display_name': schema_name_display,
                        'name': schema_name,
                        'last_modified': 'Unknown',
                        'has_metadata': False,
                    }
                )

        # Sort by last modified (most recent first)
        schemas_with_metadata.sort(key=lambda x: x['last_modified'], reverse=True)

        return schemas_with_metadata

    except Exception as e:
        print(f'Error fetching schemas: {e}')
        return []


def delete_schema(schema_name: str) -> tuple[bool, str]:
    """Delete a specific schema from DuckDB.

    Args:
        schema_name (str): Name of the schema to delete

    Returns:
        tuple[bool, str]: Success status and message
    """
    try:
        db_dir = Path(MAIN_DIR) / 'db'
        db_file = db_dir / 'duckdb.db'

        if not db_file.exists():
            return False, 'Database file not found'

        # Create a DuckDB instance to delete the schema
        duck_db = DuckDB(schema_name='temp', db_file=db_file)

        # Prune the schema name
        schema_name_pruned = schema_name.replace('duckdb.', '').replace('"', '')

        # Delete the schema
        duck_db.sql_drop_schema(schema_name_pruned)

        return True, f'Schema {schema_name_pruned} deleted successfully'

    except Exception as e:
        return False, f'Error deleting schema: {str(e)}'


def get_checklist_from_duckdb(ticket_number: str) -> dict:
    """Get the checklist from DuckDB for a specific ticket.

    Args:
        ticket_number (str): Ticket number

    Returns:
        dict: Checklist data
    """
    try:
        dir_manager = DirectoryManager(ticket_number, MAIN_DIR)
        duck_db = DuckDB(schema_name=ticket_number, db_file=dir_manager.db_path)
        return duck_db.read_checklist()
    except Exception as e:
        print(f'Error fetching checklist from DuckDB for ticket {ticket_number}: {e}')
        return {'error': str(e)}


# ============================================================================
# Helper Functions
# ============================================================================

def get_checklist_items(ticket_number: str) -> list[ChecklistItem]:
    """Get all checklist items from the DuckDB database for the specified ticket.

    The checklist type is determined by what was stored in the database during setup.

    Args:
        ticket_number (str): Ticket number to get checklist items for.

    Returns:
        list[ChecklistItem]: List of checklist items with their details.

    """
    dir_manager = DirectoryManager(ticket_number, MAIN_DIR)
    duck_db = DuckDB(schema_name=ticket_number, db_file=dir_manager.db_path)
    duck_db_data = duck_db.read_checklist()
    items = []
    for item in duck_db_data.get('checklist', []):
        checklist_item = ChecklistItem(
            id=item['id'],
            action=item['action'],
            instructions=markdown2.markdown(item['instructions']) if item['instructions'] else '',
            priority=item['priority'],
            section=item.get('section', ''),
            automated_check_ids=item.get('automated_check_ids', []),
            information_location=markdown2.markdown(  # Convert Markdown to HTML
                item.get('information_location', '')
            )
            if item.get('information_location')
            else '',  # Handle missing information_location
            check_type=item.get('check_type', 'Manual'),  # Optional field for check type
        )
        items.append(checklist_item)
    return items


async def load_checklist_from_duckdb(ticket_number: str) -> list[ChecklistItem]:
    """Load checklist data from DuckDB."""
    # Sample data for POC
    return [
        ChecklistItem(
            id='ABC-001',
            action='Check metadata completeness',
            instructions='Review all required fields for completeness and accuracy.',
            priority='required',
            section='Metadata Review',
            status='P',
            comments='All fields are complete',
            time_spent='05:30',
            information_location='<p>Check the <strong>Metadata</strong> tab in Dataverse</p>',
        ),
        ChecklistItem(
            id='ABC-002',
            action='Verify file formats',
            instructions='Ensure all files are in supported and appropriate formats.',
            priority='recommended',
            section='File Review',
            status='TBD',
            comments='',
            time_spent='02:15',
            information_location='<p>See <em>Files</em> section for list of formats</p>',
        ),
        ChecklistItem(
            id='ABC-003',
            action='Check documentation completeness',
            instructions='Verify README and codebook are present and complete.',
            priority='required',
            section='Documentation',
            status='F',
            comments='Missing codebook for variable X',
            time_spent='10:45',
            information_location='',
        ),
    ]


async def handle_status_change(item_id: str, new_status: str, ticket_number: str) -> None:
    """Handle status change with auto-save."""
    await save_to_duckdb(ticket_number, item_id, {'status': new_status})
    ui.notify(f'Status updated for {item_id}', type='positive', position='top-right', close_button=True)


async def handle_comments_change(item_id: str, new_comments: str, ticket_number: str) -> None:
    """Handle comments change."""
    await save_to_duckdb(ticket_number, item_id, {'comments': new_comments})


async def handle_time_change(item_id: str, new_time: str, ticket_number: str) -> None:
    """Handle time change with validation."""
    if validate_time_format(new_time):
        await save_to_duckdb(ticket_number, item_id, {'time_spent': new_time})
    else:
        ui.notify('Please enter time in MM:SS format', type='negative')


def validate_time_format(time_str: str) -> bool:
    """Validate MM:SS format."""
    return bool(re.match(r'^[0-9]{1,2}:[0-5][0-9]$', time_str)) if time_str else True


async def save_to_duckdb(ticket_number: str, item_id: str, data: dict) -> None:
    """Save item to DuckDB."""
    # In production, call your /update-checklist-item endpoint
    print(f'Saving to DuckDB: ticket={ticket_number}, item={item_id}, data={data}')


def calculate_total_time(items: list[ChecklistItem]) -> None:
    """Calculate total time spent."""
    total_minutes = 0
    for item in items:
        if item.time_spent:
            try:
                parts = item.time_spent.split(':')
                total_minutes += int(parts[0]) * 60 + int(parts[1])
            except (ValueError, IndexError):
                continue

    hours = total_minutes // 60
    minutes = total_minutes % 60
    ui.notify(f'Total Time Spent: {hours}:{minutes:02d}', type='info', position='top')


async def save_curation_report(items: list[ChecklistItem]) -> None:
    """Save curation report to Word."""
    ui.notify('Curation report saved successfully!', type='positive')


async def export_yaml(items: list[ChecklistItem]) -> None:
    """Export to YAML."""
    data = {
        'metadata': app.storage.user.get('ds_metadata', {}),
        'checklist_items': [item.model_dump() for item in items],
    }
    yaml_str = yaml.dump(data)
    print('YAML Export:')
    print(yaml_str)
    ui.notify('YAML exported successfully!', type='positive')


def confirm_new_dataset() -> None:
    """Confirm and navigate to new dataset."""

    async def handle_confirm() -> None:
        app.storage.user.clear()
        ui.navigate.to('/')

    with ui.dialog() as dialog, ui.card():
        ui.label('This will erase all current input. Continue?')
        with ui.row():
            ui.button('Yes', on_click=lambda: [dialog.close(), handle_confirm()])
            ui.button('No', on_click=dialog.close)
    dialog.open()


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
    print('✓ Static files mounted:', static_path.absolute())
else:
    print('⚠ WARNING: Static directory not found!')
    print('  Looked for:', static_path.absolute())


# ============================================================================
# Run the application
# ============================================================================

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title='PyDataCuration - Styled POC', favicon='🔬', port=8080, storage_secret='your-secret-key-here')
