# pylint: disable=C0301
import glob
import os
import re
import sys
import zipfile
from pathlib import Path

import deepdiff
import dotenv
import seedir as sd


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
            return file, False # TODO: unify the logic for returns
        return file, True

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

def compare_files_and_metadata(dl_files_checksums, metadata_files_cehcksums, workddir):
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
        with open(f'{workddir}/log_files/diff.txt', 'w', encoding='utf-8') as f:
            f.write(str(diff))
        print(f'See the {workddir}/log_files/diff.txt file for the differences.')
        sys.exit(1)

    else:
        print('The downloaded files and the file list metadata are the same.')
        return False

def unzip_file(ds_zip_path: str, target_dir: str):
    """Unzip the file

    Args:
        zip_file (str): The path to the zip file.
        target_dir (str): The path to the target directory.
    
    Returns:
        None
    """

    def move_maifest_file(target_dir: str):
        """Move the MAIFEST.TXT file to the metadata directory

        Args:
            target_dir (str): The path to the target directory.
        
        Returns:
            None
        """
        manifest_files = glob.glob(f'{target_dir}/MANIFEST.*', recursive=True)

        if manifest_files:
            manifest_file = manifest_files[0] # Take the first match
            try:
                parent_dir = os.path.dirname(target_dir)
                os.replace(manifest_file, f'{parent_dir}/metadata/{Path(manifest_file).name}')
            except FileNotFoundError as e:
                print(f"Error: {e}")
        else:
            print("Error: MANIFEST file not found.")

    try:
        with zipfile.ZipFile(ds_zip_path, 'r') as zipf:
            zipf.extractall(target_dir)
            move_maifest_file(target_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print('The zip file does not exist.')
        sys.exit(1)

def combine_list_items(item: list):
    """Combine the list items into a single string

    Args:
        items (list): The list of items to combine.
    
    Returns:
        str: The combined string.
    """
    return ' '.join(item)


def gen_tree_diagram(target_dir: Path, save_dir: Path) -> None:
    """Generate the tree diagram of the directory.

    Args:
        target_dir (Path): The directory path to the target directory.
        save_dir (Path): The directory path to save the tree diagram text (.txt) file`.
    """
    try:
        if Path.exists(target_dir):
            result = sd.seedir(target_dir, style='lines', printout=False, first='files')

            ds_tree_file_path = Path(save_dir, 'ds_tree.txt')

            with Path(ds_tree_file_path).open('w', encoding='utf-8') as f:
                f.write(result)

            print(f'Folder tree diagram text file saved at: {ds_tree_file_path}')
        else:
            print('The target directory does not exist. Exiting...')
            sys.exit(1)

    except Exception as e:
        print(f'Error: {e}')
        print('An error occurred while generating the folder tree diagram. Exiting...')
        sys.exit(1)

def load_env(base_url, api_token):
    dotenv.load_dotenv()
    if base_url is None:
        base_url = os.getenv('BASE_URL')
        if base_url is None:
            sys.exit('BASE_URL not found in the environment variables. Exiting...')
    if api_token is None:
        api_token = os.getenv('API_TOKEN')
        if api_token is None:
            sys.exit('API_TOKEN not found in the environment variables. Exiting...')
    print('Environment variables loaded')
    return base_url, api_token