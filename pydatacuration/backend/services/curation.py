import asyncio
from pathlib import Path

import orjson
from fastapi import HTTPException
from loguru import logger

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.checker import Checker
from pydatacuration.db import DatabaseBackend
from pydatacuration.db import get_database
from pydatacuration.downloads import Downloads
from pydatacuration.utils import directory_manager
from pydatacuration.utils.utils import check_ds_read_access


def get_dirs(ticket_number: str, main_dir: Path) -> directory_manager.DirectoryManager:
    return directory_manager.DirectoryManager(ticket_number, str(main_dir))


def get_db(schema_name: str, db_file: Path) -> DatabaseBackend:
    return get_database(schema_name=schema_name, db_file=db_file)


def init_curation(body: SetupForm) -> None:
    dirs = get_dirs(body.ticket_number, Path(body.main_dir))
    workdir_path = dirs.project_dir

    if workdir_path.exists() and not body.force_delete:
        raise HTTPException(
            status_code=409,
            detail=f"Directory {workdir_path} already exists. Use 'force_del=True' to overwrite.",
        )

    dirs.delete_dir(workdir_path)
    dirs.make_dirs()

    db = get_db(schema_name=body.ticket_number, db_file=dirs.db_path)
    db.create_database()
    db.drop_schema(body.ticket_number)
    db.create_schema()

    logger.debug(f'Initialized working directory and database for ticket {body.ticket_number} at {workdir_path}')


async def fetch_curation(body: SetupForm) -> None:
    dirs = get_dirs(body.ticket_number, Path(body.main_dir))

    try:
        check_ds_read_access(body.pid, str(body.base_url), body.api_token or '')
    except HTTPException as http_exc:
        logger.error(f'HTTP error during access check for dataset {body.pid}: {http_exc.detail}')
        raise
    except Exception as exc:
        error_message = f'Failed to access dataset {body.pid}. Error: {exc}'
        logger.error(error_message)
        raise HTTPException(status_code=503, detail=error_message) from exc

    await Downloads(
        str(body.base_url),
        body.api_token or '',
        body.pid,
        dirs.project_dir,
        body.ticket_number,
    ).downloader()

    logger.info(f'Downloaded dataset for PID {body.pid} to {dirs.project_dir}')


def check_curation(body: SetupForm) -> None:
    dirs = get_dirs(body.ticket_number, Path(body.main_dir))
    db = get_db(schema_name=dirs.ticket_number, db_file=dirs.db_path)

    with Path(dirs.metadata_dir, 'ds_metadata.json').open('rb') as f:
        ds_metadata = orjson.loads(f.read())

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


async def run_curation(body: SetupForm) -> None:
    await asyncio.to_thread(init_curation, body)
    await fetch_curation(body)
    await asyncio.to_thread(check_curation, body)
