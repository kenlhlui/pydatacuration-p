"""The checker module provides functions to check the validity of data files and metadata."""

from pathlib import Path

import jmespath
import yaml
from loguru import logger
from sqlmodel import SQLModel

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.checker.file_name_checker import FileNameFormatChecker
from pydatacuration.checker.files_open_checker import FilesOpener
from pydatacuration.checker.metadata_checker import MetadataChecker
from pydatacuration.checker.spell_checker import SpellCheckerCustomized
from pydatacuration.checklist.utils import get_checklist_file_path
from pydatacuration.checksum import Checksum
from pydatacuration.db.base import DatabaseBackend
from pydatacuration.httpx_client import HTTPXClient
from pydatacuration.utils.unzip import Unzipper
from pydatacuration.utils.utils import check_readme_file_existence
from pydatacuration.utils.utils import compare_files_and_metadata
from pydatacuration.utils.utils import parse_dataset_url
from pydatacuration.utils.utils import parse_file_list_metadata


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
        self.api_token = setup_form_instance.api_token or ''
        self.ds_metadata = ds_metadata
        self.dv_tree = dv_tree
        self.workdir = workdir
        self.check_zip = setup_form_instance.check_zip
        self.collection_alias = setup_form_instance.collection_alias
        self.db_instance = db_instance
        self.sqlmodels = self.db_instance.models
        self.curator_name = setup_form_instance.curator_name
        self.curator_email = setup_form_instance.curator_email
        self.checklist_type = setup_form_instance.checklist

        self.checksums = Checksum()
        self.files_opener = FilesOpener
        self.metadata_checker = MetadataChecker(self.workdir.joinpath('dataset', 'metadata', 'ds_metadata.json'))
        self.spell_checker = SpellCheckerCustomized()
        self.httpx_client = HTTPXClient(self.base_url, self.api_token)
        self.file_list_metadata = self._gen_file_list_metadata()
        self.common_file_format_tuple = self._read_common_file_format()

        self.ds_title = jmespath.search(
            'data.latestVersion.metadataBlocks.citation.fields[?typeName == `title`].value | [0]', self.ds_metadata
        )  # noqa
        self.dataset_id = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('id')

    def _get_ds_tree_info(self, identifier_of_dataverse: str) -> dict:
        """Get the dataset tree information in the Dataverse repository.

        Args:
            identifier_of_dataverse(str): The identifier of the dataverse parent dataverse.

        Returns:
            dict: A dictionary containing the path to the target node, empty if none.
        """

        def _process(data: dict, id_list: list, alias_list: list, name_list: list) -> dict:
            # Append the current node's alias and name to the respective lists
            # Create new lists with current node's information
            current_id_list = id_list + [data.get('id')]
            current_alias_list = alias_list + [data.get('alias')]
            current_name_list = name_list + [data.get('name')]

            # Check if the current node is the target
            if data.get('alias') == identifier_of_dataverse:
                result = {
                    'id': current_id_list,
                    'alias': current_alias_list,
                    'depth': data.get('depth'),
                    'name': current_name_list,
                }
                # Combine the paths with '/' separator
                result['path'] = '/'.join(current_name_list)
                # Turn the id, alias and name from list to tuple
                result['id'] = tuple(result['id'])
                result['alias'] = tuple(result['alias'])
                result['name'] = tuple(result['name'])
                return result

            # Recursively search through any children
            for child in data.get('children', []):
                result = _process(child, current_id_list, current_alias_list, current_name_list)
                if result:  # This is correct - if a non-empty result is returned from any child, pass it up
                    return result  # Return the result immediately when found

            # If we get here, no match was found in this branch
            return {}

        # Read the root node from the JSON once
        root = self.dv_tree.get('data', {}) if self.dv_tree.get('status') == 'OK' else {}
        result = _process(root, [], [], [])
        return result

    def _read_common_file_format(self) -> tuple | None:
        """Reads the common_file_format.yaml file and returns it as a dictionary.

        Returns:
            dict: The common file format as a dictionary.
        """
        try:
            # Check if the file exists
            if RES_DIR.joinpath('common_file_formats.yaml').exists():
                # Open the file and read its content
                with RES_DIR.joinpath('common_file_formats.yaml').open(encoding='utf-8') as file:
                    common_file_format_dict = yaml.safe_load(file)

                    file_formats = set()
                    for _category, extensions in common_file_format_dict['file_formats'].items():
                        file_formats.update(extensions)  # Use set to avoid duplicates

                    return tuple(file_formats)  # Convert set to tuple for immutability

        except FileNotFoundError:
            # Handle the case where the file is not found
            logger.error('common_file_formats.yaml file not found in the res directory.')
            return None

    def _gen_file_list_metadata(self) -> list:
        """Generate the file list metadata.

        Returns:
            list: The file list metadata.
        """
        # Check the checksum of the downloaded files
        dl_file_checksum_nested_list = self.checksums.gen_ds_files_checksum(self.workdir)

        file_list_metadata = self.ds_metadata['data']['latestVersion']['files']

        file_list_metadata_nested_list = parse_file_list_metadata(file_list_metadata)

        compare_files_and_metadata(dl_file_checksum_nested_list, file_list_metadata_nested_list, self.workdir)

        return file_list_metadata

    def check_file_name_format(self) -> None:
        """Check the file name format."""
        file_name_format_checker = FileNameFormatChecker()
        special_char_files = []
        missing_ext_files = []
        readme_files = []

        for file in self.file_list_metadata:
            file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
            file_rel_path = Path(file.get('directoryLabel', ''), file_name)

            if file_name_format_checker.check_special_char(file_name)[1] is True:
                logger.info(f'Special characters found in the filename: {file_rel_path}')
                special_char_files.append(str(file_rel_path))

            if file_name_format_checker.check_file_ext(file_name)[1] is True:
                logger.info(f'File extension does not found: {file_rel_path}')
                missing_ext_files.append(str(file_rel_path))

            if check_readme_file_existence(file_name)[1] is True:
                logger.info(f'README file found: {file_rel_path}')
                readme_files.append(str(file_rel_path))

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='filename_special_chars',
                    check_name='Files with Special Characters',
                    description='Files containing special characters in filename',
                    unit='file',
                    results=special_char_files,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write special character files to database: {e}')

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='missing_file_extensions',
                    check_name='Files Missing Extensions',
                    description='Files without proper file extensions',
                    unit='file',
                    results=missing_ext_files,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write missing_file_extensions to database: {e}')

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='readme_files',
                    check_name='README Files Found',
                    description='README files detected in the dataset',
                    unit='file',
                    results=readme_files,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write readme_files to database: {e}')

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

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='file_accessibility',
                    check_name='Inaccessible Files',
                    description='Files that cannot be opened or read by the validation tool',
                    unit='file',
                    results=inaccessible_files,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write file_accessibility to database: {e}')

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='unsupported_files',
                    check_name='Files with Unsupported Formats',
                    description='Files in formats not supported by the validation tool',
                    unit='file',
                    results=unsupported_files,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write unsupported_files to database: {e}')

    def check_common_file_format(self) -> None:
        """Check if the file format is in the common file format."""
        uncommon_format_files = []

        if self.common_file_format_tuple:
            for file in self.file_list_metadata:
                file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
                file_rel_path = Path(file.get('directoryLabel', ''), file_name)
                file_abs_path = Path(self.workdir, 'dataset', 'files', file_rel_path)
                file_ext = file_rel_path.suffix
                if file_ext.startswith('.') and file_ext not in self.common_file_format_tuple:
                    logger.info(f'File is not a common file format: {file_abs_path}')
                    uncommon_format_files.append(str(file_rel_path))
        else:
            logger.error('No common file format found in the res directory. Skipping this check.')

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='uncommon_file_formats',
                    check_name='Files with Uncommon Formats',
                    description='Files using uncommon or proprietary file formats',
                    unit='file',
                    results=uncommon_format_files,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write uncommon_file_formats to database: {e}')

    def check_missing_metadata(self) -> None:
        """Check for missing metadata."""
        missing_required_fields = []
        authors_missing_affiliation = []
        authors_missing_identifier = []
        authors_missing_scheme = []

        field_list = ['title', 'dsDescription', 'subject']
        for field in field_list:
            return_value = self.metadata_checker.check_metadata_cm_field(field)
            if return_value[1] is False:
                logger.info(f'Missing metadata found in the {field}')
                missing_required_fields.append(field)

        # Check any associated fields for an author (affiliation, identifier & scheme) are missing
        field_list_author = ['authorAffiliation', 'authorIdentifierScheme', 'authorIdentifier']
        author_info_dict = self.metadata_checker.check_author_cm_field()
        for item in author_info_dict:
            author_name = item.get('authorName')
            for field in field_list_author:
                if item.get(field) is None:
                    logger.info(f'Missing metadata found in {field} field for author: {author_name}')

                    # Collect authors missing specific fields
                    if field == 'authorAffiliation':
                        authors_missing_affiliation.append(author_name)
                    elif field == 'authorIdentifier':
                        authors_missing_identifier.append(author_name)
                    elif field == 'authorIdentifierScheme':
                        authors_missing_scheme.append(author_name)

        # Check if at least one author has authorAffiliation
        author_affiliation_num = len([item for item in author_info_dict if item.get('authorAffiliation') is not None])
        if author_affiliation_num == 0:
            logger.info('None of the authors have an institutional affiliation listed')

        # Check if at least one author has affiliation with 'University of Toronto' (Non-case sensitive)
        ut_variants = ['university of toronto', 'uoft', 'u of t']
        author_affiliation_ut_num = len(
            [
                item
                for item in author_info_dict
                if item.get('authorAffiliation') is not None
                and any(variant in item.get('authorAffiliation', '').lower() for variant in ut_variants)
            ]
        )  # noqa: E501
        if author_affiliation_ut_num == 0:
            logger.info('None of the authors have listed affiliation with University of Toronto')

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='missing_required_fields',
                    check_name='Missing Required Metadata Fields',
                    description='Required metadata fields that are empty or missing',
                    unit='field',
                    results=missing_required_fields,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write missing_required_fields to database: {e}')

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='authors_missing_affiliation',
                    check_name='Authors Without Affiliation',
                    description='Authors missing institutional affiliation information',
                    unit='author',
                    results=authors_missing_affiliation,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write authors_missing_affiliation to database: {e}')

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='authors_missing_identifier',
                    check_name='Authors Without Identifier',
                    description='Authors missing personal identifier (ORCID, etc.)',
                    unit='author',
                    results=authors_missing_identifier,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write authors_missing_identifier to database: {e}')

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='authors_missing_scheme',
                    check_name='Authors Without Identifier Scheme',
                    description='Authors missing identifier scheme information',
                    unit='author',
                    results=authors_missing_scheme,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write authors_missing_scheme to database: {e}')

    def check_spelling(self) -> None:
        """Check for spelling mistakes in the metadata."""
        potential_typos = []

        field_list = ['title', 'subtitle', 'alternativeTitle', 'dsDescription.dsDescriptionValue', 'notesText']
        for field in field_list:
            return_value, field_exists = self.metadata_checker.check_metadata_cm_field(field)

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

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_name='Potential Spelling Errors',
                    check_id='potential_typos',
                    description='Check for potential spelling errors in metadata fields',
                    unit='typo',
                    results=potential_typos,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write potential typos to database: {e}')

    def check_depositor_record(self) -> None:
        """Check if the depositor has deposited data in the dataverse collection.

        Note: This check only works if the depositor inputs their name in a consistent way across all datasets. By default, the dataset initial creator will be listed as the depositor in the metadata, with the format (LAST NAME, FIRST NAME). But anyone with edit access to the dataset can change the depositor information, so the information might be in accurate.  # noqa: E501

        """  # noqa: E501
        depositor_history = []

        query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`depositor`].value|[0]'  # noqa: E501
        depositor: str | None = jmespath.search(query_string, self.ds_metadata)

        if isinstance(depositor, str) and depositor.strip():  # Check if depositor is a non-empty string
            # Check if the depositor has record by search API
            # See https://github.com/IQSS/dataverse/issues/2038 for fq field;
            # Note that fq supports searching the fields of the database schema
            # i.e. The fields in the Native JSON export of a dataset
            # The schema can be found inside the .tsv files for each metadata block: https://github.com/IQSS/dataverse/tree/master/scripts/api/data/metadatablocks
            if self.collection_alias:  # Only check the specified collection
                response = self.httpx_client.sync_get(
                    f'/api/search?q=*&type=dataset&per_page=1000&subtree={self.collection_alias}&fq=depositor:"{depositor}"'
                )  # noqa: E501
            else:
                # If no collection_alias is provided, search in all dataverses
                response = self.httpx_client.sync_get(
                    f'/api/search?q=*&type=dataset&per_page=1000&fq=depositor:"{depositor}"'
                )  # noqa: E501
            if response and response.json():
                dataset_publish_history = (
                    jmespath.search(
                        'data.items[*].{name: name, url: url, name_of_dataverse: name_of_dataverse}',
                        response.json(),
                    )
                    or []
                )

                # Extend the string to the depositor_history list
                depositor_history.extend(
                    f'{depositor}: {dataset.get("name")} ({dataset.get("url")}) - Dataverse Name: {dataset.get("name_of_dataverse")}'
                    for dataset in dataset_publish_history
                )

            # TODO: Add error handling for the case when the response is None or empty; or HTTP error

            try:
                check_result_list_schema = self.sqlmodels.check_results()
                self.db_instance.merge_records_to_table(
                    check_result_list_schema(
                        check_id='depositor_history',
                        check_name='Depositor History',
                        description='Previous datasets depositor in this Dataverse collection',
                        unit='depositor record',
                        results=depositor_history,
                    )
                )
            except Exception as e:
                logger.error(f'Failed to write depositor history to database: {e}')
        else:
            logger.info('No valid depositor provided.')

    def check_ds_tree_info(self) -> str | None:
        """Check the path of the dataset in the dataverse Repository."""
        ds_version_id = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('id')
        if ds_version_id:
            # See https://github.com/IQSS/dataverse/issues/2038 for fq field;
            # Also check the source code the the available fq fields https://github.com/IQSS/dataverse/blob/develop/src/main/java/edu/harvard/iq/dataverse/search/SearchFields.java
            # Use 'datasetVersionId' here; in ds_metadata it is data.latestVersion.id
            # Don't mess up with data.id or data.latestVersion.datasetId which are the same and is the persistent id in the dataverse system  # noqa: E501
            response = self.httpx_client.sync_get(
                f'/api/search?q=*&type=dataset&per_page=1&fq=datasetVersionId:{ds_version_id}'
            )  # noqa: E501
            if response and response.json():
                # Get the name_of_dataverse from the response
                name_of_dataverse = response.json().get('data', {}).get('items', [{}])[0].get('name_of_dataverse', None)  # noqa: E501

                # Get the path of the dataverse from the response
                identifier_of_dataverse = (
                    response.json().get('data', {}).get('items', [{}])[0].get('identifier_of_dataverse', None)
                )  # noqa: E501
                tree_info = self._get_ds_tree_info(identifier_of_dataverse)
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
        # TODO: Add error handling for the case when the response is None or empty; or HTTP error

    def check_restricted_files(self) -> None:
        """Check for restricted files."""
        restricted_files = []

        for item in self.file_list_metadata:
            if item.get('restricted') is True:
                file_name = item.get('dataFile', {}).get('originalFileName') or item.get('dataFile', {}).get('filename')
                file_path = Path(item.get('directoryLabel', ''), file_name)
                logger.info(f'Restricted file found: {file_path}')
                restricted_files.append(str(file_path))

        try:
            check_result_list_schema: type[SQLModel] = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='restricted_files',
                    check_name='Restricted Access Files',
                    description='Files with access restrictions in the dataset',
                    unit='file',
                    results=restricted_files,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write restricted_files to database: {e}')

    def check_terms_of_use(self) -> None:
        """Check if the terms of use are present."""
        terms_of_use = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('termsOfUse', None)

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='termsOfUse',
                    check_name='Terms of Use of the Dataset',
                    description='Terms of Use information in the dataset',
                    unit='terms of use',
                    results=[
                        terms_of_use,
                    ],
                )
            )
        except Exception as e:
            logger.error(f'Failed to write termsOfUse to database: {e}')

    def check_terms_of_access(self) -> None:
        """Check if the terms of access are present."""
        terms_of_access = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('termsOfAccess', None)

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='termsOfAccess',
                    check_name='Terms of Access of the Dataset',
                    description='Terms of Access information in the dataset',
                    unit='term of access',
                    results=[
                        terms_of_access,
                    ],
                )
            )
        except Exception as e:
            logger.error(f'Failed to write termsOfAccess to database: {e}')

    def check_license(self) -> None:
        """Check if the terms of use and license are present."""
        license_name = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('license', {}).get('name', None)

        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_id='license',
                    check_name='License of the Dataset',
                    description='License information in the dataset',
                    unit='license',
                    results=[
                        license_name,
                    ],
                )
            )
        except Exception as e:
            logger.error(f'Failed to write license to database: {e}')

        if license_name == 'CC0 1.0':
            logger.info('The license is CC0 1.0')

    def check_keywords(self) -> None:
        """Check if the keywords are present."""
        query_string = (
            'data.latestVersion.metadataBlocks.citation.fields[?typeName==`keyword`].value[*].keywordValue.value[]'  # noqa: E501
        )
        keyword_list = jmespath.search(query_string, self.ds_metadata)
        if isinstance(keyword_list, list):
            logger.info(f'Keywords found in the metadata: {keyword_list}')

        # DEBUG: Test for writing to database using CheckResultList
        # FIXME: fix the update logic; it won't work if there's table
        try:
            check_result_list_schema = self.sqlmodels.check_results()
            self.db_instance.merge_records_to_table(
                check_result_list_schema(
                    check_name='Keywords Existence',
                    check_id='keywords_existence',
                    description='Check if keywords are present in the dataset',
                    unit='keyword',
                    results=keyword_list,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write keywords to database: {e}')

    # The below writes the to the database database
    def write_project_metadata_db(self) -> None:
        """Write the project metadata to the database."""
        project_metadata_schema = self.sqlmodels.project_metadata_record()

        # Check if record already exists
        try:
            project_number = self.db_instance.schema_name
            curator_name: str | None = self.curator_name
            curator_email: str | None = self.curator_email
            dataset_title = self.ds_title if self.ds_title else 'No Title'
            dataset_pid = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('datasetPersistentId', 'No ID')
            datasetid = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('datasetId', 'No ID')
            dataset_url = parse_dataset_url(self.base_url, dataset_pid)
            dataset_path = self.check_ds_tree_info()

            self.db_instance.merge_records_to_table(
                project_metadata_schema(
                    curator_name=curator_name,
                    curator_email=curator_email,
                    project_number=project_number,
                    dataset_title=dataset_title,
                    dataset_pid=dataset_pid,
                    dataset_id=self.dataset_id,
                    datasetid=datasetid,
                    dataset_url=dataset_url,
                    dataset_path=dataset_path,
                    checklist_type=self.checklist_type,
                )
            )
        except Exception as e:
            logger.error(f'Failed to write to database: {e}')

    # Note: maybe to migrate this to main.py
    def write_checklist_db(self, checklist_type: str = 'default') -> None:
        """Write the checklist items to database.

        Supports flexible checklist file naming:
        - Checklist with types: checklist-{type}.yaml or checklist-{type}.yml
        - Default: checklist.yaml or checklist.yml (when checklist_type='default')

        Args:
            checklist_type (str): Type of checklist to use. Default is 'default'
        """
        try:
            logger.debug(f'Writing the {checklist_type} checklist to database...')
            checklist_schema = self.sqlmodels.checklist()

            # Use the flexible file path function to find the checklist file
            checklist_file: Path | None = get_checklist_file_path(checklist_type, RES_DIR)

            if not checklist_file or not checklist_file.exists():
                error_msg = f'Checklist file not found for type: {checklist_type}'
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

            logger.debug(f'Using checklist file: {checklist_file}')

            with Path.open(checklist_file, 'r') as f:
                checklist_data = yaml.safe_load(f)

            # Write each checklist item to database
            for item in checklist_data.get('checklist', []):
                logger.debug(f'Writing checklist item to database: {item}')
                self.db_instance.merge_records_to_table(
                    checklist_schema(
                        id=item.get('id'),
                        action=item.get('action'),
                        instructions=item.get('instructions'),
                        priority=item.get('priority'),
                        section=item.get('section'),
                        automated_check_ids=item.get('automated_check_ids'),
                        tool_explanation=item.get('tool_explanation'),
                        curator_check_item=item.get('curator_check_item'),
                        check_type=item.get('check_type'),
                    )
                )
        except Exception as e:
            logger.error(f'Failed to write checklist to database: {e}')

    def run_checks(self) -> None:
        """Run all the checks."""
        logger.info('Running the checks...')
        self.check_file_name_format()
        self.check_file_open()
        self.check_common_file_format()
        self.check_missing_metadata()
        self.check_spelling()
        self.check_depositor_record()
        self.check_ds_tree_info()
        self.check_restricted_files()
        self.check_terms_of_use()
        self.check_terms_of_access()
        self.check_keywords()
        self.check_license()
        self.write_project_metadata_db()
        # Write the checklist to database using the configured checklist type
        self.write_checklist_db(self.checklist_type)
