"""pydatacuration-p: FastAPI application for curation report generation."""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import List
from typing import Optional

import markdown
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pydantic import ValidationError


class ChecklistItem(BaseModel):
    """Model a single checklist item.

    Args:
        id (str): item identifier
        action (str): description of the action
        instructions (str): detailed instructions
        priority (str): priority level
        section (str): section this item belongs to (optional)

    Returns:
        None: data container
    """
    id: str
    action: str
    instructions: str
    priority: str
    section: str = ''


from typing import Optional

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
        List[ChecklistItem]: List of checklist items with their details.

    """
    with Path('res/check-list_template_high.yaml').open('r') as f:
        data = yaml.safe_load(f)
    items = []
    for item in data:
        items.append(ChecklistItem(
            id=item['id'],
            action=item['action'],
            instructions=markdown.markdown(item['instructions']),  # Convert Markdown to HTML
            priority=item['priority'],
            section=item.get('section', '')
        ))
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
    return templates.TemplateResponse('index.html', {'request': request, 'items': items})


# @app.post('/save-checklist')
# async def save_checklist(request: Request) -> JSONResponse:
#     """Save checklist data to JSON file."""
#     form = await request.form()

#     # Create data structure for JSON
#     checklist_data = {
#         'metadata': {
#             'saved_at': datetime.now().isoformat(),
#             'ticket_number': form.get('ticket_number', ''),
#             'curator_name': form.get('curator_name', ''),
#             'curator_email': form.get('curator_email', ''),
#             'dataset_title': form.get('dataset_title', ''),
#             'dataset_pid': form.get('dataset_pid', ''),
#             'dataset_id': form.get('dataset_id', ''),
#             'dataset_url': form.get('dataset_url', ''),
#             'log_generated_date': form.get('log_generated_date', ''),
#             'log_updated_date': form.get('log_updated_date', ''),
#         },
#         'items': []
#     }

#     # Extract checklist items
#     items = get_checklist_items()
#     for item in items:
#         item_data = {
#             'id': item.id,
#             'action': item.action,
#             'instructions': item.instructions,
#             'priority': item.priority,
#             'section': item.section,
#             'status': form.get(f'status-{item.id}', ''),
#             'comments': form.get(f'comments-{item.id}', ''),
#             'time_spent': form.get(f'time-{item.id}', ''),
#         }
#         checklist_data['items'].append(item_data)

#     # Add other comments
#     checklist_data['other_comments'] = form.get('comments-other', '')

#     # Save to JSON file
#     ticket_number = form.get('ticket_number', 'unknown')
#     filename = 'checklist.json'

#     # Use configurable output directory
#     output_dir = Path(os.getenv('OUTPUT_DIR', 'output'))
#     filepath = output_dir / filename

#     # Create output directory if it doesn't exist
#     output_dir.mkdir(exist_ok=True)

#     with filepath.open('w', encoding='utf-8') as f:
#         json.dump(checklist_data, f, indent=2)

#     return JSONResponse(content={
#         'success': True,
#         'message': f'Checklist saved to {filename}',
#         'filepath': filepath
#     })


async def run_command(command: str, cwd: str) -> dict:
    """Run a command and return the result.

    Args:
        command (str): Command to run
        cwd (str): Working directory

    Returns:
        dict: Command result with stdout, stderr, and return code
    """
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
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
        # Debug: Print the request data
        print(f'Request data: {request}')
        print(f'force_del: {request.force_del}, check_zip: {request.check_zip}')

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
        print(f'Running command: {cmd}')
        print(f'Working directory: {os.getcwd()}/{request.parent_dir}/{request.ticket_number}')

        # Run the command
        result = await run_command(cmd)

        if result['success']:
            return JSONResponse(content={
                'success': True,
                'message': 'Curation report generated successfully',
                'output': result['stdout'],
                'command': cmd,
                'template_dict_path': f'/template-dict/{request.parent_dir}/{request.ticket_number}',
                'curator_name': request.curator_name,
                'curator_email': request.curator_email,
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
        pprint(f'HTTP exception: {e}')
        raise e
    except Exception as e:
        pprint(f'Unexpected error: {e}')
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


@app.post('/shutdown')
async def shutdown() -> None:
    """Shutdown the uvicorn server."""
    os._exit(0)


class CurationLogRequest(BaseModel):
    curationLog: str

@app.post('/save-curation-log')
async def save_curation_log(request: CurationLogRequest) -> JSONResponse:
    """Process the YAML curation log from frontend."""
    try:
        # Parse YAML data
        yaml_data = yaml.safe_load(request.curationLog)

        # Process the structured data
        # yaml_data['metadata'] contains ticket info
        # yaml_data['checklist_items'] contains item statuses/comments
        # yaml_data['other'] contains additional comments

        # Save to file or database as needed
        ticket_number = yaml_data.get('metadata', {}).get('ticket_number', 'unknown')
        output_path = Path(f'output/curation_log_{ticket_number}.yaml')

        with output_path.open('w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False)

        return JSONResponse(content={
            'success': True,
            'message': 'Curation log saved successfully',
            'data': yaml_data
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'message': str(e)}
        )