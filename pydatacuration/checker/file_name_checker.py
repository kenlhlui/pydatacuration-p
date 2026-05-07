"""Module for checking file name format."""

import re
from pathlib import Path

from loguru import logger

from pydatacuration.checker.check_result_writer import CheckResultWriter
from pydatacuration.utils.search_ds_meta import get_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_name_from_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_rel_path_from_file_list_metadata


class FileNameChecker:
    """This class is used to check the file name format.

    Note: For checks with bool return:
        - True means the file pass the check (i.e. has no issue/no need follow up with curation action)
        - False means the file fail the check (i.e. has issue/need follow up with curation action.)

    """  # noqa: E501

    def __init__(self, ds_metadata: dict, check_result_writer: CheckResultWriter) -> None:
        """Initialize the class."""
        self.file_list_metadata = get_file_list_metadata(ds_metadata)
        self.check_result_writer = check_result_writer

    @staticmethod
    def _check_special_char(file: str) -> bool:
        r"""Check if the file name contains special characters.

        <>:"/\|?* `CR` `LF` are absolutely forbidden in file names.

        , @ $ ~ are not recommended.

        See https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file for more details.

        Args:
            file (str): The path to the file.

        Returns:
            bool: True if the file name DOES NOT contain special characters, False otherwise.
        """
        return not bool(re.search(r'[<>:"/\\|?*,@$~\r\n]', Path(file).stem))

    @staticmethod
    def _check_file_name_len(file: str, file_name_max_len: int) -> bool:
        """Check if the file name is longer than the maximum length.

        Args:
            file (str): The path to the file.
            file_name_max_len (int): The maximum length of the file name.

        Returns:
            bool: True if the file name is shorter than or equal to the maximum length, False otherwise.
        """
        return len(Path(file).stem) <= file_name_max_len

    @staticmethod
    def _check_file_ext(file: str) -> bool:
        """Check if the file has an extension.

        Args:
            file (str): The path to the file.

        Returns:
            bool: True if the file has an extension, False otherwise.
        """
        return bool(Path(file).suffix)

    @staticmethod
    def _check_readme_file_existence(file: str) -> bool:
        """Check if the file is a README file.

        Args:
            file (str): The path to the file.

        Returns:
            bool: True if the file is a README file, False otherwise.
        """
        return bool(re.search(r'readme', file, re.IGNORECASE))

    def check_file_name_with_special_char(self) -> None:
        """Check if the file name contains special characters."""
        special_char_files = []
        for file in self.file_list_metadata:
            file_name = get_file_name_from_file_list_metadata(file)
            file_rel_path = get_file_rel_path_from_file_list_metadata(file, file_name)

            if not self._check_special_char(file_name):
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

            if not self._check_file_ext(file_name):
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

            # Note: Don't use `not here since if README file exist, it will return True and we want to add it to the list. # noqa: E501
            if self._check_readme_file_existence(file_name):
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
