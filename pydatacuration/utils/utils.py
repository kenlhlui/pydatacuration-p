"""Utility functions."""

import os
import re
import sys
from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import urlencode
from urllib.parse import urljoin

import deepdiff
import orjson
import seedir as sd
import typer
from loguru import logger
from tenacity import RetryError

from pydatacuration.checklist.utils import validate_checklist_yaml
from pydatacuration.exceptions import DatasetAccessError
from pydatacuration.exceptions import DatasetNotFoundError
from pydatacuration.exceptions import DatasetUnauthorizedError
from pydatacuration.httpx_client import HTTPXClient


# Logger is imported directly from loguru


def check_readme_file_existence(file: str) -> tuple:
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
        diff_log_path = Path(work_dir, 'logs', 'diff.txt').resolve()
        with diff_log_path.open('w', encoding='utf-8') as f:
            f.write(str(diff))
        logger.warning(f'See the {str(diff_log_path)} file for the differences.')
        sys.exit(1)

    else:
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
            logger.info('The target directory does not exist. Exiting...')
            sys.exit(1)

    except Exception as e:
        logger.info(f'Error: {e}')
        logger.info('An error occurred while generating the folder tree diagram. Exiting...')
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
            httpx_client.logger.error(f'❌{msg}')
            raise DatasetUnauthorizedError(msg)

        if response.status_code in http_not_found_codes:
            msg = 'The dataset does not exist. Please check the PID input.'
            httpx_client.logger.error(f'❌{msg}')
            raise DatasetNotFoundError(msg)

        if response.status_code in http_success_codes:
            httpx_client.logger.info('✅ Dataset access verified.')

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


def discover_checklist_files(res_dir: Path) -> dict[str, str]:
    """Discover available checklist files in the res directory.

    Searches for checklist files matching these patterns:
    - checklist-*.yaml or checklist-*.yml
    - checklist.yaml or checklist.yml

    Args:
        res_dir (Path): Path to the res directory containing checklist files.

    Returns:
        dict[str, str]: Dictionary mapping checklist identifiers to display names.
                        Example: {'high': 'High', 'medium': 'Medium', 'custom': 'Custom'}
    """
    checklist_options = {}

    if not res_dir.exists():
        logger.warning(f'Resource directory not found: {res_dir}')
        return checklist_options

    # Pattern 1: checklist-*.yaml or checklist-*.yml
    for pattern in ['checklist-*.yaml', 'checklist-*.yml']:
        for file_path in res_dir.glob(pattern):
            try:
                validate_checklist_yaml(file_path)
                identifier = file_path.stem.replace('checklist-', '')
                display_name = identifier.replace('_', ' ').replace('-', ' ').title()
                checklist_options[identifier] = display_name
            except Exception:
                logger.warning(f'Skipping invalid checklist file: {file_path}')
                continue

    # Pattern 2: checklist.yaml or checklist.yml
    for extension in ['.yaml', '.yml']:
        default_checklist = res_dir / f'checklist{extension}'
        if default_checklist.exists():
            try:
                validate_checklist_yaml(default_checklist)
                checklist_options['default'] = 'Default'
            except Exception:
                logger.warning(f'Skipping invalid checklist file: {default_checklist}')
                continue

    return checklist_options
