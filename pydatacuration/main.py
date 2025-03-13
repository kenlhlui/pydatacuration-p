"""The main module of the pydatacuration CLI application."""
# ruff: noqa: E501, W505
import asyncio
from pathlib import Path

import directory_manager
import downloads
import log_generation
import orjson
import typer
import utils
from checker import Checker
from custom_logging import CustomLogger
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv(override=True)

app = typer.Typer()


@app.command()
def main(

    doi: str = typer.Option(None,
                            prompt=('Input the Dataset Persistent Identifier (doi or hdl)'),
                            help='Enter the Persistent Identifier of the dataset'),
    base_url: str = typer.Option(None,
                                 help='The base URL of the Dataverse installation',
                                 prompt=('Input the base URL of the Dataverse installation'),
                                 prompt_required=True,
                                 envvar='BASE_URL'),
    api_token: str = typer.Option(None,
                                  help='The API token for the Dataverse installation',
                                  prompt=('Input the API token for the Dataverse installation'),
                                  hide_input=True,
                                  prompt_required=True,
                                  envvar='API_TOKEN'),
    parent_dir: str = typer.Option('workdir',
                                help='The working directory. If not specified, a directory "workdir" will be created in the current directory',
                                show_default=True,
                                ),
    ticket_number: str = typer.Option(None,
                                      help='The ticket number for the curation report; Also the directory name created under the working directory',
                                      prompt=('Input the ticket number for the curation report'),
                                      prompt_required=True,
                                      callback=utils.check_ticket_num_input,
                                      )) -> None:
    """This script downloads the dataset files and metadata from a Dataverse instance and checks the files and metadata for data curation, and generates a curation report in spreadsheet (.xlsx) and world (.docx) format."""  # noqa: E501, W505
    # Set up the directory structure
    workdir_path, log_files_dir, ds_dir, temp_data_dir = directory_manager.DirectoryManager(ticket_number, parent_dir).make_dirs()

    # Initialize the custom logger in the cli
    logger = CustomLogger.get_logger('main')

    # print the start message
    logger.print('Starting the pydatacuration script...')

    # Download the dataset files and metadata
    ds_metadata = asyncio.run(downloads.Downloads(base_url, api_token, doi, workdir_path).downloader())

    # Run the checker
    checker = Checker(base_url, api_token, ds_metadata, workdir_path)
    template_dict = checker.run_checks()

    # Generate the report
    generate_log = log_generation.GenerateLog(workdir_path, base_url, ds_metadata, ticket_number)
    generate_log.generate_report_xlsx(template_dict)
    generate_log.generate_report_doc(template_dict)
    generate_log.generate_project_metadata()

    # Export the template dict to JSON for debugging purposes
    with temp_data_dir.joinpath('template_dict.json').open('w') as f:
        f.write(orjson.dumps(template_dict, option=orjson.OPT_INDENT_2).decode())

    # Generate the tree diagram of the dataset files
    utils.gen_tree_diagram(Path(workdir_path, 'dataset', 'files'), Path(log_files_dir))

    # Print the end message
    logger.print(f'✅ Curation report generated successfully. \n\nType (or copy) the following (without quotes) in the terminal to view the files: \n\n`explorer.exe {workdir_path}`')


if __name__ == '__main__':
    app()
