"""Class for checking file access and permissions."""

from pathlib import Path

from loguru import logger

from pydatacuration.checker.check_result_writer import CheckResultWriter


class FileAccessChecker:
    """Class for checking file access and permissions."""

    def __init__(self, check_result_writer: CheckResultWriter):
        self.checklist_result_writer = check_result_writer

    def check_restricted_files(self, ds_metadata: dict) -> None:
        """Check for restricted files in the dataset metadata.

        Args:
            ds_metadata (dict): The dataset metadata from the JSON file.
        """
        restricted_files = []

        file_list = ds_metadata.get('data', {}).get('latestVersion', {}).get('files', [])

        if file_list:
            for file in file_list:
                if file.get('restricted') is True:
                    file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get(
                        'filename'
                    )
                    file_path = Path(file.get('directoryLabel', ''), file_name)
                    logger.info(f'Restricted file found: {file_path}')
                    restricted_files.append(str(file_path))

        self.checklist_result_writer.write(
            check_id='restricted_files',
            check_name='Restricted file names',
            description='files with access restrictions in the dataset',
            unit='file',
            results=restricted_files,
        )
