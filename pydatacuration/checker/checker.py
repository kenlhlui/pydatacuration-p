"""The checker module provides functions to check the validity of data files and metadata."""

from pathlib import Path

from loguru import logger

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.checker.check_result_writer import CheckResultWriter
from pydatacuration.checker.file_access_checker import FileAccessChecker
from pydatacuration.checker.file_format_checker import FileFormatChecker
from pydatacuration.checker.file_name_checker import FileNameChecker
from pydatacuration.checker.metadata_checker import MetadataChecker
from pydatacuration.checker.misc_checker import MiscChecker
from pydatacuration.checker.services.files_opener import FilesOpener
from pydatacuration.db.base import DatabaseBackend
from pydatacuration.services.api_calls.call_dv import DVAPICalls
from pydatacuration.services.api_calls.httpx_client import HTTPXClient
from pydatacuration.utils.search_ds_meta import get_ds_title
from pydatacuration.utils.search_ds_meta import get_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_name_from_file_list_metadata
from pydatacuration.utils.search_ds_meta import get_file_rel_path_from_file_list_metadata
from pydatacuration.utils.unzip import Unzipper


RES_DIR = Path('res')


class Checker:
    """Checker class to validate the data files and metadata."""

    def __init__(
        self,
        ds_metadata: dict,
        workdir: Path,
        db_instance: DatabaseBackend,
        setup_form_instance: SetupForm,
    ) -> None:
        """Initialize the Checker class.

        Args:
            ds_metadata (dict): The dataset metadata.
            workdir (Path): The working directory.
            db_instance (DatabaseBackend): A database backend instance for database operations.
            setup_form_instance (SetupForm | None): An instance of the setup form.
        """
        self.base_url = str(setup_form_instance.base_url) if setup_form_instance.base_url else ''
        self.api_token = str(setup_form_instance.api_token) if setup_form_instance.api_token else ''
        self.ds_metadata = ds_metadata
        self.workdir = workdir
        self.check_zip = setup_form_instance.check_zip
        self.collection_alias = setup_form_instance.collection_alias

        self.file_list_metadata = get_file_list_metadata(self.ds_metadata)

        # API calls service
        self.httpx_client = HTTPXClient(self.base_url, self.api_token)
        self.dv_api_calls = DVAPICalls(httpx_client=self.httpx_client)

        self.db_instance = db_instance
        self.sqlmodels = self.db_instance.models
        self.check_result_writer = CheckResultWriter(db_instance=self.db_instance)

        self.files_opener = FilesOpener
        self.metadata_checker = MetadataChecker(self.ds_metadata, self.check_result_writer)

        self.file_name_checker = FileNameChecker(self.file_list_metadata, self.check_result_writer)

        self.file_access_checker = FileAccessChecker(self.check_result_writer)

        # Misc checker for checks that do not fit into other categories
        self.misc_checker = MiscChecker(
            ds_metadata=self.ds_metadata,
            check_result_writer=self.check_result_writer,
            dv_api_calls_instance=self.dv_api_calls,
        )

        # File format checker
        self.file_format_checker = FileFormatChecker(
            self.file_list_metadata,
            self.check_result_writer,
            res_dir=RES_DIR,
            workdir=self.workdir,
        )

        self.ds_title = get_ds_title(self.ds_metadata)
        self.dataset_id = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('id')

    def check_file_open(self) -> None:
        """Check if the file can be opened."""
        file_list = []
        inaccessible_files = []
        unsupported_files = []

        # To generate paths for the relative files in the dataset
        for file in self.file_list_metadata:
            file_name = get_file_name_from_file_list_metadata(file)
            file_rel_path = get_file_rel_path_from_file_list_metadata(file, file_name)
            file_list.append(file_rel_path)

        # Unzip the files and append the unzipped files to the file_list
        zip_file_extensions = {'.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.gz', '.bz2', '.xz', '.7z', '.zip'}
        if self.check_zip:
            for file_rel_path in file_list[:]:  # Iterate over a copy of the list
                if file_rel_path.suffix in zip_file_extensions:
                    # Upper case the suffix and remove the leading dot
                    extracted_file_rel_paths = Unzipper(
                        zip_file=Path(self.workdir, 'dataset', 'files', file_rel_path),
                        output_dir=Path(
                            self.workdir,
                            'dataset',
                            'files',
                            '__UNZIPED_FILES__',
                            f'{file_rel_path.stem}_{file_rel_path.suffix[1:].upper()}',
                        ),
                    ).main()
                    file_list.extend(extracted_file_rel_paths)
        # Only show the message if there's zip file(s) in the dataset
        elif not self.check_zip and any(file_rel_path.suffix in zip_file_extensions for file_rel_path in file_list):
            logger.info(
                'Skipping the unzipping of zip file(s). The zip file(s) and the content inside will not be checked.'
            )  # noqa: E501

        for file_rel_path in file_list:
            file_abs_path = Path(self.workdir, 'dataset', 'files', file_rel_path)
            # Pass if the file is a zip file
            if file_rel_path.suffix not in zip_file_extensions:
                if self.files_opener(file_abs_path).open_file()[0] is False:
                    logger.info(f'File cannot be opened: {file_abs_path}')
                    inaccessible_files.append(str(file_rel_path))
                elif self.files_opener(file_abs_path).open_file()[0] is None:
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

    def run_checks(self) -> None:
        """Run all the checks."""
        logger.info('Running the checks...')
        self.file_name_checker.check_file_name_with_special_char()
        self.file_name_checker.check_file_missing_extension()
        self.file_name_checker.check_readme_file()

        self.file_format_checker.check_common_file_format()
        self.check_file_open()

        self.metadata_checker.check_terms_of_use()
        self.metadata_checker.check_terms_of_access()
        self.metadata_checker.check_keywords()
        self.metadata_checker.check_license()
        self.metadata_checker.check_related_publications()
        self.metadata_checker.check_related_datasets()
        self.metadata_checker.check_data_sources()

        self.metadata_checker.check_missing_required_fields()
        self.metadata_checker.check_missing_author_affiliation()
        self.metadata_checker.check_missing_author_identifier()
        self.metadata_checker.check_missing_author_identifier_scheme()

        self.file_access_checker.check_restricted_files(self.ds_metadata)
        self.misc_checker.check_depositor_record(collection_alias=self.collection_alias)
        self.misc_checker.check_spelling()
