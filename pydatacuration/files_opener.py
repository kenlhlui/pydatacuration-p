import csv
import logging
import os
from pathlib import Path

import chardet
import ffmpeg
import netCDF4 as nc
import pandas as pd
import pypdf
import pypdf.errors
import pyreadr
import shapefile
from PIL import Image
from pyreadstat import ReadstatError
from pyreadstat import pyreadstat

from ffmepg_file_formats import FFmpegFileFormats


IMAGE_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']
NETCDF_FILE_EXTENSIONS = ['.nc']
# TEXT_FILE_EXTENSIONS = ['.txt', '.csv', '.tsv']  # Placeholder for text file extensions
SAV_FILE_EXTENSIONS = ['.sav']  # Placeholder for SPSS file extensions
CSV_FILE_EXTENSIONS = ['.csv']  # Placeholder for CSV file extensions
DTA_FILE_EXTENSIONS = ['.dta']  # Placeholder for Stata file extensions
RDATA_FILE_EXTENSIONS = ['.rdata', '.rds']  # Placeholder for R file extensions
FFMEPG_FILE_EXTENSIONS = FFmpegFileFormats().get_ffmpeg_formats()
SHAPE_FILE_EXTENSIONS = ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.shp.xml', '.cpg']
SPREADSHEET_FILE_EXTENSIONS = ['.xls', '.xlsx', '.xlsm', '.xlsb', '.odf', '.ods', '.odt']
PDF_FILE_EXTENSIONS = ['.pdf']

class FilesOpener:
    """Open different file types."""
    def __init__(self, file: str) -> None:
        """Initialize the FilesOpener class.

        Args:
            file (str): The file path to open.
        """
        self.file = file
        self.pypdf_logger = logging.getLogger('pypdf').setLevel(logging.ERROR)

    def _get_file_encoding(self) -> dict | None:
        """Check the file encoding.

        Returns:
            dict | None: The file encoding.
        """
        with open(self.file, 'rb') as f:
            return chardet.detect(f.read()).get('encoding', None)

    def _open_image_file(self) -> tuple:
        """Open an image file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            Image.open(self.file)
            return True, self.file
        except (ValueError, Image.UnidentifiedImageError, OSError):
            return False, self.file

    def _open_netcdf_file(self) -> tuple:
        """Open a NetCDF file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            nc.Dataset(self.file, 'r')
            return True, self.file
        except (Exception, OSError):
            return False, self.file

    def _open_sav_file(self) -> tuple:
        """Open an sav (SPSS) file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            sav_file = pyreadstat.read_sav(self.file)
            return True, sav_file
        except (ReadstatError, OSError):
            return False, self.file

    def _open_csv_file(self) -> tuple:
        """Open a CSV file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            with open(self.file, 'r') as f:
                csv_reader = csv.reader(f)
                for row in csv_reader:
                    pass
            return True, self.file
        except (csv.Error, UnicodeDecodeError):
            return False, self.file

    def _open_dta_file(self):
        """Open a DTA (Stata) file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            dta_file = pyreadstat.read_dta(self.file)
            return True, dta_file
        except (ReadstatError, OSError):
            return False, self.file

    def _open_rdata_file(self) -> tuple:
        """Open an RData file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            rdata_file = pyreadr.read_r(self.file)
            return True, rdata_file
        except (pyreadr.custom_errors.PyreadrError, pyreadr.custom_errors.LibrdataError, OSError):
            return False, self.file

    def _open_audiovisual_file(self) -> tuple:
        try:
            stderr = (
                ffmpeg
                .input(self.file)
                .output('null', f='null')
                .global_args('-v', 'error')
                .run(capture_stdout=False, capture_stderr=True)
            )

            if stderr[1] == b'':
                return True, self.file
            return False, self.file

        except ffmpeg.Error:
            return False, self.file

    def _open_shape_file(self) -> tuple:
        """Open a shape file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            result = shapefile.Reader(self.file)
            if result:
                return True, result

            return False, self.file

        except shapefile.ShapefileException:
            return False, self.file

    def _open_spreadsheet_file(self) -> tuple:
        """Open a spreadsheet file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            df = pd.read_excel(self.file)
            if df is not None:
                return True, self.file
            return False, self.file
        except (pd.errors.ParserError, OSError, ValueError):
            return False, self.file

    def _open_pdf_file(self) -> tuple:
        """Open a PDF file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            pypdf.PdfReader(self.file, strict=True)
            return True, self.file
        except pypdf.errors.PdfReadError:
            return False, self.file

    def open_file(self):
        """Open a file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        if Path.is_file(Path(self.file)):
            file_ext = Path(self.file).suffix.lower()
            if file_ext in IMAGE_FILE_EXTENSIONS:
                status, file_path = self._open_image_file()
                return status, file_path
            if file_ext in NETCDF_FILE_EXTENSIONS:
                status, file_path = self._open_netcdf_file()
                return status, file_path
            if file_ext in SAV_FILE_EXTENSIONS:
                status, file_path = self._open_sav_file()
                return status, file_path
            if file_ext in CSV_FILE_EXTENSIONS:
                status, file_path = self._open_csv_file()
                return status, file_path
            if file_ext in DTA_FILE_EXTENSIONS:
                status, file_path = self._open_dta_file()
                return status, file_path
            if file_ext in RDATA_FILE_EXTENSIONS:
                status, file_path = self._open_rdata_file()
                return status, file_path
            if file_ext in FFMEPG_FILE_EXTENSIONS:
                status, file_path = self._open_audiovisual_file()
                return status, file_path
            if file_ext in SHAPE_FILE_EXTENSIONS:
                status, file_path = self._open_shape_file()
                return status, file_path
            if file_ext in SPREADSHEET_FILE_EXTENSIONS:
                status, file_path = self._open_spreadsheet_file()
                return status, file_path
            if file_ext in PDF_FILE_EXTENSIONS:
                status, file_path = self._open_pdf_file()
                return status, file_path
        return None, self.file
