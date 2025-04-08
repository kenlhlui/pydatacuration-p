"""This module is for unzipping files."""

import zipfile
from pathlib import Path

from .custom_logging import CustomLogger


class Unzipper:
    """This class is used to unzip files."""

    def __init__(self, zip_file: str | Path, output_dir: str | Path) -> None:
        """Initialize the Unzipper class.

        Args:
            zip_file (str): The path to the zip file.
            output_dir (str): The path to the output directory.
        """
        self.zip_file = Path(zip_file)
        self.output_dir = Path(output_dir)
        self.logger = CustomLogger.get_logger(__name__)

    def _unzip(self) -> None:
        """Unzip the file."""
        with zipfile.ZipFile(self.zip_file, 'r') as zip_ref:
            zip_ref.extractall(self.output_dir)

    def _get_extracted_file_paths(self) -> list[Path]:
        """Get the paths of the extracted files.

        Returns:
            list[Path]: List of paths to the extracted files.
        """
        # Get the list of the file paths in the output directory using rglob
        extracted_files = list(self.output_dir.rglob('*'))
        # Filter out directories and keep only files
        file_paths = [file for file in extracted_files if file.is_file()]
        # Convert to relative paths
        relative_paths = [file.relative_to(self.output_dir) for file in file_paths]
        self.logger.debug(f'Extracted file relative paths list: {relative_paths}')
        return relative_paths

    def main(self) -> list[Path]:
        """Main method to unzip and get the paths of the extracted files.

        Returns:
            list[Path]: List of paths to the extracted files.
        """
        self._unzip()
        return self._get_extracted_file_paths()
