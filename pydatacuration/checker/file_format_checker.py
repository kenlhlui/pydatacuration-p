"""A module to check the file format of the files in the dataset."""

from pathlib import Path

from loguru import logger

from pydatacuration.checker.check_result_writer import CheckResultWriter


class FileFormatChecker:
    """A class to check the file format of the files in the dataset."""

    def __init__(self, file_list_metadata: list, checklist_result_writer: CheckResultWriter) -> None:
        """Initialize the class."""
        self.file_list_metadata = file_list_metadata
        self.checklist_result_writer = checklist_result_writer

    @staticmethod
    def _check_file_preferred_format(file: str, preferred_file_formats_config: str) -> tuple:
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
                logger.error(f'Error: {e}')
                return []

        if Path(file).suffix in load_preferred_file_formats_list(preferred_file_formats_config):
            return file, True
        return file, False
