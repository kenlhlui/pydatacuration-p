"""Utility functions."""

import os
import platform
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import urlencode
from urllib.parse import urljoin

import deepdiff
import httpx2
import orjson
import seedir as sd
import typer
from loguru import logger
from tenacity import RetryError

from pydatacuration.exceptions import DatasetAccessError
from pydatacuration.exceptions import DatasetNotFoundError
from pydatacuration.exceptions import DatasetUnauthorizedError
from pydatacuration.services.api_calls.dataverse_client import DataverseClient
from pydatacuration.services.api_calls.httpx_client import HTTPXClient
from pydatacuration.utils.search_ds_meta import get_file_name_from_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_rel_path_from_file_list_metadata


def check_readme_file_existence(file: str) -> tuple[str, bool]:
    """Check if the file is a README file.

    Args:
        file (str): The path to the file.

    Returns:
        tuple[str, bool]: The file path and a boolean value.
    """
    if re.search(r'readme', file, re.IGNORECASE):
        return file, True
    return file, False


def compare_files_and_metadata(dl_files_checksums: list, metadata_file_checksums: list, work_dir: Path) -> bool:
    """Compare the downloaded files checksums and the metadata JSON file checksums.

    Args:
        dl_files_checksums (list): A list of dictionaries containing the file path and the checksum.
        metadata_file_checksums (list): A list of dictionaries containing the file path and the checksum.
        work_dir (Path): The working directory.

    Returns:
        bool: True if the downloaded files and the metadata JSON file checksums are different, False otherwise.
    """
    diff = deepdiff.DeepDiff(dl_files_checksums, metadata_file_checksums, ignore_order=True)
    if diff:
        logger.warning('The downloaded files and the file list metadata are different.')
        diff_log_path = Path(work_dir, 'logs', 'diff.txt').resolve()
        with diff_log_path.open('w', encoding='utf-8') as f:
            f.write(str(diff))
        logger.warning(f'See the {str(diff_log_path)} file for the differences.')

    logger.info('The downloaded files and the file list metadata are the same.')
    return False


def parse_file_list_metadata(file_list_metadata: list) -> list:
    """Parse the file list metadata.

    Args:
        file_list_metadata (list): The list of file metadata.

    Returns:
        list: The parsed file list metadata.
    """
    file_list_metadata_nested_list = []
    for file_meta in file_list_metadata:
        filename = get_file_name_from_file_list_metadata(file_meta)
        file_full_path_obj = get_file_rel_path_from_file_list_metadata(file_meta, filename)
        file_list_metadata_nested_list.append({
            'file': str(PurePosixPath(file_full_path_obj)),
            'checksum': file_meta['dataFile']['md5'],
        })

    return file_list_metadata_nested_list


def check_ticket_num_input(ticket_number: str) -> str:
    """Check if the ticket number is without any special characters or spaces.

    Args:
        ticket_number (str): The ticket number to check.

    Returns:
        str: The validated ticket number (must start with an alphanumeric character).
    """
    if not ticket_number:
        msg = 'Ticket number cannot be empty.'
        raise typer.BadParameter(msg)

    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', ticket_number):
        msg = 'Ticket number must only contain letters, numbers, hyphens, and underscores.'
        raise typer.BadParameter(msg)

    return ticket_number


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

                logger.info(f'Folder tree diagram text file saved at: {str(ds_tree_file_path)}')
        else:
            logger.warning(f'Target directory does not exist: {str(target_dir)} - skipping tree diagram generation.')
            return
    except Exception as e:
        logger.error(f'An error occurred while generating the folder tree diagram: {e}')


def check_ds_read_access(pid: str, base_url: str, api_token: str) -> None:
    """Check if the API token is valid; the PID is valid; and the user has access to the dataset.

    Args:
        pid (str): The PID of the dataset.
        base_url (str): The base URL of the Dataverse installation.
        api_token: The API token for the Dataverse installation.

    Raises:
        DatasetUnauthorizedError: If the user does not have access to the dataset.
        DatasetNotFoundError: If the dataset does not exist.
        DatasetAccessError: If there are network or connection issues.
    """
    httpx_client = HTTPXClient(base_url, api_token)

    try:
        response = DataverseClient(httpx_client).get_ds_access_status(pid)

        if response.status_code in {httpx2.codes.UNAUTHORIZED, httpx2.codes.FORBIDDEN}:
            msg = 'You do not have read access to the dataset. Please check your API token or permissions.'
            logger.error(f'❌{msg}')
            raise DatasetUnauthorizedError(msg)

        if response.status_code == httpx2.codes.NOT_FOUND:
            msg = 'The dataset does not exist. Please check the PID input.'
            logger.error(f'❌{msg}')
            raise DatasetNotFoundError(msg)

        if response.is_success:
            logger.info('✅ Dataset access verified.')
        else:
            msg = f'Unexpected response (HTTP {response.status_code}) while checking dataset access.'
            logger.error(f'❌{msg}')
            raise DatasetAccessError(msg)

    except RetryError as e:
        error_msg = (
            'The retry limit has been reached for checking dataset access. '
            'Check your input of `base_url` and `pid`. Or check your internet connection.'
        )
        logger.error(error_msg)
        raise DatasetAccessError(error_msg) from e


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


def parse_dataset_url(base_url: str | None, pid: str | None) -> str:
    """Construct a Dataverse dataset URL from a base URL and persistent ID.

    Args:
        base_url (str): The base URL of the Dataverse installation (with or without trailing slash).
        pid (str): The persistent identifier (PID) of the dataset.

    Returns:
        str: A properly constructed and encoded dataset URL.
    """
    # Ensure correct path joining
    if base_url and pid:
        api_path = 'dataset.xhtml'
        base = base_url.rstrip('/') + '/'  # guarantee single trailing slash

        # Encode query params safely
        query = urlencode({'persistentId': pid})

        return urljoin(base, api_path) + '?' + query

    return 'No URL'


def get_name_initials(fullname: str) -> str:
    """Get the initials from a full name string.

    Args:
        fullname (str): The full name string.

    Returns:
        str: The initials of the name.
    """
    return ''.join([x[0].upper() for x in fullname.split(' ')])


def validate_api_token(value: str | None) -> str | None:
    """Validate API token to prevent empty strings from overriding environment values.

    Note: None values are treated as intentionally unset and are returned unchanged.
    """
    env_token = os.getenv('API_TOKEN')
    if value == '' and env_token:
        return env_token
    return value


def get_ymdhms_timestamp() -> str:
    """Get the current timestamp in YYYYMMDD_HHMMSS format.

    Returns:
        str: The current timestamp as a string.
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def validate_project_number(value: str) -> str:
    """Validate project number that only allows letters, numbers, hyphens, and underscores.

    Args:
        value (str): The project number to validate.

    Returns:
        str: The validated project number.
    """
    if value and not re.fullmatch(r'^[A-Za-z0-9_-]+$', value):
        msg = 'Project number must only contain letters, numbers, hyphens, and underscores.'
        raise ValueError(msg)
    return value


def in_wsl() -> bool:
    """Return whether the code is running in Windows Subsystem for Linux.

    Returns:
        bool: True if running in WSL, False otherwise.

    """
    release = str(platform.uname().release).lower()
    return 'microsoft' in release or 'wsl' in release


def open_folder(path: Path | str = '.') -> None:
    """Open a folder in the system's file explorer.

    Args:
        path (Path | str): The path to the folder to open.
    """
    p = Path(path).expanduser().resolve()

    if in_wsl():
        # WSL path -> Windows path -> Explorer
        win_path = subprocess.check_output(['wslpath', '-w', str(p)], text=True).strip()
        subprocess.run(['explorer.exe', win_path], check=False)
        return

    if os.name == 'nt':
        # Native Windows / PowerShell
        os.startfile(str(p))
        return

    # macOS / Linux
    opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
    subprocess.run([opener, str(p)], check=False)
