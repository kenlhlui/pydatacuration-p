"""API endpoints for the pydatacuration backend."""

import asyncio
from pathlib import Path

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.backend.services.curation import get_db
from pydatacuration.backend.services.curation import get_dirs
from pydatacuration.backend.services.curation import run_curation
from pydatacuration.exceptions import DatasetAccessError
from pydatacuration.exceptions import DatasetNotFoundError
from pydatacuration.exceptions import DatasetUnauthorizedError
from pydatacuration.exceptions import DirectoryExistsError
from pydatacuration.exporter import Exporter


router = APIRouter()

# Note: the endpoint is with /api prefix. So to trigger the endpoint the URL should be , for example, http://localhost:8000/api/run-curation.


@router.post('/run-curation')
async def run_curation_endpoint(body: SetupForm) -> dict[str, str]:
    """Runs the curation process and returns a status message.

    Args:
        body (SetupForm): The setup form containing the necessary information for running the curation process
    """
    try:
        await run_curation(body)
        return {'status': 'ok'}
    except DirectoryExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DatasetUnauthorizedError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DatasetAccessError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post('/export-word')
async def export_word_endpoint(
    ticket_number: str = Query(...),
    main_dir: str = Query(...),
    word_template_name: str | None = Query(None),
) -> dict[str, str]:
    """Exports the curation report as a Word document saved to the project outputs directory.

    Args:
        ticket_number (str): The ticket number identifying the curation project.
        main_dir (str): The main working directory where the project data is stored.
        word_template_name (str | None): Optional custom Word template filename.
    """
    dirs = get_dirs(ticket_number, Path(main_dir).resolve())
    if not dirs.project_dir.exists():
        raise HTTPException(status_code=404, detail=f'Project directory for ticket {ticket_number!r} not found.')

    db = get_db(schema_name=ticket_number, db_file=dirs.db_path)
    exporter = Exporter(db, dirs)
    await asyncio.to_thread(exporter.export_word, word_template_name)

    return {'status': 'ok'}


@router.get('/health')
def health_check() -> dict:
    """Health check endpoint to verify that the API is running.

    Returns:
        dict: A dictionary containing the status of the API.
    """
    return {'status': 'ok'}
