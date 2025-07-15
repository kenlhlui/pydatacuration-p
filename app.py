from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi import Request
from fastapi.responses import Response
import csv
import io
import os
class ChecklistRow(BaseModel):
    """Model a single checklist row.

    Args:
        id (str): row identifier
        action (str): description of the action
        comments (str): free-text notes (optional)

    Returns:
        None: data container
    """
    id: str
    action: str
    comments: str = ''


app = FastAPI()
templates = Jinja2Templates(directory='res')

@app.get('/', response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Render the checklist UI with a table.

    Args:
        request (Request): incoming HTTP request

    Returns:
        HTMLResponse: page with checklist table
    """
    rows: List[ChecklistRow] = [
        ChecklistRow(id='1.1', action='Verify dataset in Dataverse'),
        ChecklistRow(id='1.2', action='Check metadata completeness', comments='Review schema.org mapping'),
    ]
    return templates.TemplateResponse('index.html', {'request': request, 'rows': rows})


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


@app.post('/shutdown')
async def shutdown():
    """Shutdown the uvicorn server."""
    os._exit(0)
