from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi import Request
from fastapi.responses import Response
import csv
import io
import os
import subprocess
import asyncio
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


class SetupRequest(BaseModel):
    """Model for the setup form data matching CLI parameters.

    Args:
        pid (str): Persistent Identifier of the dataset
        base_url (str): Base URL of the Dataverse installation
        api_token (str): API token for the Dataverse installation
        ticket_number (str): Ticket number for the curation report
        parent_dir (str): Working directory path
        force_del (bool): Force delete existing directory
        check_zip (bool): Unzip and check contents of zip files

    Returns:
        None: data container
    """
    pid: str
    base_url: Optional[str] = None
    api_token: Optional[str] = None
    ticket_number: str
    parent_dir: str = "workdir"
    force_del: bool = False
    check_zip: bool = True


app = FastAPI()
templates = Jinja2Templates(directory='res')

def get_checklist_items():
    """Get all checklist items with their details."""
    return [
        ChecklistItem(id='1.1', action='Is the dataset deposited directly into U of T Dataverse?', 
                     instructions='Python scripted. If the dataset is deposited in a sub-dataverse collection, include the name of the collection.', 
                     priority='info', section='1.0 Structure of deposit'),
        ChecklistItem(id='1.2', action='Has the depositor (or their research group) previously created or submitted to a dataverse collection?', 
                     instructions='Python scripted. Confirm whether the listed dataverse collection refers to the same researcher/author', 
                     priority='info', section='1.0 Structure of deposit'),
        ChecklistItem(id='1.3', action='If the dataset was deposited in a sub-dataverse collection, does it require its own dataverse or is there an associated dataverse?', 
                     instructions='If the depositor created a dataverse with one dataset: Is it the only dataset in the sub-dataverse collection? Is there another sub-dataverse collection it should be in?', 
                     priority='require', section='1.0 Structure of deposit'),
        ChecklistItem(id='2.1b', action='Do all the files open properly?', 
                     instructions='Semi-automated using Python scripts. For files that cannot be opened programmatically - if we have the program, open min. 5 of each type of file.', 
                     priority='require', section='2.0 Files'),
        ChecklistItem(id='2.2', action='Are all files free of the following special characters (<>:"/\\|?*,@$~)?', 
                     instructions='Python scripted.', 
                     priority='recommend', section='2.0 Files'),
        ChecklistItem(id='3.1', action='Does the dataset include a separate README file?', 
                     instructions='Python scripted. Read the `ds_tree.txt` file in the log_files folder to identify whether there is a README file, but it is not named with \'README\'', 
                     priority='require', section='3.0 Documentation'),
        ChecklistItem(id='4.1', action='Are there any typos in metadata fields?', 
                     instructions="""Python scripted. Only checking the following fields:\n1. Title, 2. Subtitle, 3. Alternative Title, 4. Description, 5. Notes
                     """,
                     priority='require', section='4.0 Metadata'),
        ChecklistItem(id='5.1', action='Does the dataset contain any obvious sensitivity issues, such as direct identifiers?', 
                     instructions='Review documentation and file names and see if there are any that should be opened and reviewed', 
                     priority='require', section='5.0 Sensitive data and IP'),
    ]

@app.get('/', response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    """Render the landing page for setup.

    Args:
        request (Request): incoming HTTP request

    Returns:
        HTMLResponse: setup landing page
    """
    return templates.TemplateResponse('landing.html', {'request': request})


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


@app.post('/export-csv')
async def export_csv(request: Request) -> Response:
    """Reconstructs the table from form data and streams a CSV."""
    form = await request.form()
    # form is a MultiDict of keys like 'status-1.1', 'comments-1.1', 'time-1.1', etc.
    # Extract unique row IDs:
    row_ids = sorted({key.split('-')[1] for key in form.keys() if '-' in key})

    # Prepare CSV in memory
    buf = io.StringIO()
    writer = csv.writer(buf)
    # header
    writer.writerow(['ID', 'Action Item', 'Status', 'Comments', 'Priority', 'Time Spent'])
    for rid in row_ids:
        status = form.get(f'status-{rid}', '')
        comments = form.get(f'comments-{rid}', '')
        priority = form.get(f'priority-{rid}', '')
        time_spent = form.get(f'time-{rid}', '')
        # if you also POSTed action text, you could grab it similarly, or re-lookup your stub rows
        action = form.get(f'action-{rid}', '')
        writer.writerow([rid, action, status, comments, priority, time_spent])

    csv_bytes = buf.getvalue().encode('utf-8')
    return Response(
        content=csv_bytes,
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="curation_log.csv"'}
    )


async def run_command(command: str, cwd: str = None) -> dict:
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
        # Build the command to run pydatacuration CLI
        cmd_parts = [
            'python', '-m', 'pydatacuration.main', 'gen-curation-report',
            '--pid', f'"{request.pid}"',
            '--ticket-number', f'"{request.ticket_number}"',
            '--parent-dir', f'"{request.parent_dir}"'
        ]
        print(f'{os.getcwd()}')
        # Add base URL if provided
        if request.base_url:
            cmd_parts.extend(['--base-url', f'"{request.base_url}"'])

        # Add API token if provided
        if request.api_token:
            cmd_parts.extend(['--api-token', f'"{request.api_token}"'])

        # Add optional flags
        if request.force_del:
            cmd_parts.append('--force-del')
        else:
            cmd_parts.append('--no-force-del')

        # Join command parts
        cmd = ' '.join(cmd_parts)

        # Run the command
        result = await run_command(cmd)

        if result['success']:
            return JSONResponse(content={
                'success': True,
                'message': 'Curation report generated successfully',
                'output': result['stdout'],
                'command': cmd
            })
        else:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'message': 'Curation command failed',
                    'error': result['stderr'],
                    'output': result['stdout'],
                    'command': cmd,
                    'return_code': result['return_code']
                }
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'message': f'Error during setup: {str(e)}'
            }
        )


@app.post('/shutdown')
async def shutdown():
    """Shutdown the uvicorn server."""
    os._exit(0)
