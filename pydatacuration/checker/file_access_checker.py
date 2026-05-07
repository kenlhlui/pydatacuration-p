"""Class for checking file access and permissions."""

from loguru import logger

from pydatacuration.checker.check_result_writer import CheckResultWriter
from pydatacuration.utils.search_ds_meta import get_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_name_from_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_rel_path_from_file_list_metadata


class FileAccessChecker:
    """Class for checking file access and permissions."""

    def __init__(self, check_result_writer: CheckResultWriter) -> None:
        """Initialize the class."""
        self.checklist_result_writer = check_result_writer

    def check_restricted_files(self, ds_metadata: dict) -> None:
        """Check for restricted files in the dataset metadata.

        Args:
            ds_metadata (dict): The dataset metadata from the JSON file.
        """
        restricted_files = []

        file_list = get_file_list_metadata(ds_metadata)

        if file_list:
            for file in file_list:
                if file.get('restricted') is True:
                    file_name = get_file_name_from_file_list_metadata(file)
                    file_rel_path = get_file_rel_path_from_file_list_metadata(file, file_name)
                    logger.info(f'Restricted file found: {file_rel_path}')
                    restricted_files.append(str(file_rel_path))

        self.checklist_result_writer.write(
            check_id='restricted_files',
            check_name='Restricted file names',
            description='files with access restrictions in the dataset',
            unit='file',
            results=restricted_files,
        )
