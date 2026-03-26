"""This module is for unzipping files."""

import bz2
import gzip
import lzma
import tarfile
import zipfile
from pathlib import Path

import py7zr
from loguru import logger


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

    def _unzip(self) -> None:
        """Unzip the file."""
        with zipfile.ZipFile(self.zip_file, 'r') as zip_ref:
            zip_ref.extractall(self.output_dir)

    def _extract_tar(self) -> None:
        """Extract tar files and compressed files."""
        name = self.zip_file.name

        # Handle tar archives
        if name.endswith('.tar'):
            with tarfile.open(self.zip_file, 'r') as tar_ref:
                tar_ref.extractall(path=self.output_dir)
        elif name.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(self.zip_file, 'r:gz') as tar_ref:
                tar_ref.extractall(path=self.output_dir)
        elif name.endswith(('.tar.bz2', '.tbz2')):
            with tarfile.open(self.zip_file, 'r:bz2') as tar_ref:
                tar_ref.extractall(path=self.output_dir)
        elif name.endswith(('.tar.xz', '.txz')):
            with tarfile.open(self.zip_file, 'r:xz') as tar_ref:
                tar_ref.extractall(path=self.output_dir)
        # Handle single compressed files
        elif name.endswith('.gz'):
            output_file = self.output_dir / self.zip_file.stem
            with gzip.open(self.zip_file, 'rb') as f_in, Path(output_file).open('wb') as f_out:
                f_out.write(f_in.read())
        elif name.endswith('.bz2'):
            output_file = self.output_dir / self.zip_file.stem
            with bz2.open(self.zip_file, 'rb') as f_in, Path(output_file).open('wb') as f_out:
                f_out.write(f_in.read())
        elif name.endswith('.xz'):
            output_file = self.output_dir / self.zip_file.stem
            with lzma.open(self.zip_file, 'rb') as f_in, Path(output_file).open('wb') as f_out:
                f_out.write(f_in.read())

    def _extract_7z(self) -> None:
        """Extract 7z files."""
        with py7zr.SevenZipFile(self.zip_file, mode='r') as archive:
            archive.extractall(path=self.output_dir)

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
        logger.debug(f'Extracted file relative paths list: {relative_paths}')
        return relative_paths

    def main(self) -> list[Path]:
        """Main method to unzip and get the paths of the extracted files."""
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        name = self.zip_file.name

        if name.endswith('.zip'):
            self._unzip()
        elif name.endswith('.7z'):
            self._extract_7z()
        elif any(
            name.endswith(ext)
            for ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', '.txz', '.gz', '.bz2', '.xz']
        ):
            self._extract_tar()
        else:
            logger.warning(f'Unsupported archive format: {self.zip_file}')

        return self._get_extracted_file_paths()
