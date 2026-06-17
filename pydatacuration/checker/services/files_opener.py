"""Open different file types."""

import csv
from pathlib import Path

import ffmpeg
import netCDF4 as nc
import pandas as pd
import pypdf
import pypdf.errors
import pyreadr
import shapefile
from loguru import logger
from PIL import Image
from pyreadstat import ReadstatError
from pyreadstat import pyreadstat

from pydatacuration.utils.ffmepg_file_formats import FFmpegFileFormats


IMAGE_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']
NETCDF_FILE_EXTENSIONS = ['.nc']
# TEXT_FILE_EXTENSIONS = ['.txt', '.csv', '.tsv']  # Placeholder for text file extensions
SAV_FILE_EXTENSIONS = ['.sav']  # Placeholder for SPSS file extensions
CSV_FILE_EXTENSIONS = ['.csv']  # Placeholder for CSV file extensions
TSV_FILE_EXTENSIONS = ['.tsv']  # Placeholder for TSV file extensions
DTA_FILE_EXTENSIONS = ['.dta']  # Placeholder for Stata file extensions
RDATA_FILE_EXTENSIONS = ['.rdata', '.rds']  # Placeholder for R file extensions
FFMEPG_FILE_EXTENSIONS = FFmpegFileFormats().get_ffmpeg_formats()
SHAPE_FILE_EXTENSIONS = ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.shp.xml', '.cpg']
SPREADSHEET_FILE_EXTENSIONS = ['.xls', '.xlsx', '.xlsm', '.xlsb', '.odf', '.ods', '.odt']
PDF_FILE_EXTENSIONS = ['.pdf']


class FilesOpener:
    """Open different file types.

    Note: if the file can be correctly opened, return a tuple of (True, file_path). Otherwise, return (False, file_path).

    """

    def __init__(self, file: str | Path) -> None:
        """Initialize the FilesOpener class.

        Args:
            file (str | Path): The file path to open.
        """
        self.file = file

    def _open_image_file(self) -> tuple:
        """Open an image file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            with Image.open(self.file) as _img:
                pass
            return True, self.file
        except (ValueError, Image.UnidentifiedImageError, OSError) as e:
            logger.error(f'Error reading image file: {e}')
            return False, self.file

    def _open_netcdf_file(self) -> tuple:
        """Open a NetCDF file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            nc.Dataset(self.file, 'r')
            return True, self.file
        except (Exception, OSError) as e:
            logger.error(f'Error reading NetCDF file: {e}')
            return False, self.file

    def _open_sav_file(self) -> tuple:
        """Open an sav (SPSS) file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            sav_file = pyreadstat.read_sav(self.file)
            return True, sav_file
        except (ReadstatError, OSError) as e:
            logger.error(f'Error reading SAV file: {e}')
            return False, self.file

    def _open_csv_file(self) -> tuple:
        """Open a CSV file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            with Path(self.file).open('r') as f:
                csv_reader = csv.reader(f)
                for _row in csv_reader:
                    pass
            return True, self.file
        except (csv.Error, UnicodeDecodeError) as e:
            logger.error(f'Error reading CSV file: {e}')
            return False, self.file

    def _open_tsv_file(self) -> tuple:
        """Open a TSV file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            with Path(self.file).open('r') as f:
                tsv_reader = csv.reader(f, delimiter='\t')
                for _row in tsv_reader:
                    pass
            return True, self.file
        except (csv.Error, UnicodeDecodeError) as e:
            logger.error(f'Error reading TSV file: {e}')
            return False, self.file

    def _open_dta_file(self) -> tuple:
        """Open a DTA (Stata) file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            dta_file = pyreadstat.read_dta(self.file)
            return True, dta_file
        except (ReadstatError, OSError) as e:
            logger.error(f'Error reading DTA file: {e}')
            return False, self.file

    def _open_rdata_file(self) -> tuple:
        """Open an RData file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            rdata_file = pyreadr.read_r(self.file)
            return True, rdata_file
        except (pyreadr.custom_errors.PyreadrError, pyreadr.custom_errors.LibrdataError, OSError) as e:
            logger.error(f'Error reading RData file: {e}')
            return False, self.file

    def _open_audiovisual_file(self) -> tuple:
        try:
            stderr = (
                ffmpeg.input(self.file)
                .output('null', f='null')
                .global_args('-v', 'error')
                .run(capture_stdout=False, capture_stderr=True)
            )

            if stderr[1] == b'':
                return True, self.file
            return False, self.file

        except ffmpeg.Error as e:
            logger.error(f'Error reading audiovisual file: {e}')
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

        except shapefile.ShapefileException as e:
            logger.error(f'Error reading shape file: {e}')
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
        except (pd.errors.ParserError, OSError, ValueError) as e:
            logger.error(f'Error reading spreadsheet file: {e}')
            return False, self.file

    def _open_pdf_file(self) -> tuple:
        """Open a PDF file.

        Returns:
            tuple: (bool, str) indicating success and the file path.
        """
        try:
            pypdf.PdfReader(self.file, strict=True)
            return True, self.file
        except pypdf.errors.PdfReadError as e:
            logger.error(f'Error reading PDF file: {e}')
            return False, self.file

    def open_file(self, file_to_check: Path | str | None = None):
        """Open a file and check whether it can be correctly opened by Python.

        Args:
            file_to_check (Path or str, optional): Specific file to check. Defaults to self.file.

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
            if file_ext in TSV_FILE_EXTENSIONS:
                status, file_path = self._open_tsv_file()
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
