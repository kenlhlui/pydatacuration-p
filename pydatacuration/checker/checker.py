"""The checker module provides functions to check the validity of data files and metadata."""

from pathlib import Path

from loguru import logger

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.checker.check_result_writer import CheckResultWriter
from pydatacuration.checker.file_access_checker import FileAccessChecker
from pydatacuration.checker.file_format_checker import FileFormatChecker
from pydatacuration.checker.file_name_checker import FileNameChecker
from pydatacuration.checker.file_open_checker import FileOpenChecker
from pydatacuration.checker.metadata_checker import MetadataChecker
from pydatacuration.checker.misc_checker import MiscChecker
from pydatacuration.db.base import DatabaseBackend
from pydatacuration.services.api_calls.dataverse_client import DataverseClient
from pydatacuration.services.api_calls.httpx_client import HTTPXClient


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

        # API calls service
        self.httpx_client = HTTPXClient(self.base_url, self.api_token)
        self.dv_api_calls = DataverseClient(httpx_client=self.httpx_client)

        self.db_instance = db_instance
        self.check_result_writer = CheckResultWriter(db_instance=self.db_instance)

        self.metadata_checker = MetadataChecker(self.ds_metadata, self.check_result_writer)

        self.file_name_checker = FileNameChecker(self.ds_metadata, self.check_result_writer)

        self.file_access_checker = FileAccessChecker(self.ds_metadata, self.check_result_writer)

        self.file_open_checker = FileOpenChecker(
            ds_metadata=self.ds_metadata,
            check_zip=self.check_zip,
            workdir=self.workdir,
            check_result_writer=self.check_result_writer,
        )

        # Misc checker for checks that do not fit into other categories
        self.misc_checker = MiscChecker(
            ds_metadata=self.ds_metadata,
            check_result_writer=self.check_result_writer,
            dv_api_calls_instance=self.dv_api_calls,
        )

        # File format checker
        self.file_format_checker = FileFormatChecker(
            self.ds_metadata,
            self.check_result_writer,
            res_dir=RES_DIR,
            workdir=self.workdir,
        )

    def run_checks(self) -> None:
        """Run all the checks."""
        logger.info('Running the checks...')

        self.file_name_checker.check_file_name_with_special_char()
        self.file_name_checker.check_file_missing_extension()
        self.file_name_checker.check_readme_file()

        self.file_format_checker.check_common_file_format()

        self.file_open_checker.check_file_open()

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

        self.file_access_checker.check_restricted_files()
        self.misc_checker.check_depositor_record(collection_alias=self.collection_alias)
        self.misc_checker.check_spelling()
