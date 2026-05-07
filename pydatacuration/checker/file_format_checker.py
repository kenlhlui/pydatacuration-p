"""A module to check the file format of the files in the dataset."""

from pathlib import Path

import yaml
from loguru import logger

from pydatacuration.checker.check_result_writer import CheckResultWriter
from pydatacuration.utils.directory_manager import DirectoryManager
from pydatacuration.utils.search_ds_meta import get_file_list_metadata


class FileFormatChecker:
    """A class to check the file format of the files in the dataset."""

    def __init__(
        self,
        ds_metadata: dict,
        res_dir: Path,
        check_result_writer: CheckResultWriter,
        directory_manager: DirectoryManager,
    ) -> None:
        """Initialize the class."""
        self.file_list_metadata = get_file_list_metadata(ds_metadata)
        self.check_result_writer = check_result_writer
        self.directory_manager = directory_manager
        self.common_file_format_tuple = self._read_common_file_format(res_dir)

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

    @staticmethod
    def _read_common_file_format(res_dir: Path) -> tuple | None:
        """Reads the common_file_format.yaml file and returns it as a dictionary.

        Args:
            res_dir (Path): The path to the res directory.

        Returns:
            dict: The common file format as a dictionary.
        """
        try:
            # Check if the file exists
            if res_dir.joinpath('common_file_formats.yaml').exists():
                # Open the file and read its content
                with res_dir.joinpath('common_file_formats.yaml').open(encoding='utf-8') as file:
                    common_file_format_dict = yaml.safe_load(file)
                    logger.debug(f'common_file_formats.yaml content: {common_file_format_dict}')

                    file_formats = set()
                    for _category, extensions in common_file_format_dict['file_formats'].items():
                        file_formats.update(extensions)  # Use set to avoid duplicates

                    return tuple(file_formats)  # Convert set to tuple for immutability

        except FileNotFoundError:
            # Handle the case where the file is not found
            logger.error('common_file_formats.yaml file not found in the res directory.')
            return ()  # Return an empty tuple if the file is not found
        except yaml.YAMLError as e:
            # Handle YAML parsing errors
            logger.error(f'Error parsing common_file_formats.yaml: {e}')
            return ()  # Return an empty tuple if there is a parsing error

    def check_common_file_format(self) -> None:
        """Check if the file format is in the common file format."""
        uncommon_format_files = []

        logger.debug('Starting check for common file formats.')

        if self.common_file_format_tuple:
            for file in self.file_list_metadata:
                file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
                file_rel_path = Path(file.get('directoryLabel', ''), file_name)
                file_ext = file_rel_path.suffix
                if file_ext.startswith('.') and file_ext not in self.common_file_format_tuple:
                    file_abs_path = Path(self.directory_manager.files_dir, file_rel_path)
                    logger.info(f'File is not a common file format: {file_abs_path}')
                    uncommon_format_files.append(str(file_rel_path))
        else:
            logger.error('No common file format found in the res directory. Skipping this check.')

        self.check_result_writer.write(
            check_id='uncommon_file_formats',
            check_name='Files with uncommon formats',
            description='Files using uncommon or proprietary file formats',
            unit='file',
            results=uncommon_format_files,
        )
