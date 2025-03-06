"""This module is used to manage the directories in the project."""

from pathlib import Path


class DirectoryManager:
    """This class is used to manage the directories in the project."""

    def __init__(self, workdir: str) -> None:
        """Initialize the class.

        Args:
            workdir (str): The working directory.
        """
        self.workdir = Path(workdir) if workdir else Path.cwd()

    def _mk_log_dir(self) -> Path:
        """Create the log directory.

        Returns:
            Path: The path to the log directory.
        """
        log_files_dir = Path(self.workdir, 'log_files', 'temp_data')
        log_files_dir.mkdir(parents=True, exist_ok=True)

        return log_files_dir.resolve()  # The path object of the log directory.

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

    def make_dirs(self) -> tuple[Path, Path, Path, Path]:
        """Create the directories.

        Returns:
            tuple: A tuple containing the workdir, log_files_dir, ds_dir, temp_data_dir directories.
        """
        log_files_dir = self._mk_log_dir()
        ds_dir = self._mk_ds_dir()
        temp_data_dir = self._mk_temp_dir()
        print(f'\nThe working directory is: {self.workdir}')
        return self.workdir, log_files_dir, ds_dir, temp_data_dir
