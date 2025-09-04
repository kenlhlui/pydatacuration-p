"""This module is used to manage the directories in the project."""

import sys
from pathlib import Path
from shutil import rmtree

from .custom_logging import logger


class DirectoryManager:
    """Generic directory manager for creating and managing project directories."""

    def __init__(self, ticket_number: str, main_dir: str | Path) -> None:
        """Initialize the class.

        Args:
            ticket_number (str): The ticket number, also the name of the working directory.
            main_dir (str | Path): The main directory that contains /db and the /projects directories.
        """
        self.ticket_number = ticket_number
        self.main_dir = main_dir
        self.project_dir = self._define_project_dir()
        self.logger = logger

        # Pre-defined directory structure
        self._directory_structure = {
            'logs': 'logs',
            'dataset/files': 'dataset/files',
            'dataset/metadata': 'dataset/metadata',
            'dataset/temp': 'dataset/temp',
            'outputs': 'outputs',
            'outputs/reports': 'outputs/reports',
        }

    def _define_project_dir(self) -> Path:
        """Define the project directory.

        Returns:
            Path: The path object of the project directory.
        """
        if self.main_dir:
            project_dir = Path(self.main_dir)
            # If project_dir already ends with the ticket number, use it directly
            if project_dir.name == self.ticket_number:
                return project_dir.resolve()
            # Otherwise, create the project structure
            return Path(project_dir, 'projects', self.ticket_number).resolve()
        return Path(Path.cwd(), 'workdir', self.ticket_number).resolve()

    def _define_db_dir(self) -> Path:
        """Define the database directory.

        Returns:
            Path: The path object of the database directory.
        """
        return Path(self.main_dir, 'db').resolve()

    def _define_db_path(self) -> Path:
        """Define the database file path.

        Returns:
            Path: The path object of the database file.
        """
        return Path(self._define_db_dir(), 'duckdb.db').resolve()

    def get_dir(self, dir_name: str) -> Path:
        """Get a directory path by name.

        Args:
            dir_name (str): The directory name key.

        Returns:
            Path: The resolved path to the directory.

        Raises:
            KeyError: If the directory name is not found.
        """
        if dir_name == 'db':
            return self._define_db_dir()
        if dir_name not in self._directory_structure:
            msg = f"Directory '{dir_name}' not found in structure"
            raise KeyError(msg)

        dir_path = self._directory_structure[dir_name]
        return (self.project_dir / dir_path).resolve()

    def create_dir(self, dir_name: str, custom_path: str | None = None) -> Path:
        """Create a single directory.

        Args:
            dir_name (str): The directory name key or custom name.
            custom_path (str, optional): Custom path relative to workdir.

        Returns:
            Path: The created directory path.
        """
        dir_path = (self.project_dir / custom_path).resolve() if custom_path else self.get_dir(dir_name)

        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def create_dirs(
        self, dir_names: list[str] | None = None, custom_dirs: dict[str, str] | None = None
    ) -> dict[str, Path]:
        """Create multiple directories.

        Args:
            dir_names (List[str], optional): List of directory names to create.
            custom_dirs (Dict[str, str], optional): Custom directories {name: path}.

        Returns:
            Dict[str, Path]: Dictionary of created directory paths.
        """
        created_dirs = {}

        # Create predefined directories
        if dir_names:
            for name in dir_names:
                created_dirs[name] = self.create_dir(name)

        # Create custom directories
        if custom_dirs:
            for name, path in custom_dirs.items():
                created_dirs[name] = self.create_dir(name, path)

        return created_dirs

    def make_dirs(self) -> dict[str, Path]:
        """Create the default project directory structure.

        Returns:
            Dict[str, Path]: Dictionary of created directory paths.
        """
        default_dirs = [
            'logs',
            'dataset/files',
            'dataset/metadata',
            'dataset/temp',
            'outputs',
        ]
        created_dirs = self.create_dirs(default_dirs)

        # Also create database directory
        created_dirs['db'] = self.create_dir('db')

        # Setup logging after log directory is created
        self.logger.info(f'The working directory is: {self.project_dir}')

        return created_dirs

    def add_directory(self, name: str, path: str) -> None:
        """Add a new directory to the structure.

        Args:
            name (str): The directory name key.
            path (str): The directory path relative to workdir.
        """
        self._directory_structure[name] = path

    def list_directories(self) -> dict[str, str]:
        """List all defined directories.

        Returns:
            dict[str, str]: Dictionary of directory names and their paths.
        """
        return self._directory_structure.copy()

    @staticmethod
    def confirm_del_dir(dir_path: Path, force_del: bool) -> None:
        """Confirm deletion of a directory.

        Args:
            dir_path (Path): The directory path to delete.
            force_del (bool): Whether to force deletion without confirmation.
        """
        if dir_path.exists() and not force_del:
            try:
                confirm = input(f"Directory '{dir_path}' already exists. Do you want to delete it? (y/n): ")
                if confirm.lower() not in {'y', 'yes'}:
                    logger.warning('Aborted by user. Exiting...')
                    sys.exit(1)
            except Exception as e:
                logger.error(f'Error occurred while confirming deletion: {e}')
                sys.exit(1)

        if dir_path.exists():
            rmtree(dir_path, ignore_errors=True)
            logger.info(f'Will replace {dir_path} with the new files.')

    @staticmethod
    def delete_dir(dir: Path) -> None:
        """Delete a specific directory by name.

        Args:
            dir (Path): The directory path to delete.
        """
        try:
            if dir.exists():
                rmtree(dir, ignore_errors=True)
                logger.info(f'Deleted directory: {dir}')
            else:
                logger.warning(f'Directory does not exist: {dir}')
        except KeyError as e:
            logger.error(f'Error deleting directory: {e}')

    # Backward compatibility properties
    @property
    def log_files_dir(self) -> Path:
        """Get log files directory path."""
        return self.get_dir('logs')

    @property
    def logs_dir(self) -> Path:
        """Get logs directory path."""
        return self.get_dir('logs')

    @property
    def db_dir(self) -> Path:
        """Get database directory path."""
        return self.get_dir('db')

    @property
    def db_path(self) -> Path:
        """Get database file path."""
        return self._define_db_path()

    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return self.get_dir('data')

    @property
    def outputs_dir(self) -> Path:
        """Get outputs directory path."""
        return self.get_dir('outputs')

    @property
    def metadata_dir(self) -> Path:
        """Get metadata directory path."""
        return self.get_dir('dataset/metadata')
