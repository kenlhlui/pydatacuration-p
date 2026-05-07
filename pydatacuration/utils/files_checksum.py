"""This module is used to generate the checksum of the files in the dataset directory."""

import hashlib
from pathlib import Path
from pathlib import PurePosixPath


class FilesChecksum:
    """This class is used to generate the checksum of the files in the dataset directory."""

    @staticmethod
    def _get_md5(file_path: Path | str) -> str:
        """Generate the MD5 checksum for a given file.

        Args:
            file_path (Path | str): The path to the file for which to generate the checksum

        Returns:
            str: The MD5 checksum of the file.
        """
        with Path(file_path).open('rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def gen_ds_files_checksum(self, target_dir: Path) -> list:
        """Generate the checksum of the files in the dataset directory.

        Args:
            target_dir (Path): The path to directory containing the files.

        Returns:
            list: A list of dictionaries containing the file path and the checksum.
        """
        dl_file_checksum_nested_list = []

        target_dir_path = target_dir.resolve()

        # Iterate through all files in the directory and subdirectories
        for file_path in target_dir_path.rglob('*'):
            if file_path.is_file():  # Only process files
                # Get the relative path from target_dir_path
                relative_file_path = file_path.relative_to(target_dir_path)

                # Append the relative file path and its MD5 checksum to the result list
                dl_file_checksum_nested_list.append(
                    {'file': str(PurePosixPath(relative_file_path)), 'md5_checksum': self._get_md5(file_path)}
                )

        return dl_file_checksum_nested_list
