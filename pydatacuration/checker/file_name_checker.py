"""Module for checking file name format."""

import re
import sys
from pathlib import Path

from pydatacuration.custom_logging import logger


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
                logger.info(f'Error: {e}')
                sys.exit(1)

        if Path(file).suffix in load_preferred_file_formats_list(preferred_file_formats_config):
            return file, True
        return file, False
