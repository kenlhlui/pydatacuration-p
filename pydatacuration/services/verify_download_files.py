"""Module to verify the downloaded files against the metadata JSON file."""

from pathlib import Path
from pathlib import PurePosixPath

import deepdiff
from loguru import logger

from pydatacuration.utils.directory_manager import DirectoryManager
from pydatacuration.utils.files_checksum import FilesChecksum
from pydatacuration.utils.search_ds_meta import get_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_name_from_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_rel_path_from_file_list_metadata


class VerifyDownloadFiles:
    """Class to verify the downloaded files against the metadata JSON file."""

    def __init__(self, ds_metadata: dict, directory_manager_instance: DirectoryManager) -> None:
        """Initialize the VerifyDownloadFiles class."""
        self.ds_metadata = ds_metadata

        self.file_list_metadata: list = get_file_list_metadata(self.ds_metadata)

        self.file_list_metadata_nested_list: list = self.parse_file_list_metadata(self.file_list_metadata)

        self.checksum_generator = FilesChecksum()
        self.dir_manager_instance = directory_manager_instance

    @staticmethod
    def parse_file_list_metadata(file_list_metadata: list) -> list:
        """Parse the file list metadata.

        Args:
            file_list_metadata (list): The list of file metadata.

        Returns:
            list: The parsed file list metadata.
        """
        file_list_metadata_nested_list = []
        for file_meta in file_list_metadata:
            filename = get_file_name_from_file_list_metadata(file_meta)  # noqa: E501
            file_full_path_obj = get_file_rel_path_from_file_list_metadata(file_meta, filename)  # noqa: E501
            file_list_metadata_nested_list.append(
                {'file': str(PurePosixPath(file_full_path_obj)), 'md5_checksum': file_meta['dataFile']['md5']}
            )

        return file_list_metadata_nested_list

    def compare_files_and_metadata(self, dl_files_checksums: list, metadata_file_checksums: list) -> bool:
        """Compare the downloaded files checksums and the metadata JSON file checksums.

        Args:
            dl_files_checksums (list): A list of dictionaries containing the file path and the checksum.
            metadata_file_checksums (list): A list of dictionaries containing the file path and the checksum.
            output_dir (Path): The output directory of the log file if differences are found.

        Returns:
            bool: True if the downloaded files and the metadata JSON file checksums are the same, False otherwise.
        """
        diff = deepdiff.DeepDiff(dl_files_checksums, metadata_file_checksums, ignore_order=True)
        if diff:
            logger.warning('The downloaded files and the file list metadata are different.')
            diff_log_path = Path(self.dir_manager_instance.log_files_dir / 'diff.txt').resolve()
            with diff_log_path.open('w', encoding='utf-8') as f:
                f.write(str(diff))
            logger.warning(f'See the {str(diff_log_path)} file for the differences.')
            return False

        logger.info('The downloaded files and the file list metadata are the same.')
        return True

    def _generate_dl_files_checksums(self) -> list:
        """Generate the checksums of the downloaded files.

        Returns:
            list: A list of dictionaries containing the file path and the checksum.
        """
        return self.checksum_generator.gen_ds_files_checksum(self.dir_manager_instance.files_dir)

    def verify(self) -> list | None:
        """Verify the downloaded files against the metadata JSON file.

        Args:
            project_dir (Path): The top level project directory where the downloaded files are located. (e.g. /CUR-999/dataset/files), and CUR-999 is the dir to be passed in.

        Returns:
            list | None: A list of dictionaries containing the file path and the checksum if the verification is successful, None otherwise.
        """  # noqa: E501
        if self.compare_files_and_metadata(self._generate_dl_files_checksums(), self.file_list_metadata_nested_list):
            logger.info('Verification successful: The downloaded files match the metadata JSON file.')
            return self.file_list_metadata_nested_list
        logger.error('Verification failed: The downloaded files do not match the metadata JSON file.')
        return None
