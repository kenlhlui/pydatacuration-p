"""Module to verify the downloaded files against the metadata JSON file."""

from pathlib import Path
from pathlib import PurePosixPath

import deepdiff
from loguru import logger

from pydatacuration.exceptions import FileMatchError
from pydatacuration.utils.directory_manager import DirectoryManager
from pydatacuration.utils.files_checksum import FilesChecksum
from pydatacuration.utils.search_ds_meta import get_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_name_from_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_rel_path_from_file_list_metadata
from pydatacuration.utils.utils import get_ymdhms_timestamp


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
                {'file': str(PurePosixPath(file_full_path_obj)), 'checksum': file_meta['dataFile']['md5']}
            )

        return file_list_metadata_nested_list

    def _validate_files_against_metadata(
        self,
        dl_files_checksums: list,
        metadata_file_checksums: list,
    ) -> None:
        diff = deepdiff.DeepDiff(
            dl_files_checksums,
            metadata_file_checksums,
            ignore_order=True,
        )

        if diff:
            logger.warning('The downloaded files and the file list metadata are different.')

            diff_log_path = (
                Path(self.dir_manager_instance.global_log_dir) / f'diff_{get_ymdhms_timestamp()}.txt'
            ).resolve()

            with diff_log_path.open('w', encoding='utf-8') as file:
                file.write(str(diff))

            logger.warning(f'See {diff_log_path} for the differences.')

            msg = 'Downloaded files do not match metadata checksums.'
            raise FileMatchError(msg)

        logger.info('The downloaded files and the file list metadata are the same.')

    def verify(self) -> list:
        """Verify the downloaded files against the metadata JSON file.

        Args:
            project_dir (Path): The top level project directory where the downloaded files are located. (e.g. /CUR-999/dataset/files), and CUR-999 is the dir to be passed in.

        Returns:
            list | None: A list of dictionaries containing the file path and the checksum if the verification is successful, None otherwise.
        """  # noqa: E501
        self._validate_files_against_metadata(
            FilesChecksum().gen_ds_files_checksum(self.dir_manager_instance.files_dir),
            self.file_list_metadata_nested_list,
        )

        logger.info('Verification successful: The downloaded files match the metadata JSON file.')

        return self.file_list_metadata_nested_list
