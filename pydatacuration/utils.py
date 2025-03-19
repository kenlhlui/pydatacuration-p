"""This module contains utility functions for data curation tasks."""
import os
import re
import sys
from pathlib import Path
from pathlib import PurePosixPath

import deepdiff
import seedir as sd
import typer

from .custom_logging import CustomLogger


# Initialize the logger
logger = CustomLogger.get_logger(__name__)

class FileNameFormatChecker:
    """This class is used to check the file name format."""

    def __init__(self) -> None:
        """Initialize the class."""

    @staticmethod
    def check_special_char(file: str) -> tuple:
        """Check if the file name contains special characters.

        Args:
            file (str): The path to the file.

        Returns:
            tuple: The file path and a boolean value.
        """
        if re.search(r'[^\w\s]', Path(file).stem):
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


def compare_files_and_metadata(dl_files_checksums, metadata_file_checksums, workddir: Path):
    """Compare the downloaded files checksums and the metadata JSON file checksums.

    Args:
        dl_files_checksums (list): A list of dictionaries containing the file path and the checksum.
        metadata_files_cehcksums (list): A list of dictionaries containing the file path and the checksum.
        workddir (Path): The working directory.

    Returns:
        bool: True if the downloaded files and the metadata JSON file checksums are the same, False otherwise.
    """
    diff = deepdiff.DeepDiff(dl_files_checksums, metadata_file_checksums, ignore_order=True)
    if diff:
        logger.warning('The downloaded files and the file list metadata are different.')
        diff_log_path = Path(workddir, 'log_files', 'diff.txt').resolve()
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
        filename = file_meta.get('dataFile', {}).get('originalFileName') or file_meta.get('dataFile', {}).get('filename')  # noqa: E501
        directory_label = file_meta.get('directoryLabel', '')
        file_full_path_obj = Path(directory_label, filename)
        file_list_metadata_nested_list.append({
            'file': str(PurePosixPath(file_full_path_obj)),
            'md5_checksum': file_meta['dataFile']['md5']
        })

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
