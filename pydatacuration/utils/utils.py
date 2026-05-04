"""Utility functions."""

import os
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.parse import urljoin

import deepdiff
import orjson
import seedir as sd
import typer
from loguru import logger
from tenacity import RetryError

from pydatacuration.exceptions import DatasetAccessError
from pydatacuration.exceptions import DatasetNotFoundError
from pydatacuration.exceptions import DatasetUnauthorizedError
from pydatacuration.httpx_client import HTTPXClient


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
        return True

    logger.info('The downloaded files and the file list metadata are the same.')
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

                logger.info(f'Folder tree diagram text file saved at: {str(ds_tree_file_path)}')
        else:
            logger.warning(f'Target directory does not exist: {str(target_dir)} - skipping tree diagram generation.')
    except Exception as e:
        logger.info(f'Error: {e}')
        logger.info('An error occurred while generating the folder tree diagram.')


def check_project_num_input(project_number: str) -> str:
    """Check if the project number is without any special characters or spaces.

    Args:
        project_number (str): The project number to check.

    Returns:
        str: The validated project number.
    """
    # Check if the project number is empty
    if not project_number:
        msg = 'Project number cannot be empty.'
        raise typer.BadParameter(msg)

    # Check if the project number contains any special characters or spaces
    if re.search(r'[^a-zA-Z0-9_\-]', project_number):
        msg = '⚠️ Project number must only contain letters, numbers, hyphens, and underscores.'
        raise typer.BadParameter(msg)

    return project_number


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

    http_success_codes = {200, 201, 202, 204}
    http_unauthorized_codes = {401, 403}
    http_not_found_codes = {404}

    try:
        # Check whether the user has access to the dataset
        response = httpx_client.sync_get(f'api/datasets/:persistentId/?persistentId={pid}', raise_for_status=False)

        if response.status_code in http_unauthorized_codes:
            msg = 'You do not have read access to the dataset. Please check your API token or permissions.'
            logger.error(f'❌{msg}')
            raise DatasetUnauthorizedError(msg)

        if response.status_code in http_not_found_codes:
            msg = 'The dataset does not exist. Please check the PID input.'
            logger.error(f'❌{msg}')
            raise DatasetNotFoundError(msg)

        if response.status_code in http_success_codes:
            logger.info('✅ Dataset access verified.')

    except RetryError as e:
        error_msg = (
            'The retry limit has been reached for checking dataset access. '
            'Check your input of `base_url` and `pid`. Or check your internet connection.'
        )
        logger.error(error_msg)
        raise DatasetAccessError(error_msg) from e


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
