#!/usr/bin/env python3
"""The main module of the pydatacuration CLI application."""
# ruff: noqa: E501, W505
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
from . import log_generation
from . import utils
from .checker import Checker
from .custom_logging import CustomLogger
from .utils import orjson_export


# Load environment variables from .env file
load_dotenv(override=True)

app = typer.Typer(rich_markup_mode='rich')
init_tui(app)


@app.command()
def cli(
    pid: str = typer.Option(...,
                            '--pid',
                            '-p',
                            prompt=('Input the Dataset Persistent Identifier (doi or hdl)'),
                            help='Enter the Persistent Identifier of the dataset'),
    base_url: str = typer.Option(None,
                                 '--base-url',
                                 '-b',
                                 help=f'The base URL of the Dataverse installation (current value: [bold yellow]{os.getenv("BASE_URL", "None")}[/bold yellow])',
                                 prompt=('Input the base URL of the Dataverse installation'),
                                 prompt_required=True,
                                 envvar='BASE_URL'),
    api_token: str = typer.Option(None,
                                  '--api-token',
                                  '-a',
                                  help=f'The API token for the Dataverse installation (current: [bold {"green" if os.getenv("API_TOKEN") else "red"}]{"Set" if os.getenv("API_TOKEN") else "Not set"}[/bold {"green" if os.getenv("API_TOKEN") else "red"}])',
                                  prompt=('Input the API token for the Dataverse installation'),
                                  hide_input=True,
                                  prompt_required=True,
                                  envvar='API_TOKEN',
                                  callback=utils.validate_api_token),
    parent_dir: str = typer.Option('workdir',
                                   '--parent-dir',
                                   '-dir',
                                   help='The working directory. If not specified, a directory "workdir" will be created in the current directory',
                                   show_default=True,
                                   ),
    ticket_number: str = typer.Option(...,
                                      '--ticket-number',
                                      '-t',
                                      help='The ticket number for the curation report. It will also be the directory name created under the working directory',
                                      prompt=('Input the ticket number for the curation report'),
                                      prompt_required=True,
                                      callback=utils.check_ticket_num_input,
                                      ),
    force_del: bool = typer.Option(False,
                                   '--force-del/--no-force-del',
                                   '-f/-nf',
                                   help='To force replace (delete) an existing working directory, if any',
                                   show_default=True),
    check_zip: bool = typer.Option(True,
                                   '--check_zip/--no-check_zip,',
                                   '-z/-nz',
                                   help='To unzip zip files and check the content inside or not')) -> None:
    """This script downloads the dataset files and metadata from a Dataverse instance and checks the files and metadata for data curation, and generates a curation report in spreadsheet (.xlsx) and world (.docx) format."""  # noqa: E501, W505
    # Define the working directory
    workdir_path = directory_manager.DirectoryManager(ticket_number, parent_dir).define_workdir()

    # Check if the working directory already exists and ask user for confirmation to delete it
    utils.confirm_del_dir(workdir_path, force_del)

    # Create the working directory and its subdirectories
    directory_manager.DirectoryManager(ticket_number, parent_dir).make_dirs()

    # Define the log directory
    log_files_dir = directory_manager.DirectoryManager(ticket_number, parent_dir).log_files_dir

    # Initialize the custom logger in the cli
    logger = CustomLogger.get_logger('main')

    # print the start message
    logger.print('Starting the pydatacuration script...')

    # Check if the dataset PID is valid and the user has access to it
    utils.check_ds_access(pid, base_url, api_token)

    # Download the dataset files and metadata
    ds_metadata, dv_tree = asyncio.run(downloads.Downloads(base_url, api_token, pid, workdir_path, ticket_number).downloader())

    # Run the checker
    checker = Checker(base_url, api_token, ds_metadata, dv_tree, workdir_path, check_zip)
    template_dict = checker.run_checks()

    # Generate the report
    generate_log = log_generation.GenerateLog(log_files_dir, base_url, ds_metadata, ticket_number)
    # ! Disable generation of xlsx report for now
    # generate_log.generate_report_xlsx(template_dict)
    generate_log.generate_report_doc(template_dict, 'medium')  # medium-level report
    generate_log.generate_report_doc(template_dict, 'high')  # high-level report
    generate_log.generate_project_metadata()

    # Export the template dict to JSON for debugging purposes
    orjson_export(log_files_dir.joinpath('template_dict.json'), template_dict)

    # Generate the tree diagram of the dataset files
    utils.gen_tree_diagram(Path(workdir_path, 'dataset', 'files'), Path(log_files_dir))

    # Print the end message
    logger.print(f'✅ Curation report generated successfully.\n\nThe windows explorer should be popped up with the working directory opened. \n\nIf that does not work, type (or copy) the following in the terminal to view the files: \n\nexplorer.exe "$(wslpath -w {workdir_path})"')

    # Run the command to open the working directory in Windows Explorer
    subprocess.run([f'explorer.exe "$(wslpath -w {workdir_path})"'], shell=True, check=False)


if __name__ == '__main__':
    with Progress(SpinnerColumn(), expand=True) as progress:
        progress.add_task('', total=None, visible=True)
        app()
