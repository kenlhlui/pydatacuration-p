"""This module is used to generate the checksum of the files in the dataset directory."""

import hashlib
from pathlib import Path


class Checksum:
    """This class is used to generate the checksum of the files in the dataset directory."""

    @staticmethod
    def _get_md5(file_path: Path) -> str:
        """Generate the MD5 checksum for a given file."""
        with Path(file_path).open('rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def gen_ds_files_checksum(self, target_dir: Path) -> list:
        """Generate the checksum of the files in the dataset directory.

        Args:
            target_dir (str): The path to the dataset directory.

        Returns:
            list: A list of dictionaries containing the file path and the checksum.
        """
        dl_file_checksum_nested_list = []

        # Normalize target_dir to a Path object and resolve to an absolute path
        target_dir_path = target_dir.resolve()

        # Iterate through all files in the directory and subdirectories
        for file_path in target_dir_path.rglob('*'):
            if file_path.is_file():  # Only process files
                # Get the relative path from target_dir_path
                relative_file_path = file_path.relative_to(target_dir_path)

                # Append the relative file path and its MD5 checksum to the result list
                dl_file_checksum_nested_list.append({
                    'file': str(relative_file_path).replace('\\', '/'),
                    'md5_checksum': self._get_md5(file_path)
                })

        return dl_file_checksum_nested_list
