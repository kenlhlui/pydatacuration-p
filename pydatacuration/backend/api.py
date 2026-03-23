from fastapi import APIRouter

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.backend.services.curation import check_curation
from pydatacuration.backend.services.curation import fetch_curation
from pydatacuration.backend.services.curation import init_curation


router = APIRouter()


@router.post('/init')
def init_endpoint(body: SetupForm) -> None:
    init_curation(body)


@router.post('/fetch')
async def fetch_endpoint(body: SetupForm) -> None:
    await fetch_curation(body)


@router.post('/check')
def check_endpoint(body: SetupForm) -> None:
    check_curation(body)


@router.get('/health')
def health_check() -> dict:
    return {'status': 'ok'}
