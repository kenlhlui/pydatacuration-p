# pylint: disable=C0301
import os
from pathlib import Path
from PIL import Image
import chardet

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

    def open_image_file(self):
        """Open an image file
        
        Returns:
            Image: The image object.
        """
        image_file_list = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'] # TODO: 1. Add more image file extensions; 2. Use a function to allow import a list from a configuration file;
        file_ext = Path(self.file).suffix
        if file_ext and file_ext.lower() in image_file_list:
            try:
                Image.open(self.file)
                return True, self.file
            except (ValueError, Image.UnidentifiedImageError, OSError):
                return False, self.file
    def open_text_file(self):
        """Open a text file and return the encoding of the file
        
        Returns:
            str: The text content.
        """
        text_file_list = ['.txt', '.csv', '.tsv']
        file_ext = Path(self.file).suffix
        if file_ext and file_ext.lower() in text_file_list:
            encoding = self._get_file_encoding()  # Check the file encoding
            try:
                with open(self.file, 'r', encoding=encoding):
                    return True, self.file, encoding
            except (Exception, UnicodeDecodeError):
                return False, self.file, None
        return False, self.file, None
