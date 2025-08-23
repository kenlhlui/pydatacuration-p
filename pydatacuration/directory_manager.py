"""This module is used to manage the directories in the project."""

from pathlib import Path

from loguru import logger

from .custom_logging import setup_logging


class DirectoryManager:
    """This class is used to manage the directories in the project."""

    def __init__(self, ticket_number: str, parent_dir: str | None = None) -> None:
        """Initialize the class.

        Args:
            ticket_number (str): The name ticket number, also the name of the working directory.
            parent_dir (str | None): The parent directory where the working directory will be created.
        """
        self.ticket_number = ticket_number
        self.parent_dir = parent_dir
        self.workdir = self.define_workdir()
        self.log_files_dir = Path(self.workdir, 'log_files').resolve()
        self.logger = logger

    def _mk_log_dir(self) -> Path:
        """Create the log directory.

        Returns:
            Path: The path to the log directory.
        """
        self.log_files_dir.mkdir(parents=True, exist_ok=True)

        return self.log_files_dir

    def _mk_ds_dir(self) -> Path:
        """Create the dataset directory.

        Returns:
            Path: The path to the dataset directory.
        """
        dir_path_list = [
            Path(self.workdir, 'dataset').resolve(),
            Path(self.workdir, 'dataset', 'files').resolve(),
            Path(self.workdir, 'dataset', 'metadata').resolve(),
        ]

        for dir_path in dir_path_list:
            Path.mkdir(dir_path, parents=True, exist_ok=True)

        return dir_path_list[0]  # The path object of the root directory of dataset.

    def _mk_temp_dir(self) -> Path:
        """Create the temp directory.

        Returns:
            Path: The path to the temp directory.
        """
        temp_data_dir = Path(self.workdir, 'temp_data')
        Path.mkdir(temp_data_dir, parents=True, exist_ok=True)

        return temp_data_dir.resolve()

    def define_workdir(self) -> Path:
        """Define the working directory. Combine the ticket number with the path.

        Returns:
            Path: The path object of the working directory.
        """
        if self.parent_dir:
            return Path(self.parent_dir, self.ticket_number).resolve()
        return Path(Path.cwd(), 'workdir', self.ticket_number)

    def make_dirs(self) -> None:
        """Create the directories."""
        log_files_dir = self._mk_log_dir()
        self._mk_ds_dir()  # The dataset directory.
        self._mk_temp_dir()  # The temp directory.
        setup_logging(log_files_dir)
        self.logger.info(f'The working directory is: {self.workdir}')
