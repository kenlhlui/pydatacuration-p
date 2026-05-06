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
from pydatacuration.checker.services.dataset_tree_info import DatasetTreeInfo
from pydatacuration.checklist.utils import get_checklist_content
from pydatacuration.db import DatabaseBackend
from pydatacuration.db import get_database
from pydatacuration.exceptions import DirectoryExistsError
from pydatacuration.services.api_calls.call_dv import DVAPICalls
from pydatacuration.services.api_calls.downloads import Downloads
from pydatacuration.services.api_calls.httpx_client import HTTPXClient
from pydatacuration.utils import directory_manager
from pydatacuration.utils.search_ds_meta import get_ds_title
from pydatacuration.utils.utils import DatasetAccessError
from pydatacuration.utils.utils import DatasetNotFoundError
from pydatacuration.utils.utils import DatasetUnauthorizedError
from pydatacuration.utils.utils import check_ds_read_access


def get_dirs(project_number: str, main_dir: Path, res_dir: Path | None = None) -> directory_manager.DirectoryManager:
    """Returns a DirectoryManager instance for the given project number and main directory.

    Args:
        project_number (str): The project number for the curation process.
        main_dir (Path): The main directory where the project directory will be created.
        res_dir (Path | None): Optional path to the resource directory containing checklist files.

    Returns:
        DirectoryManager: An instance of the DirectoryManager class.

    """
    return directory_manager.DirectoryManager(project_number, str(main_dir), res_dir=res_dir)


def get_db(schema_name: str, db_file: Path) -> DatabaseBackend:
    """Returns a DatabaseBackend instance for the given schema name and database file.

    Args:
        schema_name (str): The name of the schema.
        db_file (Path): The path to the database file.

    Returns:
        DatabaseBackend: An instance of the DatabaseBackend class.
    """
    return get_database(schema_name=schema_name, db_file=db_file)


def init_curation(body: SetupForm) -> None:
    """Initializes the working directory and database for the curation process.

    Args:
        body (SetupForm): The setup form containing the necessary information for initialization.

    Raises:
        DirectoryExistsError: If the working directory already exists and force_delete is not set to True.
    """
    dirs = get_dirs(body.project_number, Path(body.main_dir))
    workdir_path = dirs.project_dir

    if workdir_path.exists() and not body.force_delete:
        msg = f"Directory {workdir_path} already exists. Use 'force_delete=True' to overwrite."
        logger.error(msg)
        raise DirectoryExistsError(msg)

    dirs.delete_dir(workdir_path)
    dirs.make_dirs()

    db = get_db(schema_name=body.project_number, db_file=dirs.db_path)
    db.create_database()
    db.drop_schema(body.project_number)
    db.create_schema()

    logger.debug(f'Initialized working directory and database for project {body.project_number} at {workdir_path}')


def _ensure_dataset_read_access(body: SetupForm) -> None:
    try:
        check_ds_read_access(body.pid, str(body.base_url), str(body.api_token or ''))
    except DatasetUnauthorizedError as exc:
        logger.error(f'Unauthorized access for dataset {body.pid}: {exc}')
        raise
    except DatasetNotFoundError as exc:
        logger.error(f'Dataset not found {body.pid}: {exc}')
        raise
    except DatasetAccessError as exc:
        logger.error(f'Dataset access error for {body.pid}: {exc}')
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
    dirs = get_dirs(body.project_number, Path(body.main_dir))

    await asyncio.to_thread(_ensure_dataset_read_access, body)

    downloader = Downloads.from_setup_form(body, dirs.project_dir)
    await downloader.downloader()

    logger.info(f'Downloaded dataset for PID {body.pid} to {dirs.project_dir}')


def check_curation(body: SetupForm) -> None:
    """Runs the checks for the curation process.

    Args:
        body (SetupForm): The setup form containing the necessary information for running the checks.
    """
    dirs = get_dirs(body.project_number, Path(body.main_dir), res_dir=Path(body.res_dir))
    db = get_db(schema_name=dirs.project_number, db_file=dirs.db_path)
    httpx_client = HTTPXClient(str(body.base_url), str(body.api_token))
    dv_api_calls = DVAPICalls(httpx_client=httpx_client)

    res_dir = Path(body.res_dir) if body.res_dir else None

    try:
        # Get the checklist content
        checklist_content = get_checklist_content(body.checklist, res_dir)

        # Read the dataset metadata and dataverse tree from the downloaded files
        with Path(dirs.metadata_dir, 'ds_metadata.json').open('rb') as f:
            ds_metadata = orjson.loads(f.read())

        # Read the dataverse tree file
        with Path(dirs.metadata_dir, 'dv_tree.json').open('rb') as f:
            dv_tree = orjson.loads(f.read())

        dataset_search_result = dv_api_calls.search_dataset_by_version_id(
            ds_metadata.get('data', {}).get('latestVersion', {}).get('id')
        )

        dataset_identifier = DatasetTreeInfo.get_dataset_identifier_from_search_result(dataset_search_result)

        tree_info = DatasetTreeInfo(dv_tree=dv_tree).get_ds_tree_info(dataset_identifier)

        dataset_path = DatasetTreeInfo.get_ds_path(tree_info, get_ds_title(ds_metadata))

        checker = Checker(
            ds_metadata=ds_metadata,
            dv_tree=dv_tree,
            workdir=dirs.project_dir,
            db_instance=db,
            setup_form_instance=body,
        )

        # Setup writes — before checks run
        write_project_metadata_to_db(db, checker, dataset_path)
        write_checklist_metadata_to_db(db, checklist_content)
        write_checklist_items_to_db(db, checklist_content)

        checker.run_checks()
        logger.info('Checks completed')
    except Exception as exc:
        db.drop_schema(body.project_number)
        dirs.delete_dir(dirs.project_dir)
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
