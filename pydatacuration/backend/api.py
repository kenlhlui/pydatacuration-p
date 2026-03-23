"""The backend API for running the curation review tool."""

from pathlib import Path

import orjson
from fastapi import APIRouter
from fastapi import HTTPException
from loguru import logger

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
def init(ticket_number: str, force_del: bool, main_dir: Path) -> None:
    """Initialize working directory and database for a ticket."""
    # TODO: Add back the args docstring
    dirs: directory_manager.DirectoryManager = get_dirs(ticket_number, main_dir)

    workdir_path = dirs.project_dir

    if workdir_path.exists() and not force_del:
        error_message = f"Directory {workdir_path} already exists. Use 'force_del=True' to overwrite."
        raise HTTPException(status_code=409, detail=error_message)

    dirs.delete_dir(workdir_path)
    dirs.make_dirs()

    db = get_db(schema_name=ticket_number, db_file=dirs.db_path)
    db.create_database()
    db.drop_schema(ticket_number)
    db.create_schema()

    logger.debug(f'Initialized working directory and database for ticket {ticket_number} at {workdir_path}')


@router.post('/fetch')
async def fetch(pid: str, base_url: str, api_token: str, ticket_number: str, main_dir: Path) -> None:
    """Download dataset files and metadata.

    Args:
        pid (str): Dataverse PID.
        base_url (str): Dataverse base URL.
        api_token (str): Dataverse API token.
        ticket_number (str): Ticket identifier.
        main_dir (Path): Root working directory.

    Returns:
        None: Saves files and metadata to working dir.
    """
    dirs = get_dirs(ticket_number, main_dir)
    # add_cli_run_logging(dirs.log_files_dir) # FIXME: add back the logging later once the API is fully implemented

    try:
        check_ds_read_access(
            pid, base_url, api_token
        )  # TODO: fix the business logic and make this compatible with the new API design

    except HTTPException as http_exc:
        logger.error(f'HTTP error during access check for dataset {pid}: {http_exc.detail}')
        raise HTTPException(status_code=http_exc.status_code, detail=http_exc.detail) from http_exc

    except Exception as e:
        error_message: str = f'Failed to access dataset {pid}. Error: {e}'
        logger.error(error_message)
        raise HTTPException(status_code=503, detail=error_message) from e

    await Downloads(base_url, api_token, pid, dirs.project_dir, ticket_number).downloader()

    logger.info(f'Downloaded dataset for PID {pid} to {dirs.project_dir}')


@router.post('/check')
def check(
    ticket_number: str,
    base_url: str,
    api_token: str,
    check_zip: bool,
    collection_alias: str | None,
    curator_name: str | None,
    curator_email: str | None,
    checklist: str,
    main_dir: Path,
) -> None:
    dirs: directory_manager.DirectoryManager = get_dirs(ticket_number, main_dir)
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
        base_url=base_url,
        api_token=api_token,
        ds_metadata=ds_metadata,
        dv_tree=dv_tree,
        workdir=dirs.project_dir,
        check_zip=check_zip,
        db_instance=db,
        collection_alias=collection_alias,
        curator_name=curator_name,
        curator_email=curator_email,
        checklist_type=checklist,
    )
    checker.run_checks()
    logger.info('Checks completed')


@router.post('/report')
def report() -> None:
    pass
    # TODO: this api endpoint might not be necessary. Might just keep it in the CLI for now
