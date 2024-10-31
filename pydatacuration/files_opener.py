# pylint: disable=C0301
import os
from pathlib import Path
from PIL import Image
import chardet
import netCDF4 as nc

class FilesOpener:
    def __init__(self, file):
        self.file = file

    def _get_file_encoding(self):
        """Check the file encoding
        
        Returns:
            str: The file encoding.
        """
        with open(self.file, 'rb') as f:
            return chardet.detect(f.read()).get('encoding', None)

    def _open_image_file(self):
        """Open an image file
        
        Returns:
            Image: The image object.
        """
        try:
            Image.open(self.file)
            return True, self.file
        except (ValueError, Image.UnidentifiedImageError, OSError):
            return False, self.file
    
    def _open_netcdf_file(self):
        """Open a NetCDF file
        
        Returns:
            str: The NetCDF file object.
        """
        try:
            nc.Dataset(self.file, 'r')
            return True, self.file
        except (Exception, OSError):
            return False, self.file

    def open_file(self):
        """Open a file
        
        Returns:
            str: The file object
        """
        if os.path.isfile(self.file):
            file_ext = Path(self.file).suffix
            image_file_list = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'] # TODO: 1. Add more image file extensions; 2. Use a function to allow import a list from a configuration file;
            # text_file_list = ['.txt', '.csv', '.tsv'] TODO: Placeholder for text file extensions
            netcdf_file_list = ['.nc']
            if file_ext.lower() in image_file_list:
                return self._open_image_file()

            if file_ext.lower() in netcdf_file_list:
                return self._open_netcdf_file()
        return None, self.file