from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

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
