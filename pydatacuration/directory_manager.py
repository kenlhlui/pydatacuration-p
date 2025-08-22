"""This module is used to manage the directories in the project."""

from pathlib import Path

from .custom_logging import CustomLogger


class DirectoryManager:
    """Generic directory manager for creating and managing project directories."""

    def __init__(self, ticket_number: str, parent_dir: str) -> None:
        """Initialize the class.

        Args:
            ticket_number (str): The ticket number, also the name of the working directory.
            parent_dir (str): The parent directory where the working directory will be created.
        """
        self.ticket_number = ticket_number
        self.parent_dir = parent_dir
        self.workdir = self._define_workdir()
        self.logger = CustomLogger.get_logger(__name__)

        # Pre-defined directory structure
        self._directory_structure = {
            'log_files': 'log_files',
            'db': '../db',  # Relative to parent_dir
            'dataset': 'dataset',
            'dataset_files': 'dataset/files',
            'dataset_metadata': 'dataset/metadata',
            'temp_data': 'temp_data',
        }

    def _define_workdir(self) -> Path:
        """Define the working directory.

        Returns:
            Path: The path object of the working directory.
        """
        if self.parent_dir:
            return Path(self.parent_dir, self.ticket_number).resolve()
        return Path(Path.cwd(), 'workdir', self.ticket_number).resolve()

    def get_dir(self, dir_name: str) -> Path:
        """Get a directory path by name.

        Args:
            dir_name (str): The directory name key.

        Returns:
            Path: The resolved path to the directory.

        Raises:
            KeyError: If the directory name is not found.
        """
        if dir_name not in self._directory_structure:
            raise KeyError(f"Directory '{dir_name}' not found in structure")

        dir_path = self._directory_structure[dir_name]

        # Handle relative paths that start with ../
        if dir_path.startswith('../'):
            base_path = Path(self.parent_dir).resolve()
            relative_path = dir_path[3:]  # Remove '../'
            return (base_path / relative_path).resolve()

        return (self.workdir / dir_path).resolve()

    def create_dir(self, dir_name: str, custom_path: str = None) -> Path:
        """Create a single directory.

        Args:
            dir_name (str): The directory name key or custom name.
            custom_path (str, optional): Custom path relative to workdir.

        Returns:
            Path: The created directory path.
        """
        dir_path = (self.workdir / custom_path).resolve() if custom_path else self.get_dir(dir_name)

        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def create_dirs(self, dir_names: list[str] = None, custom_dirs: list[str, str] = None) -> list[str, Path]:
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
        default_dirs = ['log_files', 'dataset', 'dataset_files', 'dataset_metadata', 'temp_data', 'db']
        created_dirs = self.create_dirs(default_dirs)

        # Setup logging after log directory is created
        CustomLogger.setup_logging(log_file_dir=created_dirs['log_files'])
        self.logger.print(f'The working directory is: {self.workdir}')

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

    # Backward compatibility properties
    @property
    def log_files_dir(self) -> Path:
        """Get log files directory path."""
        return self.get_dir('log_files')

    @property
    def db_dir(self) -> Path:
        """Get database directory path."""
        return self.get_dir('db')
