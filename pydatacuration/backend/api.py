"""API endpoints for the pydatacuration backend."""

from fastapi import APIRouter
from fastapi import HTTPException

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.backend.services.curation import run_curation
from pydatacuration.exceptions import DatasetAccessError
from pydatacuration.exceptions import DatasetNotFoundError
from pydatacuration.exceptions import DatasetUnauthorizedError
from pydatacuration.exceptions import DirectoryExistsError


router = APIRouter()


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


@router.get('/health')
def health_check() -> dict:
    """Health check endpoint to verify that the API is running.

    Returns:
        dict: A dictionary containing the status of the API.
    """
    return {'status': 'ok'}
