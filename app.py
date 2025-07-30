"""pydatacuration-p: FastAPI application for curation report generation."""
import asyncio
import json
import os
from pathlib import Path

# import markdown
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

from pydatacuration.new_generate_log import render_report_from_yaml


class ChecklistItem(BaseModel):
    """Model a single checklist item.

    Args:
        id (str): item identifier
        action (str): description of the action
        instructions (str): detailed instructions
        priority (str): priority level
        section (str): section this item belongs to (optional)
        automated_check_ids (list[str]): list of automated check IDs that map to this item

    Returns:
        None: data container
    """
    id: str
    action: str
    instructions: str
    priority: str
    section: str = ''
    automated_check_ids: list[str] = []


class SetupRequest(BaseModel):
    """Model for the setup form data matching CLI parameters.

    Args:
        pid (str): Persistent Identifier of the dataset
        base_url (str): Base URL of the Dataverse installation
        api_token (str): API token for the Dataverse installation
        ticket_number (str): Ticket number for the curation report
        curator_name (str): Curator's name
        curator_email (str): Curator's email
        parent_dir (str): Working directory path
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
    parent_dir: str = 'workdir'
    force_del: bool = False
    check_zip: bool = True


app = FastAPI()
templates = Jinja2Templates(directory='pydatacuration/frontend/')

# Mount static files for CSS, JS, and other assets
app.mount("/static", StaticFiles(directory="pydatacuration/frontend"), name="static")

# Load environment variables
load_dotenv()


def get_checklist_items() -> list[ChecklistItem]:
    """Get all checklist items from the check-list_template_high.yaml file.

    Returns:
        list[ChecklistItem]: List of checklist items with their details.

    """
    with Path('res/check-list_template_high.yaml').open('r') as f:
        data = yaml.safe_load(f)
    items = []
    for item in data.get('checklist', []):
        checklist_item = ChecklistItem(
            id=item['id'],
            action=item['action'],
            instructions=markdown2.markdown(item['instructions']),  # Convert Markdown to HTML
            priority=item['priority'],
            section=item.get('section', ''),
            automated_check_ids=item.get('automated_check_ids', [])
        )
        if checklist_item.automated_check_ids:
            print(f"Item {checklist_item.id} has automated_check_ids: {checklist_item.automated_check_ids}")
        items.append(checklist_item)
    return items


@app.get('/', response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    """Render the landing page for setup.

    Args:
        request (Request): incoming HTTP request

    Returns:
        HTMLResponse: setup landing page
    """
    # Get environment variables for prefilling form fields
    env_data = {
        'base_url': os.getenv('BASE_URL', ''),
        'api_token': os.getenv('API_TOKEN', ''),
        'curator_name': os.getenv('CURATOR_NAME', ''),
        'curator_email': os.getenv('CURATOR_EMAIL', ''),
    }

    return templates.TemplateResponse('landing.html', {
        'request': request,
        'env_data': env_data
    })


@app.get('/checklist', response_class=HTMLResponse)
def checklist(request: Request) -> HTMLResponse:
    """Render the checklist UI with a table.

    Args:
        request (Request): incoming HTTP request

    Returns:
        HTMLResponse: page with checklist table
    """
    items = get_checklist_items()
    
    # Check results will be loaded via JavaScript from session storage
    return templates.TemplateResponse('index.html', {
        'request': request, 
        'items': items, 
        'check_results': []  # Empty, will be populated by frontend JavaScript
    })


async def run_command(command: str) -> dict:
    """Run a command and return the result.

    Args:
        command (str): Command to run

    Returns:
        dict: Command result with stdout, stderr, and return code
    """
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        return {
            'stdout': stdout.decode(),
            'stderr': stderr.decode(),
            'return_code': process.returncode,
            'success': process.returncode == 0
        }
    except Exception as e:
        return {
            'stdout': '',
            'stderr': str(e),
            'return_code': -1,
            'success': False
        }


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
            raise HTTPException(status_code=400, detail='PID is required')
        if not request.ticket_number or not request.ticket_number.strip():
            raise HTTPException(status_code=400, detail='Ticket number is required')
        if not request.curator_name or not request.curator_name.strip():
            raise HTTPException(status_code=400, detail='Curator name is required')
        if not request.curator_email or not request.curator_email.strip():
            raise HTTPException(status_code=400, detail='Curator email is required')

        # Build the command to run pydatacuration CLI
        cmd_parts = [
            'python', '-m', 'pydatacuration.main', 'gen-curation-report',
            '--pid', f'"{request.pid}"',
            '--ticket-number', f'"{request.ticket_number}"',
            '--parent-dir', f'"{request.parent_dir}"'
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

        # Define the working directory
        app.state.work_dir = Path(Path.cwd()) / request.parent_dir / request.ticket_number
        print(f'Working directory: {app.state.work_dir}')

        # Run the command
        result = await run_command(cmd)

        if result['success']:
            return JSONResponse(content={
                'success': True,
                'message': 'Curation report generated successfully',
                'output': result['stdout'],
                'command': cmd,
                'curator_name': request.curator_name,
                'curator_email': request.curator_email,
                'redirect_url': f'/checklist?parent_dir={request.parent_dir}&ticket_number={request.ticket_number}',
            })
        return JSONResponse(
            status_code=400,
            content={
                'success': False,
                'message': 'Curation command failed',
                'error': result['stderr'],
                'output': result['stdout'],
                'command': cmd,
                'return_code': result['return_code'],
            }
        )

    except ValidationError as e:
        print(f'Validation error: {e}')
        return JSONResponse(
            status_code=422,
            content={
                'success': False,
                'message': 'Validation error',
                'detail': str(e),
                'errors': e.errors()
            }
        )
    except HTTPException as e:
        print(f'HTTP exception: {e}')
        raise e
    except Exception as e:
        print(f'Unexpected error: {e}')
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'message': f'Error during setup: {str(e)}'
            }
        )


@app.get('/template-dict/{parent_dir}/{ticket_number}')
async def get_template_dict(parent_dir: str, ticket_number: str) -> JSONResponse:
    """Serve the template dictionary file for a specific ticket.

    Args:
        parent_dir (str): Parent directory name
        ticket_number (str): Ticket number

    Returns:
        JSONResponse: Template dictionary data
    """
    try:
        template_path = Path(parent_dir) / ticket_number / 'log_files' / 'template_dict.json'
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template dictionary not found")

        with template_path.open('r', encoding='utf-8') as f:
            template_data = json.load(f)

        return JSONResponse(content=template_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading template dictionary: {str(e)}")


@app.get('/check-results/{parent_dir}/{ticket_number}')
async def get_check_results(parent_dir: str, ticket_number: str) -> JSONResponse:
    """Serve the check results file for a specific ticket.

    Args:
        parent_dir (str): Parent directory name
        ticket_number (str): Ticket number

    Returns:
        JSONResponse: Check results data
    """
    try:
        check_results_path = Path(parent_dir) / ticket_number / 'log_files' / 'check_results.json'
        if not check_results_path.exists():
            raise HTTPException(status_code=404, detail="Check results not found")

        with check_results_path.open('r', encoding='utf-8') as f:
            check_results_data = json.load(f)

        return JSONResponse(content=check_results_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading check results: {str(e)}")


@app.get('/api/check-results')
async def get_check_results_from_session(request: Request) -> JSONResponse:
    """Serve check results based on session storage data (via query params).
    
    Expected query parameters:
    - ticket_number: from sessionStorage
    - parent_dir: optional, defaults to 'workdir'
    
    Returns:
        JSONResponse: Check results data or empty results if not found
    """
    try:
        parent_dir = request.query_params.get('parent_dir', 'workdir')
        ticket_number = request.query_params.get('ticket_number')
        
        if not ticket_number:
            return JSONResponse(content={'check_results': []})
        
        check_results_path = Path(parent_dir) / ticket_number / 'log_files' / 'check_results.json'
        if not check_results_path.exists():
            return JSONResponse(content={'check_results': []})

        with check_results_path.open('r', encoding='utf-8') as f:
            check_results_data = json.load(f)

        return JSONResponse(content=check_results_data)
    except Exception as e:
        print(f"Error loading check results: {e}")
        return JSONResponse(content={'check_results': []})


@app.post('/shutdown')
async def shutdown() -> None:
    """Shutdown the uvicorn server."""
    os._exit(0)


class CurationLogRequest(BaseModel):
    curationLog: str

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

        # Read the check-list_template_high.yaml to get the checklist items
        with Path('res/check-list_template_high.yaml').open('r', encoding='utf-8') as f:
            template_data = yaml.safe_load(f)
            check_list_template_items = template_data.get('checklist', [])

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
        output_data = {
            'metadata': {},
            'checklist': check_list_template_items
        }

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
        output_path = Path(f'{app.state.work_dir}', 'log_files', f'{ticket_number}_new.yaml')

        with output_path.open('w', encoding='utf-8') as f:
            yaml.dump(output_data, f,
                      default_flow_style=False,
                      sort_keys=False,
                      allow_unicode=True)

        return JSONResponse(content={
            'success': True,
            'message': f'Curation log in YAML format exported successfully to {output_path}',
            'data': output_data,
            'file_path': str(output_path)
        })

    except Exception as e:
        print(f'Error in export_log_yaml: {e}')
        return JSONResponse(
            status_code=500,
            content={'success': False, 'message': str(e)}
        )


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
                    status_code=400,
                    content={
                        'success': False,
                        'message': 'No curation log data found in request'
                    }
                )

        # Create CurationLogRequest object for save_log_yaml
        curation_request = CurationLogRequest(curationLog=curation_log_data)

        # Invoke save_log_yaml before rendering the report
        save_result = await export_log_yaml(curation_request)

        # Check if save was successful
        if not save_result.status_code == 200:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'message': 'Failed to save curation log before rendering'
                }
            )

        # Parse YAML to get ticket number for dynamic file paths
        yaml_data = yaml.safe_load(curation_log_data)
        ticket_number = yaml_data.get('metadata', {}).get('ticket_number', 'unknown')

        # Render the report from the saved YAML file with dynamic paths
        yaml_path = Path(f'{app.state.work_dir}', 'log_files', f'{ticket_number}_new.yaml')
        output_path = Path(f'{app.state.work_dir}', 'log_files', f'{ticket_number}_new.docx')

        render_report_from_yaml(
            yaml_path=yaml_path,
            template_path=Path('res/new_template_high.docx'),
            output_path=output_path
        )

        return JSONResponse(content={
            'success': True,
            'message': f'Curation log saved to {output_path} successfully',
            'output_file': str(output_path)
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'message': f'Error when rendering report: {str(e)}'
            }
        )
