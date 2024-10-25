import os
from pathlib import Path
import re
import sys
import deepdiff
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

class FileNameFormatChecker:
    """This class is used to check the file name format
    """

    def __init__(self):
        pass

    def check_special_char(self, file):
        """Check if the file name contains special characters

        Args:
            file (str): The path to the file.
        
        Returns:
            tuple: The file path and a boolean value.
        """
        if re.search(r'[^\w\s]', Path(file).stem):
            return file, True
        return file, False

    def check_file_name_len(self, file, file_name_max_len: int):
        """Check if the file name is longer than the maximum length

        Args:
            file (str): The path to the file.
            file_name_max_len (int): The maximum length of the file name.
        
        Returns:
            tuple: The file path and a boolean value.
        """

        if len(Path(file).stem) > file_name_max_len:
            return file, True
        return file, False

    def check_file_ext(self, file):
        """Check if the file has an extension

        Args:
            file (str): The path to the file.
        
        Returns:
            tuple: The file path and a boolean value.
        """

        if Path(file).suffix:
            return file, True
        return file, False

    def check_flie_preferred_format(self, file: str, preffered_file_formats_config: str):
        """
        Check if the file format is in the preferred file formats list.

        Args:
            file (str): The path to the file.
        
        Returns:
            tuple: The file path and a boolean value.
        """

        def load_preferred_file_formats_list(preffered_file_formats_config: str):
            """
            Load the list of preferred file formats from the configuration .txt file.

            Args:
                file (str): The path to the text file.

            Returns:
                list: A list of lines in the text file without newline characters.
            """
            try:
                with open(preffered_file_formats_config, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f.readlines()]
            except FileNotFoundError as e:
                print(f"Error: {e}")
                sys.exit(1)

        if Path(file).suffix in load_preferred_file_formats_list(preffered_file_formats_config):
            return file, True
        return file, False

def readme_file_checker(file: str):
    """Check if the file is a README file

    Args:
        file (str): The path to the file.
    
    Returns:
        tuple: The file path and a boolean value.
    """
    if re.search(r'readme', file, re.IGNORECASE):
        return file, True
    return file, False

def compare_files_and_metadata(dl_files_checksums, metadata_files_cehcksums):
    """Compare the downloaded files checksums and the metadata JSON file checksums

    Args:
        dl_files_checksums (list): A list of dictionaries containing the file path and the checksum.
        metadata_files_cehcksums (list): A list of dictionaries containing the file path and the checksum.

    Returns:
        bool: True if the downloaded files and the metadata JSON file checksums are the same, False otherwise.
    """
    diff = deepdiff.DeepDiff(dl_files_checksums, metadata_files_cehcksums, ignore_order=True)
    if diff:
        print('The downloaded files and the file list metadata are different.')
        with open('log_files/diff.txt', 'w', encoding='utf-8') as f:
            f.write(str(diff))
        sys.exit(1)
        
    else:
        print('The downloaded files and the file list metadata are the same.')
        return False
