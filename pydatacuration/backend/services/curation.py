"""Function for the curation process, including initialization, fetching the dataset, and running the checks."""

import asyncio
from pathlib import Path

import orjson
from loguru import logger

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.backend.services.db_writer import write_checklist_items_to_db
from pydatacuration.backend.services.db_writer import write_checklist_metadata_to_db
from pydatacuration.backend.services.db_writer import write_project_metadata_to_db
from pydatacuration.checker import Checker
from pydatacuration.checklist.utils import get_checklist_content
from pydatacuration.db import get_database
from pydatacuration.exceptions import DatasetAccessError
from pydatacuration.exceptions import DatasetNotFoundError
from pydatacuration.exceptions import DatasetUnauthorizedError
from pydatacuration.exceptions import DirectoryExistsError
from pydatacuration.services.api_calls.downloads import Downloads
from pydatacuration.services.verify_download_files import VerifyDownloadFiles
from pydatacuration.utils.directory_manager import DirectoryManager
from pydatacuration.utils.search_ds_meta import get_dataset_path
from pydatacuration.utils.utils import check_ds_read_access


def init_curation(body: SetupForm) -> None:
    """Initializes the working directory and database for the curation process.

    Args:
        body (SetupForm): The setup form containing the necessary information for initialization.

    Raises:
        DirectoryExistsError: If the working directory already exists and force_delete is not set to True.
    """
    dir_manager_instance = DirectoryManager.get_dir_manager_instance(body.project_number, Path(body.main_dir))

    if dir_manager_instance.project_dir.exists() and not body.force_delete:
        msg = f"Directory {dir_manager_instance.project_dir} already exists. Use 'force_delete=True' to overwrite."
        logger.error(msg)
        raise DirectoryExistsError(msg)

    dir_manager_instance.delete_dir(dir_manager_instance.project_dir)
    dir_manager_instance.make_project_dir()

    db = get_database(schema_name=body.project_number, db_file=dir_manager_instance.db_path)
    db.create_database()
    db.drop_schema(body.project_number)
    db.create_schema()

    logger.debug(
        f'Initialized working directory and database for project {body.project_number} at {dir_manager_instance.project_dir}'
    )


def _ensure_dataset_read_access(body: SetupForm) -> None:
    try:
        check_ds_read_access(body.pid, str(body.base_url), str(body.api_token or ''))
    except (DatasetUnauthorizedError, DatasetNotFoundError, DatasetAccessError):
        raise
    except Exception as exc:
        error_message = f'Failed to access dataset {body.pid}. Error: {exc}'
        logger.error(error_message)
        raise DatasetAccessError(error_message) from exc


async def fetch_curation(body: SetupForm) -> None:
    """Fetches the dataset for the curation process and saves it to the working directory.

    Args:
        body (SetupForm): The setup form containing the necessary information for fetching the dataset.
    """
    dir_manager_instance = DirectoryManager.get_dir_manager_instance(body.project_number, Path(body.main_dir))
    db = get_database(schema_name=body.project_number, db_file=dir_manager_instance.db_path)

    try:
        await asyncio.to_thread(_ensure_dataset_read_access, body)
        downloader = Downloads.from_setup_form(body)
        ds_metadata = await downloader.downloader()
        logger.info(f'Downloaded dataset for PID {body.pid} to {dir_manager_instance.project_dir}')

        VerifyDownloadFiles(ds_metadata=ds_metadata, directory_manager_instance=dir_manager_instance).verify()

    except Exception:
        db.drop_schema(body.project_number)
        dir_manager_instance.delete_dir(dir_manager_instance.project_dir)
        raise


def check_curation(body: SetupForm) -> None:
    """Runs the checks for the curation process.

    Args:
        body (SetupForm): The setup form containing the necessary information for running the checks.
    """
    dir_manager_instance = DirectoryManager.get_dir_manager_instance(
        body.project_number, Path(body.main_dir), res_dir=Path(body.res_dir)
    )
    db = get_database(schema_name=body.project_number, db_file=dir_manager_instance.db_path)

    res_dir = Path(body.res_dir) if body.res_dir else None

    try:
        # Get the checklist content
        checklist_content = get_checklist_content(body.checklist, res_dir)

        # Read the dataset metadata and dataverse tree from the downloaded files
        with Path(dir_manager_instance.metadata_dir, 'ds_metadata.json').open('rb') as f:
            ds_metadata = orjson.loads(f.read())

        checker = Checker(
            ds_metadata=ds_metadata,
            db_instance=db,
            setup_form_instance=body,
            directory_manager_instance=dir_manager_instance,
        )

        dataset_path = get_dataset_path(ds_metadata)

        # Setup writes — before checks run
        write_project_metadata_to_db(db, checker, dataset_path, body)
        write_checklist_metadata_to_db(db, checklist_content)
        write_checklist_items_to_db(db, checklist_content)

        checker.run_checks()
        logger.info('Checks completed')
    except Exception as exc:
        db.drop_schema(body.project_number)
        dir_manager_instance.delete_dir(dir_manager_instance.project_dir)
        error_message = f'Error occurred during checks: {exc}'
        logger.error(error_message)
        raise Exception(error_message) from exc


async def run_curation(body: SetupForm) -> None:
    """Runs the entire curation process, including initialization, fetching the dataset, and running the checks.

    Args:
        body (SetupForm): The setup form containing the necessary information for running the curation process
    """
    await asyncio.to_thread(init_curation, body)
    await fetch_curation(body)
    await asyncio.to_thread(check_curation, body)
