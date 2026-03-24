"""Stress test script for the API endpoint and the application."""

import httpx
from loguru import logger

from app import app_settings
from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.backend.models.setup_form import SetupDefaults
from pydatacuration.backend.models.setup_form import SetupForm


def run_curation(setup_form_instance: SetupForm, app_settings: AppSettings):
    logger.debug(app_settings.app_port)
    httpx.post(
        f'http://localhost:{app_settings.app_port}/api/run-curation',
        json=setup_form_instance.model_dump(mode='json'),
        timeout=None,
    )


def dois() -> list[str]:
    """Return a list of DOIs for testing."""
    return [
        '10.5072/TOTALLYFICTICIOUS',
        '10.5072/EVENMOREFICTICIOUS',
        '10.5072/ANOTHERFAKEONE',
    ]


if __name__ == '__main__':
    default_setup = SetupDefaults()
    app_settings = AppSettings()

    run_curation(default_setup, app_settings)
