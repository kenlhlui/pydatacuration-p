"""This module contains utility functions for data curation tasks."""

import os
import re
import shutil
import sys
from pathlib import Path
from pathlib import PurePosixPath

import deepdiff
import orjson
import seedir as sd
import typer
from tenacity import RetryError

from .custom_logging import CustomLogger
from .httpx_client import HTTPXClient


# Initialize the logger
logger = CustomLogger.get_logger(__name__)


class FileNameFormatChecker:
    """This class is used to check the file name format."""

    def __init__(self) -> None:
        """Initialize the class."""

    @staticmethod
    def check_special_char(file: str) -> tuple:
        r"""Check if the file name contains special characters.

        <>:"/\|?* `CR` `LF` are absolutely forbidden in file names.

        , @ $ ~ are not recommended.

        See https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file for more details.

        Args:
            file (str): The path to the file.

        Returns:
            tuple: The file path and a boolean value.
        """
        if re.search(r'[<>:"/\\|?*,@$~\r\n]', Path(file).stem):
            return file, True
        return file, False

    @staticmethod
    def check_file_name_len(file: str, file_name_max_len: int) -> tuple:
        """Check if the file name is longer than the maximum length.

        Args:
            file (str): The path to the file.
            file_name_max_len (int): The maximum length of the file name.

        Returns:
            tuple: The file path and a boolean value.
        """
        if len(Path(file).stem) > file_name_max_len:
            return file, True
        return file, False

    @staticmethod
    def check_file_ext(file: str) -> tuple:
        """Check if the file has an extension.

        Args:
            file (str): The path to the file.

        Returns:
            tuple: The file path and a boolean value.
        """
        if Path(file).suffix:
            return file, False  # TODO: unify the logic for returns
        return file, True

    @staticmethod
    def check_file_preferred_format(file: str, preferred_file_formats_config: str) -> tuple:
        """Check if the file format is in the preferred file formats list.

        Args:
            file (str): The path to the file.
            preferred_file_formats_config (str): The path to the configuration .txt file.

        Returns:
            tuple: The file path and a boolean value.
        """

        def load_preferred_file_formats_list(preferred_file_formats_config: str) -> list:
            """Load the list of preferred file formats from the configuration .txt file.

            Args:
                file (str): The path to the text file.
                preferred_file_formats_config (str): The path to the configuration .txt file.

            Returns:
                list: A list of lines in the text file without newline characters.
            """
            try:
                with Path(preferred_file_formats_config).open(encoding='utf-8') as f:
                    return [line.strip() for line in f.readlines()]
            except FileNotFoundError as e:
                logger.print(f'Error: {e}')
                sys.exit(1)

        if Path(file).suffix in load_preferred_file_formats_list(preferred_file_formats_config):
            return file, True
        return file, False


def readme_file_checker(file: str) -> tuple:
    """Check if the file is a README file.

    Args:
        file (str): The path to the file.

    Returns:
        tuple: The file path and a boolean value.
    """
    if re.search(r'readme', file, re.IGNORECASE):
        return file, True
    return file, False


def compare_files_and_metadata(dl_files_checksums: list, metadata_file_checksums: list, work_dir: Path) -> None | bool:
    """Compare the downloaded files checksums and the metadata JSON file checksums.

    Args:
        dl_files_checksums (list): A list of dictionaries containing the file path and the checksum.
        metadata_file_checksums (list): A list of dictionaries containing the file path and the checksum.
        work_dir (Path): The working directory.

    Returns:
        bool: True if the downloaded files and the metadata JSON file checksums are the same, False otherwise.
    """
    diff = deepdiff.DeepDiff(dl_files_checksums, metadata_file_checksums, ignore_order=True)
    if diff:
        logger.warning('The downloaded files and the file list metadata are different.')
        diff_log_path = Path(work_dir, 'log_files', 'diff.txt').resolve()
        with diff_log_path.open('w', encoding='utf-8') as f:
            f.write(str(diff))
        logger.warning(f'See the {str(diff_log_path)} file for the differences.')
        sys.exit(1)

    else:
        logger.print('The downloaded files and the file list metadata are the same.')
        return False


def gen_tree_diagram(target_dir: Path, save_dir: Path) -> None:
    """Generate the tree diagram of the directory.

    Args:
        target_dir (Path): The directory path to the target directory.
        save_dir (Path): The directory path to save the tree diagram text (.txt) file`.
    """
    try:
        if Path.exists(target_dir):
            result = sd.seedir(target_dir, style='lines', printout=False, first='files')

            if result:
                ds_tree_file_path = Path(save_dir, 'ds_tree.txt')
                with Path(ds_tree_file_path).open('w', encoding='utf-8') as f:
                    f.write(result)

                logger.print(f'Folder tree diagram text file saved at: {str(ds_tree_file_path)}')
        else:
            logger.print('The target directory does not exist. Exiting...')
            sys.exit(1)

    except Exception as e:
        logger.print(f'Error: {e}')
        logger.print('An error occurred while generating the folder tree diagram. Exiting...')
        sys.exit(1)


def parse_file_list_metadata(file_list_metadata: list) -> list:
    """Parse the file list metadata.

    Args:
        file_list_metadata (list): The list of file metadata.

    Returns:
        list: The parsed file list metadata.
    """
    file_list_metadata_nested_list = []
    for file_meta in file_list_metadata:
        filename = file_meta.get('dataFile', {}).get('originalFileName') or file_meta.get('dataFile', {}).get(
            'filename'
        )  # noqa: E501
        directory_label = file_meta.get('directoryLabel', '')
        file_full_path_obj = Path(directory_label, filename)
        file_list_metadata_nested_list.append(
            {'file': str(PurePosixPath(file_full_path_obj)), 'md5_checksum': file_meta['dataFile']['md5']}
        )

    return file_list_metadata_nested_list


def check_ticket_num_input(ticket_num: str) -> str:
    """Check if the ticket number is without any special characters or spaces.

    Args:
        ticket_num (str): The ticket number to check.

    Returns:
        str: The validated ticket number.
    """
    # Check if the ticket number is empty
    if not ticket_num:
        msg = 'Ticket number cannot be empty.'
        raise typer.BadParameter(msg)

    # Check if the ticket number contains any special characters or spaces
    if re.search(r'[^a-zA-Z0-9_\-]', ticket_num):
        msg = '⚠️ Ticket number must only contain letters, numbers, hyphens, and underscores.'
        raise typer.BadParameter(msg)

    return ticket_num


def confirm_del_dir(dir_path: Path, default: bool = False) -> None:
    """Delete a directory after seeking user confirmation.

    Args:
        dir_path (Path): Path to the directory to delete
        default (bool): If True, delete without confirmation; otherwise ask user
    """
    if dir_path.exists():
        try:
            if default or typer.confirm(
                f'Do you want to replace {dir_path} with the new files?',
                default=False,
                abort=True,
            ):
                shutil.rmtree(dir_path)
                typer.echo(f'Will Replace {dir_path} with the new files.')
        except typer.Abort:
            typer.echo('Aborted by user. Exiting...')
            sys.exit(1)


def check_ds_access(pid: str, base_url: str, api_token: str) -> None:
    """Check if the API token is valid; the PID is valid; and the user has access to the dataset.

    Args:
        pid (str): The PID of the dataset.
        base_url (str): The base URL of the Dataverse installation.
        api_token: The API token for the Dataverse installation.
    """
    httpx_client = HTTPXClient(base_url, api_token)

    http_success_codes = {200, 201, 202, 204}
    http_unauthorized_codes = {401, 403}
    http_not_found_codes = {404}

    try:
        # Check whether the user has access to the dataset
        response = httpx_client.sync_get(f'api/datasets/:persistentId/?persistentId={pid}', raise_for_status=False)
        httpx_client.logger.debug(f'{response.status_code} {response.text}')

        if response.status_code in http_unauthorized_codes:
            httpx_client.logger.error(
                '❌You do not have access to the dataset. \nPlease check your API token or permissions.'
            )  # noqa: E501

            sys.exit(1)
        elif response.status_code in http_not_found_codes:
            httpx_client.logger.error('❌The dataset does not exist. Please check the PID input.')
            sys.exit(1)
        elif response.status_code in http_success_codes:
            httpx_client.logger.print('✅ Access to the dataset checked successfully.')

    except RetryError:
        logger.error(
            'The retry limit has been reached for checking dataset access. \nCheck your input of `base_url` and `pid`. Or check your internet connection.'
        )  # noqa: E501
        sys.exit(1)


def validate_api_token(value: str) -> str | None:
    """Validate API token to prevent empty strings from overriding environment values."""
    if value == '' and os.getenv('API_TOKEN'):
        return os.getenv('API_TOKEN')
    return value


def orjson_export(file_path: Path | str, obj: dict) -> None:
    """Export a dictionary to a JSON file using orjson.

    Args:
        file_path (Path | str): The path to the JSON file.
        obj (dict): The dictionary to export.
    """
    try:
        with Path(file_path).open('wb') as f:
            f.write(orjson.dumps(obj, option=orjson.OPT_INDENT_2))
    except Exception as e:
        logger.error(f'Error exporting JSON: {e}')
        raise e
