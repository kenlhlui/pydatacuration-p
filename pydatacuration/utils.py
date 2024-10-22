import os
from pathlib import Path
class DirectoryManager:
    """This class is used to manage the directories in the project
    """

    def __init__(self):
        self.log_files_dir_path = r'./log_files/temp_data'
        self.dir_path_list = [r'./dataset', r'./dataset/files', r'./dataset/metadata']
        self.temp_data_dir = r'./temp_data'

    def mk_log_dir(self):
        """Create the log directory
        """
        os.makedirs(self.log_files_dir_path, exist_ok=True)

    def mk_ds_dir(self):
        """Create the dataset directory
        """
        for dir_path in self.dir_path_list:
            os.makedirs(dir_path, exist_ok=True)

    def mk_temp_dir(self):
        """Create the temp directory
        """
        os.makedirs(self.temp_data_dir, exist_ok=True)

# Export the structure ('tree') of a directory as plain text
def list_files(startpath):
    """List the files in the directory
    """
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))


def get_file_name(file):
    """Get the file name from the file path
    """
    return Path(file).stem

def get_file_extension(file):
    """Get the file extension from the file path
    """
    return Path(file).suffix
