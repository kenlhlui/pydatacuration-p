"""Stress test script for the API endpoint and the application."""

import time

import httpx
from loguru import logger

from app import app_settings
from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.backend.models.setup_form import SetupDefaults
from pydatacuration.backend.models.setup_form import SetupForm


def run_curation(setup_form_instance: SetupForm | SetupDefaults, app_settings: AppSettings) -> None:
    start_time = time.time()
    logger.info(f'Running crawl for {setup_form_instance.pid}')
    with httpx.Client() as client:
        client.post(
            f'http://localhost:{app_settings.app_port}/api/run-curation',
            json=setup_form_instance.model_dump(mode='json'),
            timeout=None,
        )
    end_time = time.time()
    logger.info(f'Crawl completed for {setup_form_instance.pid} in {end_time - start_time:.2f} seconds')


def datasets() -> dict[str, str]:
    """Return a list of DOIs for testing."""
    return {
        'CUR-001': 'doi:10.80240/FK2/HT4WPP',
        # 'CUR-002': 'doi:10.80240/FK2/HCUJKX',
        # 'CUR-003': 'doi:10.80240/FK2/CFUXY6',
        # 'CUR-004': 'doi:10.80240/FK2/WTMREZ',
        'CUR-005': 'doi:10.80240/FK2/TSHCUL',
    }


if __name__ == '__main__':
    default_setup = SetupDefaults()
    app_settings = AppSettings()

    datasets_dict = datasets()
    for ticket_number, pid in datasets_dict.items():
        setup_data = default_setup.model_dump()
        setup_data['ticket_number'] = ticket_number
        setup_data['pid'] = pid
        setup_form = SetupForm(**setup_data, main_dir=app_settings.main_dir)
        try:
            run_curation(setup_form, app_settings)
        except Exception as e:
            logger.error(f'Error occurred while running curation for {ticket_number}: {e}')
