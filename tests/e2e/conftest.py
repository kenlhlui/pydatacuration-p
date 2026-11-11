"""Fixtures for the end-to-end tests: run the curation pipeline once against a live Dataverse."""

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path

import pytest
from loguru import logger

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.backend.services.curation import run_curation
from pydatacuration.db import get_database
from pydatacuration.services.exporter import Exporter
from pydatacuration.utils.directory_manager import DirectoryManager


PROJECT_NUMBER = 'E2E-001'
RES_DIR = Path('res')


@dataclass(frozen=True)
class CuratedProject:
    """Outcome of one curation run: its directories and the check results keyed by check_id."""

    dirs: DirectoryManager
    results: dict[str, list]


@pytest.fixture(scope='session')
def curated_project(tmp_path_factory: pytest.TempPathFactory) -> CuratedProject:
    """Curate the seeded dataset and export the Word report, once per test session."""
    main_dir = tmp_path_factory.mktemp('workdir')
    logs_dir = main_dir / 'logs'
    logs_dir.mkdir()
    logger.add(logs_dir / 'e2e.log', level='DEBUG')  # The pipeline deletes the project dir on failure.

    form = SetupForm(
        base_url=os.environ['E2E_BASE_URL'],
        api_token=os.environ['E2E_API_TOKEN'],
        pid=os.environ['E2E_PID'],
        project_number=PROJECT_NUMBER,
        checklist='checklist-high.yaml',
        check_zip=True,
        force_delete=True,
        main_dir=main_dir,
        res_dir=RES_DIR,
    )
    asyncio.run(run_curation(form))

    dirs = DirectoryManager.get_dir_manager_instance(PROJECT_NUMBER, main_dir, res_dir=RES_DIR)
    db = get_database(db_file=dirs.db_path, project_number=PROJECT_NUMBER)
    Exporter(db, dirs).export_word()

    results = {row['check_id']: row['results'] for row in db.read_check_results()['check_results']}
    (main_dir / 'check_results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    return CuratedProject(dirs=dirs, results=results)
