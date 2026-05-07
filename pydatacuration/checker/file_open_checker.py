"""Class for checking if files in the dataset can be opened."""

from pathlib import Path

from loguru import logger

from pydatacuration.checker.check_result_writer import CheckResultWriter
from pydatacuration.checker.services.files_opener import FilesOpener
from pydatacuration.utils.search_ds_meta import get_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_name_from_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_rel_path_from_file_list_metadata
from pydatacuration.utils.unzip import Unzipper


class FileOpenChecker:
    """Class for checking if files in the dataset can be opened."""

    def __init__(self, check_result_writer: CheckResultWriter) -> None:
        """Initialize the class."""
        self.check_result_writer = check_result_writer
        self.files_opener = FilesOpener

    def check_file_open(self, ds_metadata: dict, check_zip: bool, workdir: Path) -> None:
        """Check if the file can be opened."""
        file_list = []
        inaccessible_files = []
        unsupported_files = []
        # Get the file list metadata from the dataset metadata
        file_list_metadata = get_file_list_metadata(ds_metadata)

        # To generate paths for the relative files in the dataset
        for file in file_list_metadata:
            file_name = get_file_name_from_file_list_metadata(file)
            file_rel_path = get_file_rel_path_from_file_list_metadata(file, file_name)
            file_list.append(file_rel_path)

        # Unzip the files and append the unzipped files to the file_list
        zip_file_extensions = {'.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.gz', '.bz2', '.xz', '.7z', '.zip'}
        if check_zip:
            for file_rel_path in file_list[:]:  # Iterate over a copy of the list
                if file_rel_path.suffix in zip_file_extensions:
                    # Upper case the suffix and remove the leading dot
                    extracted_file_rel_paths = Unzipper(
                        zip_file=Path(workdir, 'dataset', 'files', file_rel_path),
                        output_dir=Path(
                            workdir,
                            'dataset',
                            'files',
                            '__UNZIPED_FILES__',
                            f'{file_rel_path.stem}_{file_rel_path.suffix[1:].upper()}',
                        ),
                    ).main()
                    file_list.extend(extracted_file_rel_paths)
        # Only show the message if there's zip file(s) in the dataset
        elif not check_zip and any(file_rel_path.suffix in zip_file_extensions for file_rel_path in file_list):
            logger.info(
                'Skipping the unzipping of zip file(s). The zip file(s) and the content inside will not be checked.'
            )  # noqa: E501

        for file_rel_path in file_list:
            file_abs_path = Path(workdir, 'dataset', 'files', file_rel_path)
            # Pass if the file is a zip file
            if file_rel_path.suffix not in zip_file_extensions:
                result, *_ = self.files_opener(file_abs_path).open_file()
                if result is False:
                    logger.info(f'File cannot be opened: {file_abs_path}')
                    inaccessible_files.append(str(file_rel_path))
                elif result is None:
                    logger.info(f'File is not a supported file format (not checked by the script): {file_abs_path}')  # noqa: E501
                    unsupported_files.append(str(file_rel_path))

        self.check_result_writer.write(
            check_id='file_accessibility',
            check_name='File accessibility report',
            description='Files that cannot be opened or read by the validation tool',
            unit='file',
            results=inaccessible_files,
        )

        self.check_result_writer.write(
            check_id='unsupported_files',
            check_name='Files in unsupported formats by the validation tool',
            description='Files in formats not supported by the validation tool',
            unit='file',
            results=unsupported_files,
        )
