import os
from pathlib import Path
from PIL import Image

class FilesOpener:
    def __init__(self, file):
        self.file = file

    def open_image_file(self):
        """Open an image file
        
        Returns:
            Image: The image object.
        """
        image_file_list = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']
        file_ext = Path(self.file).suffix
        if file_ext and file_ext.lower() in image_file_list:
            try:
                result = Image.open(self.file)
                result.crop((0, 0, 100, 100))
                return True
            except (ValueError, Image.UnidentifiedImageError, OSError):
                return False
