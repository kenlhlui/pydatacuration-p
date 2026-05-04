"""Module to verify the downloaded files against the metadata JSON file."""

from pathlib import Path
from pathlib import PurePosixPath

import deepdiff
from loguru import logger

from pydatacuration.services.files_checksum import FilesChecksum


class VerifyDownloadFiles:
    """Class to verify the downloaded files against the metadata JSON file."""

    def __init__(
        self,
        target_dir: Path,
        ds_metadata: dict,
    ) -> None:
        """Initialize the VerifyDownloadFiles class."""
        self.target_dir = target_dir
        self.ds_metadata = ds_metadata

        self.file_list_metadata: list = self.get_file_list_metadata()

        self.file_list_metadata_nested_list: list = self.parse_file_list_metadata(self.file_list_metadata)

        self.checksum_generator = FilesChecksum()

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
            filename = file_meta.get('dataFile', {}).get('originalFileName') or file_meta.get('dataFile', {}).get(
                'filename'
            )  # noqa: E501
            directory_label = file_meta.get('directoryLabel', '')
            file_full_path_obj = Path(directory_label, filename)
            file_list_metadata_nested_list.append(
                {'file': str(PurePosixPath(file_full_path_obj)), 'md5_checksum': file_meta['dataFile']['md5']}
            )

        return file_list_metadata_nested_list

    @staticmethod
    def compare_files_and_metadata(dl_files_checksums: list, metadata_file_checksums: list, work_dir: Path) -> bool:
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
            return False

        logger.info('The downloaded files and the file list metadata are the same.')
        return True

    def generate_dl_files_checksums(self) -> list:
        """Generate the checksums of the downloaded files.

        Returns:
            list: A list of dictionaries containing the file path and the checksum.
        """
        return self.checksum_generator.gen_ds_files_checksum(self.target_dir)

    def get_file_list_metadata(self) -> list:
        """Get the file list metadata from the dataset metadata.

        Returns:
            list: A list of dictionaries containing the file path and the checksum.
        """
        return self.ds_metadata.get('data', {}).get('latestVersion', {}).get('files', [])

    def verify(self, work_dir: Path) -> list | None:
        """Verify the downloaded files against the metadata JSON file.

        Args:
            work_dir (Path): The working directory.

        Returns:
            list | None: A list of dictionaries containing the file path and the checksum if the verification is successful, None otherwise.
        """  # noqa: E501
        if self.compare_files_and_metadata(
            self.generate_dl_files_checksums(), self.file_list_metadata_nested_list, work_dir
        ):
            logger.info('Verification successful: The downloaded files match the metadata JSON file.')
            return self.file_list_metadata_nested_list
        logger.error('Verification failed: The downloaded files do not match the metadata JSON file.')
        return None
