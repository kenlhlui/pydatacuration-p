"""This module is used to manage the directories in the project."""

from pathlib import Path
from shutil import rmtree

from .custom_logging import logger


class DirectoryManager:
    """Generic directory manager for creating and managing project directories."""

    # Pre-defined constants
    DB_FILE_NAME = 'db.duckdb'
    DB_SUBDIR = 'db'

    def __init__(self, project_number: str, main_dir: str | Path, res_dir: str | Path | None = None) -> None:
        """Initialize the class.

        Args:
            project_number (str): The project number, also the name of the working directory.
            main_dir (str | Path): The main directory that contains /db and the /projects directories.
            res_dir (str | Path | None): The resource directory path.
        """
        self.project_number = project_number
        self.main_dir = main_dir
        self.project_dir = self._define_project_dir()
        self.res_dir = res_dir

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
        if self.main_dir_path:
            project_dir = Path(self.main_dir_path)
            # If project_dir already ends with the project number, use it directly
            if project_dir.name == self.project_number:
                return project_dir.resolve()
            # Otherwise, create the project structure
            return Path(project_dir, 'projects', self.project_number).resolve()
        return Path(Path.cwd(), 'workdir', self.project_number).resolve()

    def _define_db_dir(self) -> Path:
        """Define the database directory.

        Returns:
            Path: The path object of the database directory.
        """
        return Path(self.main_dir_path, self.DB_SUBDIR).resolve()

    def _define_db_path(self) -> Path:
        """Define the database file path.

        Returns:
            Path: The path object of the database file.
        """
        return Path(self._define_db_dir(), self.DB_FILE_NAME).resolve()

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
        logger.info(f'The working directory is: {self.project_dir}')

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
    def outputs_dir(self) -> Path:
        """Get outputs directory path."""
        return self.get_dir('outputs')

    @property
    def metadata_dir(self) -> Path:
        """Get metadata directory path."""
        return self.get_dir('dataset/metadata')

    @property
    def files_dir(self) -> Path:
        """Get files directory path."""
        return self.get_dir('dataset/files')

    @property
    def main_dir_path(self) -> Path:
        """Get main directory path."""
        return Path(self.main_dir).resolve()
