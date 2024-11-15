# pylint: disable=C0301

import os

class DirectoryManager:
    """This class is used to manage the directories in the project
    """

    def __init__(self, workdir: str = None):
        """Initialize the class

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
        self.workdir = dir_path if dir_path and os.path.exists(dir_path) else os.path.join(os.getcwd(), 'workdir')
        if not os.path.exists(dir_path):
            print(f"The user defined directory does not exist. The current directory will be used: {self.workdir}")

    def _mk_log_dir(self):
        """Create the log directory
        """
        log_files_dir = os.path.join(self.workdir, 'log_files', 'temp_data')
        os.makedirs(log_files_dir, exist_ok=True)

        return log_files_dir

    def _mk_ds_dir(self):
        """Create the dataset directory
        """
        dir_path_list = [
            os.path.join(self.workdir, 'dataset'),
            os.path.join(self.workdir, 'dataset', 'files'),
            os.path.join(self.workdir, 'dataset', 'metadata')
        ]

        for dir_path in dir_path_list:
            os.makedirs(dir_path, exist_ok=True)

        return dir_path_list[0]

    def _mk_temp_dir(self):
        """Create the temp directory
        """
        temp_data_dir = os.path.join(self.workdir, 'temp_data')
        os.makedirs(temp_data_dir, exist_ok=True)

        return temp_data_dir

    def make_dirs(self):
        """Create the directories
        """
        log_files_dir = self._mk_log_dir()
        ds_dir = self._mk_ds_dir()
        temp_data_dir = self._mk_temp_dir()
        print('\nWorkdir created')
        return self.workdir, log_files_dir, ds_dir, temp_data_dir
