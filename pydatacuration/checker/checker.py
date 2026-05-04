"""The checker module provides functions to check the validity of data files and metadata."""

from pathlib import Path

import jmespath
from loguru import logger

from pydatacuration.backend.models.setup_form import SetupForm

# Write to db module
from pydatacuration.checker.check_result_writer import CheckResultWriter

# File Format Checker
from pydatacuration.checker.file_format_checker import FileFormatChecker

# File Name Checker
from pydatacuration.checker.file_name_checker import FileNameChecker

# File Open Checker
from pydatacuration.checker.files_open_checker import FilesOpener

# Metadata Checker
from pydatacuration.checker.metadata_checker import MetadataChecker

# Services
from pydatacuration.checker.services.dataset_tree_info import DatasetTreeInfo
from pydatacuration.checker.spell_checker import SpellCheckerCustomized
from pydatacuration.db.base import DatabaseBackend
from pydatacuration.services.api_calls.call_dv import DVAPICalls
from pydatacuration.services.api_calls.httpx_client import HTTPXClient

# Verify downloaded files
from pydatacuration.services.verify_download_files import VerifyDownloadFiles
from pydatacuration.utils.unzip import Unzipper


RES_DIR = Path('res')


class Checker:
    """Checker class to validate the data files and metadata."""

    def __init__(
        self,
        ds_metadata: dict,
        dv_tree: dict,
        workdir: Path,
        db_instance: DatabaseBackend,
        setup_form_instance: SetupForm,
    ) -> None:
        """Initialize the Checker class.

        Args:
            ds_metadata (dict): The dataset metadata.
            dv_tree (dict): The Dataverse tree metadata.
            workdir (Path): The working directory.
            db_instance (DatabaseBackend): A database backend instance for database operations.
            setup_form_instance (SetupForm | None): An instance of the setup form.
        """
        self.base_url = str(setup_form_instance.base_url) if setup_form_instance.base_url else ''
        self.api_token = str(setup_form_instance.api_token) if setup_form_instance.api_token else ''
        self.ds_metadata = ds_metadata
        self.dv_tree = dv_tree
        self.workdir = workdir
        self.check_zip = setup_form_instance.check_zip
        self.collection_alias = setup_form_instance.collection_alias

        # Verify the downloaded files
        self.verify_download_files_service = VerifyDownloadFiles(target_dir=workdir, ds_metadata=ds_metadata)
        self.file_list_metadata = self.verify_download_files_service.file_list_metadata
        self.verify_download_files_service.verify(workdir)

        # Dataset tree information service
        self.dv_tree_info = DatasetTreeInfo(dv_tree=dv_tree)

        # API calls service
        self.httpx_client = HTTPXClient(self.base_url, self.api_token)
        self.dv_api_calls = DVAPICalls(httpx_client=self.httpx_client)

        self.db_instance = db_instance
        self.sqlmodels = self.db_instance.models
        self.checklist_result = self.sqlmodels.check_results()
        self.checklist_result_writer = CheckResultWriter(db_instance=self.db_instance)

        self.curator_name = setup_form_instance.curator_name
        self.curator_email = setup_form_instance.curator_email
        self.checklist_type = setup_form_instance.checklist

        self.files_opener = FilesOpener
        self.metadata_checker = MetadataChecker(self.ds_metadata, self.checklist_result_writer)
        self.spell_checker = SpellCheckerCustomized()

        self.file_name_checker = FileNameChecker(self.file_list_metadata, self.checklist_result_writer)

        # File format checker
        self.file_format_checker = FileFormatChecker(
            self.file_list_metadata,
            self.checklist_result_writer,
            res_dir=RES_DIR,
            workdir=self.workdir,
        )

        self.ds_title = jmespath.search(
            'data.latestVersion.metadataBlocks.citation.fields[?typeName == `title`].value | [0]', self.ds_metadata
        )
        self.dataset_id = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('id')

    def check_file_open(self) -> None:
        """Check if the file can be opened."""
        file_list = []
        inaccessible_files = []
        unsupported_files = []

        # To generate paths for the relative files in the dataset
        for file in self.file_list_metadata:
            file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
            file_rel_path = Path(file.get('directoryLabel', ''), file_name)
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

        self.checklist_result_writer.write(
            check_id='file_accessibility',
            check_name='File accessibility report',
            description='Files that cannot be opened or read by the validation tool',
            unit='file',
            results=inaccessible_files,
        )

        self.checklist_result_writer.write(
            check_id='unsupported_files',
            check_name='Files in unsupported formats by the validation tool',
            description='Files in formats not supported by the validation tool',
            unit='file',
            results=unsupported_files,
        )

    def check_spelling(self) -> None:
        """Check for spelling mistakes in the metadata."""
        potential_typos = []

        field_list = ['title', 'subtitle', 'alternativeTitle', 'dsDescription.dsDescriptionValue', 'notesText']
        for field in field_list:
            return_value, field_exists = self.metadata_checker.get_metadata_cm_field(field)

            if field_exists:
                typos, has_typos = self.spell_checker.check_spelling(return_value[0])
                if has_typos:
                    typo_messages = [f'{field}: `{item}`' for item in typos]
                    for message in typo_messages:
                        logger.info(f'Spelling mistake found in the {field}: {message}')

                    # Collect typos for new structure
                    for typo in typos:
                        potential_typos.append(
                            {
                                'field': field,
                                'typo': typo,
                                'context': return_value[0][:100] + '...'
                                if len(return_value[0]) > 100
                                else return_value[0],
                            }
                        )

        self.checklist_result_writer.write(
            check_name='Fields for Title, Subtitle, Alternative Title, Description, and Notes',
            check_id='potential_typos',
            description='Fields for Title, Subtitle, Alternative Title, Description, and Notes',  # noqa: E501
            unit='typo',
            results=potential_typos,
        )

    def check_depositor_record(self) -> None:
        """Check if the depositor has deposited data in the dataverse collection.

        Note: This check only works if the depositor inputs their name in a consistent way across all datasets. By default, the dataset initial creator will be listed as the depositor in the metadata, with the format (LAST NAME, FIRST NAME). But anyone with edit access to the dataset can change the depositor information, so the information might be in accurate.  # noqa: E501

        """  # noqa: E501
        depositor_history = []

        query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`depositor`].value|[0]'  # noqa: E501
        depositor: str | None = jmespath.search(query_string, self.ds_metadata)

        if isinstance(depositor, str) and depositor.strip():  # Check if depositor is a non-empty string
            response_json = self.dv_api_calls.search_depositor_record(
                depositor=depositor, collection_alias=self.collection_alias
            )
            if response_json:
                dataset_publish_history = (
                    jmespath.search(
                        'data.items[*].{name: name, url: url, name_of_dataverse: name_of_dataverse}',
                        response_json,
                    )
                    or []
                )

                # Extend the string to the depositor_history list
                depositor_history.extend(
                    f'{depositor}: {dataset.get("name")} ({dataset.get("url")}) - Dataverse Name: {dataset.get("name_of_dataverse")}'  # noqa: E501
                    for dataset in dataset_publish_history
                )

            # TODO: Add error handling for the case when the response is None or empty; or HTTP error

            self.checklist_result_writer.write(
                check_id='depositor_history',
                check_name='Depositor history',
                description='Previous datasets depositor in this Dataverse collection',
                unit='depositor record',
                results=depositor_history,
            )

        else:
            logger.info('No valid depositor provided.')

    def check_ds_tree_info(self) -> str | None:
        """Check the path of the dataset in the dataverse Repository."""
        ds_version_id = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('id')
        if ds_version_id:
            response_json = self.dv_api_calls.search_dataset_by_version_id(ds_version_id=ds_version_id)
            if response_json:
                # Get the name_of_dataverse from the response
                name_of_dataverse = response_json.get('data', {}).get('items', [{}])[0].get('name_of_dataverse', None)  # noqa: E501

                # Get the path of the dataverse from the response
                identifier_of_dataverse = (
                    response_json.get('data', {}).get('items', [{}])[0].get('identifier_of_dataverse', None)
                )  # noqa: E501
                tree_info = self.dv_tree_info.get_ds_tree_info(identifier_of_dataverse)
                path: str | None = tree_info.get('path', '')
                dataset_path = ''  # Placeholder to prevent error
                if path:
                    # Add the dataset title to the end of the path
                    ds_title = self.ds_title if self.ds_title else 'Unknown Dataset Title'
                    # Join the Path
                    dataset_path = f'{path}/{ds_title}'
                    logger.debug(f'Dataset path in the dataverse repository: {dataset_path}')  # noqa: E501

                return dataset_path
        return None

    def check_restricted_files(self) -> None:
        """Check for restricted files."""
        restricted_files = []

        for item in self.file_list_metadata:
            if item.get('restricted') is True:
                file_name = item.get('dataFile', {}).get('originalFileName') or item.get('dataFile', {}).get('filename')
                file_path = Path(item.get('directoryLabel', ''), file_name)
                logger.info(f'Restricted file found: {file_path}')
                restricted_files.append(str(file_path))

        self.checklist_result_writer.write(
            check_id='restricted_files',
            check_name='Restricted file names',
            description='files with access restrictions in the dataset',
            unit='file',
            results=restricted_files,
        )

    def run_checks(self) -> None:
        """Run all the checks."""
        logger.info('Running the checks...')
        self.file_name_checker.check_file_name_with_special_char()
        self.file_name_checker.check_file_missing_extension()
        self.file_name_checker.check_readme_file()

        self.check_file_open()
        self.file_format_checker.check_common_file_format()
        self.check_spelling()
        self.check_depositor_record()
        self.check_ds_tree_info()
        self.check_restricted_files()
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
