"""The backend API for running the curation review tool."""

from pathlib import Path

import orjson
from fastapi import APIRouter
from fastapi import HTTPException
from loguru import logger

from pydatacuration.backend.setup_form import SetupForm
from pydatacuration.checker import Checker
from pydatacuration.db import DatabaseBackend
from pydatacuration.db import get_database
from pydatacuration.downloads import Downloads
from pydatacuration.utils import directory_manager
from pydatacuration.utils.utils import check_ds_read_access


def get_dirs(ticket_number: str, main_dir: Path) -> directory_manager.DirectoryManager:
    """Build directory manager for a ticket.

    Args:
        ticket_number (str): Ticket identifier.
        main_dir (Path): Root working directory.

    Returns:
        directory_manager.DirectoryManager: Configured directory manager.
    """
    return directory_manager.DirectoryManager(ticket_number, str(main_dir))


def get_db(schema_name: str, db_file: Path) -> DatabaseBackend:
    """Instantiate database backend via factory.

    Args:
        schema_name (str): Schema (ticket) name.
        db_file (Path): DB file path (used by DuckDB backend only).

    Returns:
        DatabaseBackend: Backend instance.
    """
    return get_database(schema_name=schema_name, db_file=db_file)


router = APIRouter()


@router.post('/init')
def init(body: SetupForm) -> None:
    """Initialize working directory and database for a ticket.

    Args:
        body (SetupForm): The pydantic model containing initialization parameters.

    """
    dirs: directory_manager.DirectoryManager = get_dirs(body.ticket_number, Path(body.main_dir))

    workdir_path = dirs.project_dir

    if workdir_path.exists() and not body.force_delete:
        error_message = f"Directory {workdir_path} already exists. Use 'force_del=True' to overwrite."
        raise HTTPException(status_code=409, detail=error_message)

    dirs.delete_dir(workdir_path)
    dirs.make_dirs()

    db = get_db(schema_name=body.ticket_number, db_file=dirs.db_path)
    db.create_database()
    db.drop_schema(body.ticket_number)
    db.create_schema()

    logger.debug(f'Initialized working directory and database for ticket {body.ticket_number} at {workdir_path}')


@router.post('/fetch')
async def fetch(body: SetupForm) -> None:
    """Download dataset files and metadata.

    Args:
        body (SetupForm): Request body containing pid, base_url, api_token,
            ticket_number, and main_dir.

    Returns:
        None: Saves files and metadata to working dir.
    """
    dirs = get_dirs(body.ticket_number, Path(body.main_dir))
    # add_cli_run_logging(dirs.log_files_dir) # FIXME: add back the logging later once the API is fully implemented

    try:
        check_ds_read_access(
            body.pid, str(body.base_url), body.api_token or ''
        )  # TODO: fix the business logic and make this compatible with the new API design

    except HTTPException as http_exc:
        logger.error(f'HTTP error during access check for dataset {body.pid}: {http_exc.detail}')
        raise HTTPException(status_code=http_exc.status_code, detail=http_exc.detail) from http_exc

    except Exception as e:
        error_message: str = f'Failed to access dataset {body.pid}. Error: {e}'
        logger.error(error_message)
        raise HTTPException(status_code=503, detail=error_message) from e

    await Downloads(
        str(body.base_url), body.api_token or '', body.pid, dirs.project_dir, body.ticket_number
    ).downloader()

    logger.info(f'Downloaded dataset for PID {body.pid} to {dirs.project_dir}')


@router.post('/check')
def check(body: SetupForm) -> None:
    """Run curation checks on the dataset.

    Args:
        body (SetupForm): Request body containing pid, base_url, api_token,
            ticket_number, main_dir, and checklist.

    """
    dirs: directory_manager.DirectoryManager = get_dirs(body.ticket_number, Path(body.main_dir))
    db = get_db(schema_name=dirs.ticket_number, db_file=dirs.db_path)

    # Get the dataset metadata dir
    # TODO: maybe refactor to avoid re-reading from disk
    with Path(dirs.metadata_dir, 'ds_metadata.json').open('rb') as f:
        ds_metadata = orjson.loads(f.read())

    # Get the dv_tree metadata
    # TODO: maybe refactor to avoid re-reading from disk
    with Path(dirs.metadata_dir, 'dv_tree.json').open('rb') as f:
        dv_tree = orjson.loads(f.read())

    checker = Checker(
        base_url=str(body.base_url),
        api_token=body.api_token or '',
        ds_metadata=ds_metadata,
        dv_tree=dv_tree,
        workdir=dirs.project_dir,
        check_zip=body.check_zip,
        db_instance=db,
        collection_alias=body.collection_alias,
        curator_name=body.curator_name,
        curator_email=body.curator_email,
        checklist_type=body.checklist,
    )
    checker.run_checks()
    logger.info('Checks completed')


# @router.post('/report')
# def report() -> None:
#     pass
#     # TODO: this api endpoint might not be necessary. Might just keep it in the CLI for now


@router.get('/health')
def health_check() -> dict:
    """Health check endpoint to verify API is running."""
    return {'status': 'ok'}
