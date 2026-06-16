"""Stress test script for the API endpoint and the application."""

import time
from pathlib import Path

import httpx2
from loguru import logger

from app import app_settings
from pydatacuration.backend.models.app_settings import AppSettings
from pydatacuration.backend.models.setup_form import SetupDefaults
from pydatacuration.backend.models.setup_form import SetupForm


def run_curation(setup_form_instance: SetupForm | SetupDefaults, app_settings: AppSettings) -> None:
    start_time = time.time()
    logger.info(f'Running crawl for {setup_form_instance.pid} with project number {setup_form_instance.project_number}')
    with httpx2.Client() as client:
        client.post(
            f'http://localhost:{app_settings.app_port}/api/run-curation',
            json=setup_form_instance.model_dump(mode='json'),
            timeout=None,
        )
    end_time = time.time()
    logger.info(f'Crawl completed for {setup_form_instance.pid} in {end_time - start_time:.2f} seconds')


def datasets() -> dict[str, str]:
    """Return a list of DOIs for testing."""
    # Note: Change the DOI here for different datasets.
    with Path('tests/doi_list.txt').open(encoding='utf-8') as f:
        doi_list = [line.strip() for line in f if line.strip() and '#' not in line]
    return {f'CUR-{i + 1:03d}': doi for i, doi in enumerate(doi_list)}


if __name__ == '__main__':
    default_setup = SetupDefaults()
    app_settings = AppSettings()

    datasets_dict = datasets()
    for project_number, pid in datasets_dict.items():
        setup_data: dict = default_setup.model_dump(mode='python')
        setup_data['project_number'] = project_number
        setup_data['pid'] = pid
        setup_form = SetupForm(**setup_data, main_dir=app_settings.main_dir)
        try:
            run_curation(setup_form, app_settings)
        except Exception as e:
            logger.error(f'Error occurred while running curation for {project_number}: {e}')
