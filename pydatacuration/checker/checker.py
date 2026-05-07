"""The checker module provides functions to check the validity of data files and metadata."""

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
from pydatacuration.utils.directory_manager import DirectoryManager


class Checker:
    """Checker class to validate the data files and metadata."""

    def __init__(
        self,
        ds_metadata: dict,
        db_instance: DatabaseBackend,
        setup_form_instance: SetupForm,
        directory_manager_instance: DirectoryManager,
    ) -> None:
        """Initialize the Checker class.

        Args:
            ds_metadata (dict): The dataset metadata.
            db_instance (DatabaseBackend): A database backend instance for database operations.
            setup_form_instance (SetupForm | None): An instance of the setup form.
            directory_manager_instance (DirectoryManager): An instance of the directory manager.
        """
        self.base_url = str(setup_form_instance.base_url)
        self.api_token = str(setup_form_instance.api_token)
        self.ds_metadata = ds_metadata
        self.collection_alias = setup_form_instance.collection_alias

        # Initialize the directory manager
        self.directory_manager = directory_manager_instance

        # API calls service
        self.dataverse_client = DataverseClient(HTTPXClient(self.base_url, self.api_token))

        # Initialize the check result writer
        self.check_result_writer = CheckResultWriter(db_instance)

        self.metadata_checker = MetadataChecker(ds_metadata, self.check_result_writer)

        self.file_name_checker = FileNameChecker(ds_metadata, self.check_result_writer)

        self.file_access_checker = FileAccessChecker(ds_metadata, self.check_result_writer)

        self.file_open_checker = FileOpenChecker(
            ds_metadata=ds_metadata,
            check_zip=setup_form_instance.check_zip,
            check_result_writer=self.check_result_writer,
            directory_manager=self.directory_manager,
        )

        # Misc checker for checks that do not fit into other categories
        self.misc_checker = MiscChecker(
            ds_metadata=ds_metadata,
            check_result_writer=self.check_result_writer,
            dataverse_client_instance=self.dataverse_client,
        )

        # File format checker
        self.file_format_checker = FileFormatChecker(
            ds_metadata=ds_metadata,
            res_dir=setup_form_instance.res_dir,
            check_result_writer=self.check_result_writer,
            directory_manager=self.directory_manager,
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
