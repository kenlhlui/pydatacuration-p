"""Module for checking file name format."""

import re
from pathlib import Path

from loguru import logger

from pydatacuration.checker.check_result_writer import CheckResultWriter
from pydatacuration.checker.services.utils import get_file_name_from_file_list_metadata
from pydatacuration.checker.services.utils import get_file_rel_path_from_file_list_metadata


class FileNameChecker:
    """This class is used to check the file name format."""

    def __init__(self, file_list_metadata: list, check_result_writer: CheckResultWriter) -> None:
        """Initialize the class."""
        self.file_list_metadata = file_list_metadata
        self.check_result_writer = check_result_writer

    @staticmethod
    def _check_special_char(file: str) -> tuple:
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
    def _check_file_name_len(file: str, file_name_max_len: int) -> tuple:
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
    def _check_file_ext(file: str) -> tuple:
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
    def _check_readme_file_existence(file: str) -> tuple:
        """Check if the file is a README file.

        Args:
            file (str): The path to the file.

        Returns:
            tuple: The file path and a boolean value.
        """
        if re.search(r'readme', file, re.IGNORECASE):
            return file, True
        return file, False

    def check_file_name_with_special_char(self) -> None:
        """Check if the file name contains special characters."""
        special_char_files = []
        for file in self.file_list_metadata:
            file_name = get_file_name_from_file_list_metadata(file)
            file_rel_path = get_file_rel_path_from_file_list_metadata(file, file_name)

            if self._check_special_char(file_name)[1] is True:
                logger.info(f'Special characters found in the filename: {file_rel_path}')
                special_char_files.append(str(file_rel_path))

        # Check special characters in file names and write to db
        self.check_result_writer.write(
            check_id='filename_special_chars',
            check_name='File names with Special Characters',
            description='Files containing special characters in filename',
            unit='file',
            results=special_char_files,
        )

    def check_file_missing_extension(self) -> None:
        """Check if the file name is without extension."""
        missing_ext_files = []
        for file in self.file_list_metadata:
            file_name = get_file_name_from_file_list_metadata(file)
            file_rel_path = get_file_rel_path_from_file_list_metadata(file, file_name)

            if self._check_file_ext(file_name)[1] is True:
                logger.info(f'File extension does not found: {file_rel_path}')
                missing_ext_files.append(str(file_rel_path))

        # Check missing file extension and write to db
        self.check_result_writer.write(
            check_id='missing_file_extensions',
            check_name='File names missing extensions',
            description='Files without proper file extensions',
            unit='file',
            results=missing_ext_files,
        )

    def check_readme_file(self) -> None:
        """Check if the README file exists."""
        readme_files = []
        for file in self.file_list_metadata:
            file_name = get_file_name_from_file_list_metadata(file)
            file_rel_path = get_file_rel_path_from_file_list_metadata(file, file_name)

            if self._check_readme_file_existence(file_name)[1] is True:
                logger.info(f'README file found: {file_rel_path}')
                readme_files.append(str(file_rel_path))

        # Check README files and write to db
        self.check_result_writer.write(
            check_id='readme_files',
            check_name='File names for README',
            description='README files detected in the dataset',
            unit='file',
            results=readme_files,
        )
