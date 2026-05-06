"""MetadataChecker class for checking dataset metadata."""

from loguru import logger

from pydatacuration.checker.check_result_writer import CheckResultWriter
from pydatacuration.utils.search_ds_meta import get_author_cm_field
from pydatacuration.utils.search_ds_meta import get_data_sources
from pydatacuration.utils.search_ds_meta import get_keywords
from pydatacuration.utils.search_ds_meta import get_metadata_cm_field
from pydatacuration.utils.search_ds_meta import get_related_dataset
from pydatacuration.utils.search_ds_meta import get_related_publication


class MetadataChecker:
    """Class for checking dataset metadata."""

    def __init__(self, metadata: dict, checklist_result_writer: CheckResultWriter) -> None:
        """Initialize the MetadataChecker class.

        Args:
            metadata (dict): Metadata from the JSON file.
            checklist_result_writer (CheckResultWriter): Writer for storing check results.
        """
        self.metadata = metadata
        self.checklist_result_writer = checklist_result_writer

        self.author_info_dict = get_author_cm_field(self.metadata)

    def check_missing_required_fields(self) -> None:
        """Check for missing required metadata fields."""
        missing_required_fields = []

        required_fields = ['title', 'dsDescription', 'subject']

        for field in required_fields:
            return_value = get_metadata_cm_field(self.metadata, field)
            if return_value[1] is False:
                logger.info(f'Missing metadata found in the {field}')
                missing_required_fields.append(field)

        self.checklist_result_writer.write(
            check_id='missing_required_fields',
            check_name='Missing Required Metadata Fields',
            description='Required metadata fields that are empty or missing',
            unit='field',
            results=missing_required_fields,
        )

    def check_missing_author_affiliation(self) -> None:
        """Check for missing author affiliation."""
        authors_missing_affiliation = []

        for item in self.author_info_dict:
            if item.get('authorAffiliation') is None:
                author_name = item.get('authorName')
                logger.info(f'Missing metadata found in authorAffiliation field for author: {author_name}')
                authors_missing_affiliation.append(author_name)

        self.checklist_result_writer.write(
            check_id='authors_missing_affiliation',
            check_name='Author affiliation field',
            description='Authors missing institutional affiliation information',
            unit='author',
            results=authors_missing_affiliation,
        )

    def check_missing_author_identifier(self) -> None:
        """Check for missing author identifier."""
        authors_missing_identifier = []

        for item in self.author_info_dict:
            if item.get('authorIdentifier') is None:
                author_name = item.get('authorName')
                logger.info(f'Missing metadata found in authorIdentifier field for author: {author_name}')
                authors_missing_identifier.append(author_name)

        self.checklist_result_writer.write(
            check_id='authors_missing_identifier',
            check_name='Author Research ID field',
            description='Authors missing personal identifier (ORCID, etc.)',
            unit='author',
            results=authors_missing_identifier,
        )

    def check_missing_author_identifier_scheme(self) -> None:
        """Check for missing author identifier scheme."""
        authors_missing_scheme = []

        for item in self.author_info_dict:
            if item.get('authorIdentifierScheme') is None:
                author_name = item.get('authorName')
                logger.info(f'Missing metadata found in authorIdentifierScheme field for author: {author_name}')
                authors_missing_scheme.append(author_name)

        self.checklist_result_writer.write(
            check_id='authors_missing_scheme',
            check_name='Authors Research Identifier Scheme',
            description='Authors missing identifier scheme information',
            unit='author',
            results=authors_missing_scheme,
        )

    def check_missing_institutional_affiliation(self) -> None:
        """Check for missing institutional affiliation."""
        # Check if at least one author has affiliation with 'University of Toronto' (Non-case sensitive)
        ut_variants = ['university of toronto', 'uoft', 'u of t']
        author_affiliation_ut_num = len(
            [
                item
                for item in self.author_info_dict
                if item.get('authorAffiliation') is not None
                and any(variant in item.get('authorAffiliation', '').lower() for variant in ut_variants)
            ]
        )  # noqa: E501
        if author_affiliation_ut_num == 0:
            logger.info('None of the authors have listed affiliation with University of Toronto')

        # TODO: Write this to db and make it a check in the checklist

    def check_related_datasets(self) -> None:
        """Check if the related datasets are present."""
        related_datasets = get_related_dataset(self.metadata)
        if isinstance(related_datasets, list):
            logger.info(f'Related datasets found in the metadata: {related_datasets}')
        try:
            self.checklist_result_writer.write(
                check_name='Related Datasets',
                check_id='related_datasets_entries',
                description='Check if related datasets are present in the dataset metadata',  # noqa: E501
                unit='related dataset',
                results=related_datasets,
            )
        except Exception as e:
            logger.error(f'Failed to write related datasets to database: {e}')

    def check_data_sources(self) -> None:
        """Check if the data sources are present."""
        data_sources = get_data_sources(self.metadata)
        if isinstance(data_sources, list):
            logger.info(f'Data sources found in the metadata: {data_sources}')
        try:
            self.checklist_result_writer.write(
                check_name='Data Sources',
                check_id='data_sources_entries',
                description='Check if data sources are present in the dataset metadata',  # noqa: E501
                unit='data source',
                results=data_sources,
            )
        except Exception as e:
            logger.error(f'Failed to write data sources to database: {e}')

    def check_related_publications(self) -> None:
        """Check if the related publications are present."""
        related_publications = get_related_publication(self.metadata)
        if isinstance(related_publications, list):
            logger.info(f'Related publications found in the metadata: {related_publications}')
        try:
            self.checklist_result_writer.write(
                check_name='Related Publications',
                check_id='related_publications_entries',
                description='Check if related publications are present in the dataset',
                unit='publication',
                results=related_publications,
            )
        except Exception as e:
            logger.error(f'Failed to write related publications to database: {e}')

    def check_keywords(self) -> None:
        """Check if the keywords are present."""
        keyword_list = get_keywords(self.metadata)

        if isinstance(keyword_list, list):
            logger.info(f'Keywords found in the metadata: {keyword_list}')

        self.checklist_result_writer.write(
            check_name='Keywords',
            check_id='keywords_existence',
            description='Check if keywords are present in the dataset',
            unit='keyword',
            results=keyword_list,
        )

    def check_license(self) -> None:
        """Check if the terms of use and license are present."""
        license_name = self.metadata.get('data', {}).get('latestVersion', {}).get('license', {}).get('name', None)

        self.checklist_result_writer.write(
            check_id='license',
            check_name='License of the Dataset',
            description='License information in the dataset',
            unit='license',
            results=[
                license_name,
            ],
        )

        if license_name == 'CC0 1.0':
            logger.info('The license is CC0 1.0')

    def check_terms_of_access(self) -> None:
        """Check if the terms of access are present."""
        terms_of_access = self.metadata.get('data', {}).get('latestVersion', {}).get('termsOfAccess', None)

        self.checklist_result_writer.write(
            check_id='termsOfAccess',
            check_name='Terms of Access of the Dataset',
            description='Terms of Access information in the dataset',
            unit='term of access',
            results=[
                terms_of_access,  # FIXME: might need to update the model to accept None object, and also need to handle the rendering part.  # noqa: E501
            ],
        )

    def check_terms_of_use(self) -> None:
        """Check if the terms of use are present."""
        terms_of_use = self.metadata.get('data', {}).get('latestVersion', {}).get('termsOfUse', None)

        self.checklist_result_writer.write(
            check_id='termsOfUse',
            check_name='Terms of Use of the Dataset',
            description='Terms of Use information in the dataset',
            unit='terms of use',
            results=[
                terms_of_use,  # FIXME: might need to update the model to accept None object, and also need to handle the rendering part.  # noqa: E501
            ],
        )
