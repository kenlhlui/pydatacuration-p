"""pydatacuration-p: FastAPI application for curation report generation."""

import asyncio
import os
import re
from pathlib import Path

import markdown2
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pydantic import ValidationError

from pydatacuration.custom_logging import logger
from pydatacuration.custom_logging import setup_logging
from pydatacuration.directory_manager import DirectoryManager
from pydatacuration.duck_db import DuckDB
from pydatacuration.new_generate_log import render_report_from_yaml


load_dotenv(override=True)
MAIN_DIR: Path = Path(os.getenv('MAIN_DIR', 'workdir'))

# Setup logging with your custom style
setup_logging(log_file_dir=MAIN_DIR / 'logs', log_level='DEBUG')


class ChecklistItem(BaseModel):
    """Model a single checklist item.

    Args:
        id (str): item identifier
        action (str): description of the action
        instructions (str): detailed instructions
        priority (str): priority level
        section (str): section this item belongs to (optional)
        automated_check_ids (list[str]): list of automated check IDs that map to this item
        information_location (str): location where information can be found

    Returns:
        None: data container
    """

    id: str
    action: str
    instructions: str
    priority: str
    section: str = ''
    automated_check_ids: list[str] | None = []
    information_location: str = ''
    check_type: str = ''


class SetupRequest(BaseModel):
    """Model for the setup form data matching CLI parameters.

    Args:
        pid (str): Persistent Identifier of the dataset
        base_url (str): Base URL of the Dataverse installation
        api_token (str): API token for the Dataverse installation
        ticket_number (str): Ticket number for the curation report
        curator_name (str): Curator's name
        curator_email (str): Curator's email
        main_dir (str): Working directory path
        force_del (bool): Force delete existing directory
        check_zip (bool): Unzip and check contents of zip files

    Returns:
        None: data container
    """

    pid: str
    base_url: str | None = None
    api_token: str | None = None
    ticket_number: str
    curator_name: str
    curator_email: str
    main_dir: str = str(MAIN_DIR.resolve())
    force_del: bool = False
    check_zip: bool = True


app = FastAPI()
templates = Jinja2Templates(directory='pydatacuration/frontend/')

# Mount static files for CSS, JS, and other assets
app.mount('/static', StaticFiles(directory='pydatacuration/frontend'), name='static')

# Load environment variables
load_dotenv()


def get_checklist_items(ticket_number: str) -> list[ChecklistItem]:
    """Get all checklist items from the check-list_template_high.yaml file.

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


@app.get('/', response_class=HTMLResponse)
def main_landing(request: Request) -> HTMLResponse:
    """Render the main landing page with navigation options.

    Args:
        request (Request): incoming HTTP request

    Returns:
        HTMLResponse: main landing page
    """
    return templates.TemplateResponse('main.html', {'request': request})


@app.get('/new-dataset', response_class=HTMLResponse)
def new_dataset(request: Request) -> HTMLResponse:
    """Render the new dataset setup page.

    Args:
        request (Request): incoming HTTP request

    Returns:
        HTMLResponse: new dataset setup page
    """
    # Get environment variables for prefilling form fields
    env_data = {
        'base_url': os.getenv('BASE_URL', ''),
        'api_token': os.getenv('API_TOKEN', ''),
        'curator_name': os.getenv('CURATOR_NAME', ''),
        'curator_email': os.getenv('CURATOR_EMAIL', ''),
        'main_dir': str(MAIN_DIR.resolve()),
    }

    return templates.TemplateResponse('landing.html', {'request': request, 'env_data': env_data})


@app.get('/checklist', response_class=HTMLResponse)
async def checklist(request: Request) -> HTMLResponse:
    """Render the checklist UI with a table.

    Args:
        request (Request): incoming HTTP request

    Returns:
        HTMLResponse: page with checklist table
    """
    ticket_number = request.query_params.get('ticket_number')
    items = get_checklist_items(ticket_number)

    resume_schema = request.query_params.get('resume')

    # Check results will be loaded via JavaScript from session storage
    return templates.TemplateResponse(
        'index.html',
        {
            'request': request,
            'items': items,
            'check_results': [],  # Empty, will be populated by frontend JavaScript
            'resume_schema': resume_schema,  # Pass to frontend for handling
        },
    )


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
        else:
            # Extract the last meaningful error message from CLI output
            error_details = []
            if result['stderr']:
                error_details.append(f'CLI Error: {result["stderr"].strip()}')
            if result['stdout']:
                # Look for error patterns in stdout (CLI logs errors there too)
                stdout_lines = result['stdout'].strip().split('\n')
                for line in reversed(stdout_lines):
                    clean_line = line.strip()
                    if (
                        'error' in clean_line.lower()
                        or 'aborting' in clean_line.lower()
                        or 'failed' in clean_line.lower()
                    ):
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


@app.get('/ds-metadata')
async def get_ds_metadata(main_dir: str, ticket_number: str, base_url: str = ''):
    """Serve the dataset metadata file for a specific ticket.

    Args:
        main_dir (str): Main directory name
        ticket_number (str): Ticket number
        base_url (str): Base URL for dataset links (optional)

    Returns:
        JSONResponse: Dataset metadata data
    """
    try:
        processed_metadata = {}
        dir_manager = DirectoryManager(ticket_number, main_dir)

        if dir_manager.db_path.exists():
            try:
                # Use DuckDB to get metadata
                duck_db = DuckDB(schema_name=ticket_number, db_file=dir_manager.db_path)
                processed_metadata = duck_db.read_project_metadata_record()
                if processed_metadata and processed_metadata.get('dataset_pid'):
                    return JSONResponse(content=processed_metadata)
                logger.warning(f'No data found in DuckDB for ticket {ticket_number}')
            except Exception as db_error:
                logger.warning(f'DuckDB query failed for ticket {ticket_number}: {db_error}')

    except Exception as e:
        logger.error(f'Error reading dataset metadata for ticket {ticket_number}: {e}')
        raise HTTPException(status_code=500, detail=f'Error reading dataset metadata: {str(e)}')


def _get_check_results_from_duckdb(main_dir: str, ticket_number: str, table_name: str) -> dict:
    """Get the check results from DuckDB for a specific ticket."""
    try:
        dir_manager = DirectoryManager(ticket_number, main_dir)
        duck_db = DuckDB(schema_name=ticket_number, db_file=dir_manager.db_path)
        return duck_db.read_check_results(table_name)
    except Exception as e:
        logger.error(f'Error fetching check results from DuckDB for ticket {ticket_number}: {e}')
        return {'error': str(e)}


def get_checklist_from_duckdb(main_dir: str | Path, ticket_number: str) -> dict:
    """Get the checklist from DuckDB for a specific ticket."""
    try:
        dir_manager = DirectoryManager(ticket_number, main_dir)
        duck_db = DuckDB(schema_name=ticket_number, db_file=dir_manager.db_path)
        return duck_db.read_checklist()
    except Exception as e:
        logger.error(f'Error fetching checklist from DuckDB for ticket {ticket_number}: {e}')
        return {'error': str(e)}


@app.delete('/api/schemas/{schema_name}')
async def delete_schema(schema_name: str) -> JSONResponse:
    """Delete a specific schema from DuckDB.

    Args:
        schema_name (str): Name of the schema to delete

    Returns:
        JSONResponse: Result of the delete operation
    """
    try:
        # Use default main database directory to find the main database file
        main_dir = MAIN_DIR
        db_dir = Path(main_dir) / 'db'
        db_file = db_dir / 'duckdb.db'

        if not db_file.exists():
            logger.warning(f'Database file not found at {db_file}')
            return JSONResponse(status_code=404, content={'error': 'Database file not found'})

        # Create a DuckDB instance to delete the schema
        duck_db = DuckDB(schema_name='temp', db_file=db_file)

        # Prune the schema name
        schema_name_pruned = schema_name.replace('duckdb.', '').replace('"', '')

        # Delete the schema
        duck_db.sql_drop_schema(schema_name_pruned)
        logger.info(f'Successfully deleted schema: {schema_name_pruned}')

        return JSONResponse(content={'success': True, 'message': f'Schema {schema_name_pruned} deleted successfully'})

    except Exception as e:
        logger.error(f'Error deleting schema {schema_name_pruned}: {e}')
        return JSONResponse(status_code=500, content={'error': f'Error deleting schema: {str(e)}'})


@app.get('/api/schemas')
async def get_schemas() -> JSONResponse:
    """Get all available schemas (projects) from DuckDB.

    Returns:
        JSONResponse: List of available schemas with metadata
    """
    try:
        # Use default main database directory to find the main database file
        main_dir = MAIN_DIR
        db_dir = Path(main_dir) / 'db'
        db_file = db_dir / 'duckdb.db'

        if not db_file.exists():
            logger.warning(f'Database file not found at {db_file}')
            return JSONResponse(content={'schemas': []})

        # Create a DuckDB instance to get schemas (schema_name doesn't matter for this operation)
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
                        'has_metadata': bool(metadata and metadata.get('dataset_pid')),
                    }
                )
            except Exception as e:
                logger.warning(f'Could not get metadata for schema {schema_name}: {e}')
                schemas_with_metadata.append({'name': schema_name, 'last_modified': 'Unknown', 'has_metadata': False})

        # Sort by last modified (most recent first)
        schemas_with_metadata.sort(key=lambda x: x['last_modified'], reverse=True)

        return JSONResponse(content={'schemas': schemas_with_metadata})

    except Exception as e:
        logger.error(f'Error fetching schemas: {e}')
        return JSONResponse(status_code=500, content={'error': f'Error fetching schemas: {str(e)}'})


@app.get('/api/check-results')
async def get_check_results_from_session(request: Request) -> JSONResponse:
    """Serve check results based on session storage data (via query params).

    Expected query parameters:
    - ticket_number: from sessionStorage
    - main_dir: optional, defaults to 'workdir'

    Returns:
        JSONResponse: Check results data or empty results if not found
    """
    try:
        main_dir = MAIN_DIR
        ticket_number = request.query_params.get('ticket_number')
        _check_results = _get_check_results_from_duckdb(main_dir, ticket_number, 'check_results')

        return JSONResponse(content=_check_results)
    except Exception as e:
        print(f'Error loading check results: {e}')
        return JSONResponse(content={'check_results': []})


@app.post('/shutdown')
async def shutdown() -> None:
    """Shutdown the uvicorn server."""
    os._exit(0)


class CurationLogRequest(BaseModel):
    curationLog: str


class ChecklistUpdateRequest(BaseModel):
    """Model for updating checklist items in DuckDB."""
    ticket_number: str
    item_id: str
    status: str | None = None
    comments: str | None = None
    time_spent: str | None = None


@app.post('/export-curation-log')
async def export_log_yaml(request: CurationLogRequest) -> JSONResponse:
    """Export the curationLog from sessionStorage to a YAML file."""
    try:
        # Parse YAML data
        yaml_data = yaml.safe_load(request.curationLog)

        checklist_items = yaml_data.get('checklist_items', [])
        # Convert array to dictionary for easier lookup
        checklist_map = {}
        if isinstance(checklist_items, list):
            for item in checklist_items:
                if isinstance(item, dict) and 'id' in item:
                    checklist_map[item['id']] = item
        elif isinstance(checklist_items, dict):
            checklist_map = checklist_items

        # Load the metadata block
        metadata = yaml_data.get('metadata', {})

        # Get the ticket number from metadata
        ticket_number = metadata.get('ticket_number', 'unknown')

        # Read the check-list_template_high.yaml to get the checklist items
        checklist = get_checklist_from_duckdb(MAIN_DIR, ticket_number)
        check_list_template_items = checklist.get('checklist', [])

        # Update checklist items with user data
        for item in check_list_template_items:
            item_id = item['id']
            # Look up our map (keys are already strings)
            data = checklist_map.get(item_id, {})
            # Update the item with status, comments, and time spent
            item['status'] = data.get('status', '')
            item['comments'] = data.get('comments', '')
            item['time_spent'] = data.get('time', '')

        # Create the final output structure
        output_data = {'metadata': {}, 'checklist': check_list_template_items}

        # Add metadata from the YAML data
        metadata = yaml_data.get('metadata', {})
        if metadata:
            for key, value in metadata.items():
                # Handle datetime objects
                if hasattr(value, 'strftime'):  # Check if it's a date/datetime object
                    output_data['metadata'][key] = value.strftime('%Y-%m-%d')
                else:
                    output_data['metadata'][key] = value

        # Save to file
        ticket_number = metadata.get('ticket_number', 'unknown')
        main_dir = metadata.get('main_dir', 'workdir')
        dir_manager = DirectoryManager(ticket_number, main_dir)
        output_path = dir_manager.get_dir('outputs') / f'{ticket_number}.yaml'

        with output_path.open('w', encoding='utf-8') as f:
            yaml.dump(output_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        return JSONResponse(
            content={
                'success': True,
                'message': f'Curation log in YAML format exported successfully to {output_path}',
                'data': output_data,
                'file_path': str(output_path),
            }
        )

    except Exception as e:
        print(f'Error in export_log_yaml: {e}')
        return JSONResponse(status_code=500, content={'success': False, 'message': str(e)})


@app.post('/render-report')
async def render_report(request: Request) -> JSONResponse:
    """Render a DOCX report from the YAML curation log.

    Args:
        request (Request): HTTP request containing the curation log data

    Returns:
        JSONResponse: Result of the report generation
    """
    try:
        # Handle both JSON and form data
        if request.headers.get('content-type') == 'application/json':
            data = await request.json()
            curation_log_data = data.get('curationLog')
        else:
            # Handle form data - reconstruct the YAML from form fields
            form_data = await request.form()

            # Get the YAML data from sessionStorage (passed via form)
            curation_log_data = form_data.get('curationLog', '')

            if not curation_log_data:
                # If no YAML data in form, try to reconstruct from session storage
                # This might require getting it from the frontend differently
                return JSONResponse(
                    status_code=400, content={'success': False, 'message': 'No curation log data found in request'}
                )

        # Create CurationLogRequest object for save_log_yaml
        curation_request = CurationLogRequest(curationLog=curation_log_data)

        # Invoke save_log_yaml before rendering the report
        save_result = await export_log_yaml(curation_request)

        # Check if save was successful
        if not save_result.status_code == 200:
            return JSONResponse(
                status_code=500, content={'success': False, 'message': 'Failed to save curation log before rendering'}
            )

        # Parse YAML to get ticket number for dynamic file paths
        yaml_data = yaml.safe_load(curation_log_data)
        ticket_number = yaml_data.get('metadata', {}).get('ticket_number', 'unknown')
        main_dir = yaml_data.get('metadata', {}).get('main_dir', 'workdir')
        dir_manager = DirectoryManager(ticket_number, main_dir)

        # Render the report from the saved YAML file with dynamic paths
        yaml_path = dir_manager.get_dir('outputs') / f'{ticket_number}.yaml'
        output_path = dir_manager.get_dir('outputs') / f'{ticket_number}.docx'

        render_report_from_yaml(
            yaml_path=yaml_path, template_path=Path('res/new_template_high.docx'), output_path=output_path
        )

        return JSONResponse(
            content={
                'success': True,
                'message': f'Curation log saved to {output_path} successfully',
                'output_file': str(output_path),
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500, content={'success': False, 'message': f'Error when rendering report: {str(e)}'}
        )


@app.get('/api/checklist-data')
async def get_checklist_data(request: Request) -> JSONResponse:
    """Get checklist data with saved status, comments, and time_spent from DuckDB.

    Expected query parameters:
    - ticket_number: The ticket number to get data for

    Returns:
        JSONResponse: Checklist data with saved values
    """
    try:
        ticket_number = request.query_params.get('ticket_number')
        if not ticket_number:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'message': 'ticket_number parameter is required'}
            )

        # Get checklist data from DuckDB
        checklist_data = get_checklist_from_duckdb(MAIN_DIR, ticket_number)

        return JSONResponse(content=checklist_data)

    except Exception as e:
        ticket_number = request.query_params.get('ticket_number', 'unknown')
        logger.error(f'Error fetching checklist data for ticket {ticket_number}: {e}')
        return JSONResponse(
            status_code=500,
            content={'success': False, 'message': f'Error fetching checklist data: {str(e)}'}
        )


@app.post('/update-checklist-item')
async def update_checklist_item(request: ChecklistUpdateRequest) -> JSONResponse:
    """Update a single checklist item in DuckDB.

    Args:
        request (ChecklistUpdateRequest): Request containing checklist item update data

    Returns:
        JSONResponse: Result of the update operation
    """
    try:
        logger.info(f'Updating checklist item {request.item_id} for ticket {request.ticket_number}')

        # Get the database file path
        dir_manager = DirectoryManager(request.ticket_number, MAIN_DIR)
        db_file = dir_manager.db_path

        # Create DuckDB instance for the ticket's schema
        duck_db = DuckDB(schema_name=request.ticket_number, db_file=db_file)

        # Check if schema exists
        if not duck_db.sql_check_schema_exists(request.ticket_number):
            logger.warning(f'Schema {request.ticket_number} does not exist')
            return JSONResponse(
                status_code=404,
                content={'success': False, 'message': f'Ticket schema {request.ticket_number} not found'}
            )

        # Update the checklist item
        success = duck_db.sql_update_checklist_item(
            item_id=request.item_id,
            status=request.status,
            comments=request.comments,
            time_spent=request.time_spent
        )

        if success:
            logger.info(f'Successfully updated checklist item {request.item_id}')
            return JSONResponse(
                content={
                    'success': True,
                    'message': f'Checklist item {request.item_id} updated successfully'
                }
            )

        logger.error(f'Failed to update checklist item {request.item_id}')
        return JSONResponse(
            status_code=400,
            content={'success': False, 'message': f'Failed to update checklist item {request.item_id}'}
        )

    except Exception as e:
        logger.error(f'Error updating checklist item {request.item_id}: {e}')
        return JSONResponse(
            status_code=500,
            content={'success': False, 'message': f'Internal server error: {str(e)}'}
        )
