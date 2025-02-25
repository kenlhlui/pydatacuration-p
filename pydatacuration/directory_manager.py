"""This module is used to manage the directories in the project."""

from pathlib import Path


class DirectoryManager:
    """This class is used to manage the directories in the project."""

    def __init__(self, workdir: str = None) -> None:
        """Initialize the class.

        Args:
            workdir (str): The working directory.
        """
        self._check_dir(workdir)

    def _check_dir(self, dir_path: str):
        """Check if the directory exists and update self.workdir.

        Args:
            dir_path (str): The path to the directory.

        This method updates self.workdir to a valid path (user's choice if valid, otherwise current directory).
        """
        dir_path = Path(dir_path)  # Ensure dir_path is a Path object
        self.workdir = dir_path if dir_path.exists() else Path(Path.cwd(), 'workdir')
        if not dir_path.exists():
            print(f'The user defined directory does not exist. The current directory will be used: {self.workdir}')

    def _mk_log_dir(self) -> str:
        """Create the log directory.

        Returns:
            str: The path to the log directory.
        """
        log_files_dir = Path(self.workdir, 'log_files', 'temp_data')
        log_files_dir.mkdir(parents=True, exist_ok=True)

        return str(log_files_dir.resolve())

    def _mk_ds_dir(self) -> str:
        """Create the dataset directory.

        Returns:
            str: The path to the dataset directory.
        """
        dir_path_list = [
            Path(self.workdir, 'dataset').resolve(),
            Path(self.workdir, 'dataset', 'files').resolve(),
            Path(self.workdir, 'dataset', 'metadata').resolve(),
        ]

        for dir_path in dir_path_list:
            Path.mkdir(dir_path, parents=True, exist_ok=True)

        return str(dir_path_list[0])

    def _mk_temp_dir(self) -> str:
        """Create the temp directory.

        Returns:
            str: The path to the temp directory.
        """
        temp_data_dir = Path(self.workdir, 'temp_data')
        Path.mkdir(temp_data_dir, parents=True, exist_ok=True)

        return str(temp_data_dir.resolve())

    def make_dirs(self) -> tuple:
        """Create the directories.

        Returns:
            tuple: A tuple containing the workdir, log_files_dir, ds_dir, temp_data_dir directories.
        """
        log_files_dir = self._mk_log_dir()
        ds_dir = self._mk_ds_dir()
        temp_data_dir = self._mk_temp_dir()
        print('\nworkdir created')
        return self.workdir, log_files_dir, ds_dir, temp_data_dir
