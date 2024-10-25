import os
import hashlib

class Checksum():
    """This class is used to generate the checksum of the files in the dataset directory
    """

    def _get_md5(self, file):
        with open(file, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def gen_ds_files_checksum(self, target_dir):
        """Generate the checksum of the files in the dataset directory

        Args:
            target_dir (str): The path to the dataset directory.
        
        Returns:
            list: A list of dictionaries containing the file path and the checksum.
        """
        dl_file_checksum_nested_list = []
        os_walk_object = os.walk(target_dir)
        for root, dirs, files in os_walk_object:
            for file in files:
                file_path = os.path.join(root, file).replace('\\', '/').replace('dataset/files/', '')
                dl_file_checksum_nested_list.append({
                    'file': file_path,
                    'md5_checksum': self._get_md5(rf'{root}/{file}')
                })

        return dl_file_checksum_nested_list
