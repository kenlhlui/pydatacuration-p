#!/usr/bin/env python3
"""CLI entrypoint for pydatacuration."""

import asyncio
import os
import subprocess
from pathlib import Path

import orjson
import typer
from dotenv import load_dotenv
from rich.progress import Progress
from rich.progress import SpinnerColumn
from trogon.typer import init_tui

from . import directory_manager
from . import downloads
from . import duck_db
from . import utils
from .checker import Checker
from .custom_logging import add_cli_run_logging
from .custom_logging import logger
from .custom_logging import setup_global_logging


load_dotenv(override=True)

app = typer.Typer(rich_markup_mode='rich')


class TyperOptions:
    """Helper class for Typer options with types and defaults."""

    api_token_option = typer.Option(
        ...,
        '--api-token',
        '-a',
        help='Dataverse API token',
        prompt='Input the API token for the Dataverse',
        hide_input=True,
        callback=utils.validate_api_token,
    )

    ticket_number_option: str = typer.Option(
        ...,
        '--ticket-number',
        '-t',
        help='Ticket number (also used as schema and folder name)',
        prompt='Input the ticket number for the curation report',
        callback=utils.check_ticket_num_input,
    )

    base_url_option: str = typer.Option(
        ...,
        '--base-url',
        '-b',
        envvar='BASE_URL',
        prompt='Input the base URL of the Dataverse installation',
        help='Dataverse base URL',
    )

    force_del_option: bool = typer.Option(
        False,
        '--force-del/--no-force-del',
        '-f/-nf',
        help='Delete existing working directory and DB schema if present',
        show_default=True,
    )

    pid_option: str = typer.Option(
        ...,
        '--pid',
        '-p',
        prompt='Input the Dataset Persistent Identifier (doi or hdl)',
        help='Dataset Persistent Identifier',
    )
    curator_name_option: str = typer.Option(None, '--curator-name', '-cn', help='Curator name')

    curator_email_option: str = typer.Option(None, '--curator-email', '-ce', help='Curator email')

    open_dir_option: bool = typer.Option(True, '--open-dir/--no-open-dir', help='Open working directory in Explorer')

    check_zip_option: bool = typer.Option(True, '--check-zip/--no-check-zip', '-z/-nz')

    collection_alias_option: str | None = typer.Option(None, '--collection-alias', '-c')


class CtxObj:
    """Lightweight context object for sharing state across commands."""

    def __init__(self, main_dir: Path) -> None:
        """Initialize with main working directory and env vars."""
        self.main_dir = main_dir
        env_dict = {k: v for k, v in os.environ.items()}


@app.callback()
def main(
    ctx: typer.Context,
    main_dir: Path = typer.Option(
        Path(os.getenv('MAIN_DIR', 'workdir')).resolve(),
        '--main-dir',
        help='Top-level working directory for all runs',
        show_default=True,
    ),
) -> None:
    """Initialize shared context.

    Args:
        ctx (typer.Context): Typer context.
        main_dir (Path): Root working directory.

    Returns:
        None: Sets ctx.obj with shared state.
    """
    ctx.obj = CtxObj(main_dir=main_dir)
    setup_global_logging(log_file_dir=Path(main_dir, 'logs'), log_level='DEBUG')


def get_dirs(ticket_number: str, main_dir: Path) -> directory_manager.DirectoryManager:
    """Build directory manager for a ticket.

    Args:
        ticket_number (str): Ticket identifier.
        main_dir (Path): Root working directory.

    Returns:
        directory_manager.DirectoryManager: Configured directory manager.
    """
    return directory_manager.DirectoryManager(ticket_number, str(main_dir))


def get_duck(schema_name: str, db_file: Path) -> duck_db.DuckDB:
    """Instantiate DuckDB wrapper.

    Args:
        schema_name (str): Schema (ticket) name.
        db_file (Path): DB file path.

    Returns:
        duck_db.DuckDB: DuckDB instance.
    """
    return duck_db.DuckDB(schema_name=schema_name, db_file=db_file)


@app.command()
def init(
    ctx: typer.Context,
    ticket_number: str = TyperOptions.ticket_number_option,
    force_del: bool = TyperOptions.force_del_option,
) -> None:
    """Prepare working directory and DuckDB schema.

    Args:
        ctx (typer.Context): Typer context (provides main_dir).
        ticket_number (str): Ticket identifier.
        force_del (bool): Force cleanup if existing.

    Returns:
        None: Creates dirs and initializes schema.
    """
    dirs: directory_manager.DirectoryManager = get_dirs(ticket_number, ctx.obj.main_dir)
    workdir_path = dirs.project_dir

    if workdir_path.exists() and not force_del:
        logger.error(f'Working directory {workdir_path} already exists. Use --force-del to overwrite.')
        raise typer.Exit(code=1)

    dirs.delete_dir(workdir_path)
    dirs.make_dirs()
    add_cli_run_logging(dirs.log_files_dir)

    duck = get_duck(schema_name=dirs.ticket_number, db_file=dirs.db_path)
    duck.create_database()
    duck.sql_drop_schema(ticket_number)
    duck.create_schema()
    logger.info(f'Initialized working area at {workdir_path}')


@app.command()
def fetch(
    ctx: typer.Context,
    pid: str = TyperOptions.pid_option,
    base_url: str = TyperOptions.base_url_option,
    api_token: str = TyperOptions.api_token_option,
    ticket_number: str = TyperOptions.ticket_number_option,
) -> None:
    """Download dataset files and metadata.

    Args:
        ctx (typer.Context): Typer context.
        pid (str): Dataverse PID.
        base_url (str): Dataverse base URL.
        api_token (str): Dataverse API token.
        ticket_number (str): Ticket identifier.

    Returns:
        None: Saves files and metadata to working dir.
    """
    dirs = get_dirs(ticket_number, ctx.obj.main_dir)

    add_cli_run_logging(dirs.log_files_dir)
    with Progress(SpinnerColumn(), expand=True) as progress:
        progress.add_task('Checking dataset access...', total=None, visible=True)
        utils.check_ds_access(pid, base_url, api_token)

        progress.add_task('Downloading dataset...', total=None, visible=True)
        ds_metadata, dv_tree = asyncio.run(
            downloads.Downloads(base_url, api_token, pid, dirs.project_dir, ticket_number).downloader()
        )

    # Cache metadata for later stages if you persist it (e.g., JSON in logs dir)
    logger.info(f'Downloaded dataset for PID {pid} to {dirs.project_dir}')


@app.command()
def check(
    ctx: typer.Context,
    ticket_number: str = TyperOptions.ticket_number_option,
    base_url: str = TyperOptions.base_url_option,
    api_token: str = TyperOptions.api_token_option,
    check_zip: bool = typer.Option(
        True,
        '--check-zip/--no-check-zip',
        '-z/-nz',
        help='Unzip archives and inspect their contents',
        show_default=True,
    ),
    collection_alias: str | None = typer.Option(None, '--collection-alias', '-c', help='Collection alias to search'),
) -> None:
    """Run curation checks on downloaded files/metadata.

    Args:
        ctx (typer.Context): Typer context.
        ticket_number (str): Ticket identifier.
        base_url (str | None): Base URL (optional if already embedded in downloaded metadata).
        api_token (str | None): API token (optional if not needed at this stage).
        check_zip (bool): Whether to unzip and inspect archives.
        collection_alias (str | None): Collection alias filter.

    Returns:
        None: Writes check results to DuckDB and logs.
    """
    dirs: directory_manager.DirectoryManager = get_dirs(ticket_number, ctx.obj.main_dir)
    duck = get_duck(schema_name=dirs.ticket_number, db_file=dirs.db_path)

    add_cli_run_logging(dirs.log_files_dir)

    # Get the dataset metadata dir
    with Path(dirs.metadata_dir, 'ds_metadata.json').open('rb') as f:
        ds_metadata = orjson.loads(f.read())

    # FIXME: PLACEHOLDER
    dv_tree = {}
    checker = Checker(
        base_url,
        api_token,
        ds_metadata,
        dv_tree,
        dirs.project_dir,
        check_zip,
        duck,
        collection_alias,
    )
    checker.run_checks()
    logger.info('Checks completed')


@app.command()
def report(
    ctx: typer.Context,
    ticket_number: str = TyperOptions.ticket_number_option,
    curator_name: str | None = TyperOptions.curator_name_option,
    curator_email: str | None = TyperOptions.curator_email_option,
    open_dir: bool = TyperOptions.open_dir_option,
) -> None:
    """Generate artifacts (tree diagram, spreadsheets/docs) and optionally open the folder.

    Args:
        ctx (typer.Context): Typer context.
        ticket_number (str): Ticket identifier.
        curator_name (str | None): Curator name for report.
        curator_email (EmailStr | None): Curator email for report.
        open_dir (bool): Whether to open the output folder.

    Returns:
        None: Produces report artifacts.
    """
    dirs = get_dirs(ticket_number, ctx.obj.main_dir)

    add_cli_run_logging(dirs.log_files_dir)

    utils.gen_tree_diagram(Path(dirs.project_dir, 'dataset', 'files'), Path(dirs.log_files_dir))

    logger.info('✅ Curation report generated successfully.')
    logger.info(f'If Explorer did not open automatically, run:\n\nexplorer.exe "$(wslpath -w {dirs.project_dir})"')

    if open_dir:
        subprocess.run([f'explorer.exe "$(wslpath -w {dirs.project_dir})"'], shell=True, check=False)


@app.command('all')
def run_all(
    ctx: typer.Context,
    pid: str = TyperOptions.pid_option,
    base_url: str = TyperOptions.base_url_option,
    api_token: str = TyperOptions.api_token_option,
    ticket_number: str = TyperOptions.ticket_number_option,
    force_del: bool = TyperOptions.force_del_option,
    check_zip: bool = TyperOptions.check_zip_option,
    collection_alias: str | None = TyperOptions.collection_alias_option,
    curator_name: str = TyperOptions.curator_name_option,
    curator_email: str = TyperOptions.curator_email_option,
    open_dir: bool = TyperOptions.open_dir_option,
) -> None:
    """Run the full pipeline: init ➜ fetch ➜ check ➜ report.

    Args:
        ctx (typer.Context): Typer context.
        pid (str): Dataset PID.
        base_url (str): Dataverse base URL.
        api_token (str): Dataverse API token.
        ticket_number (str): Ticket identifier.
        force_del (bool): Whether to clear existing outputs.
        check_zip (bool): Inspect archive contents.
        collection_alias (str | None): Collection alias filter.
        curator_name (str | None): Curator name.
        curator_email (str | None): Curator email.
        open_dir (bool): Open output folder.

    Returns:
        None: Executes all stages.
    """
    # init.callback = None  # silence "unused" warnings if imported as module
    init(ctx, ticket_number=ticket_number, force_del=force_del)
    fetch(ctx, pid=pid, base_url=base_url, api_token=api_token, ticket_number=ticket_number)
    check(
        ctx,
        ticket_number=ticket_number,
        base_url=base_url,
        api_token=api_token,
        check_zip=check_zip,
        collection_alias=collection_alias,
    )
    report(ctx, ticket_number=ticket_number, curator_name=curator_name, curator_email=curator_email, open_dir=open_dir)


init_tui(app)

if __name__ == '__main__':
    app()
