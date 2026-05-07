"""Misc checker for checks that do not fit into other categories."""

# Write to db module
from loguru import logger

from pydatacuration.checker.check_result_writer import CheckResultWriter
from pydatacuration.checker.services.spell_checker import SpellCheckerCustomized
from pydatacuration.services.api_calls.call_dv import DVAPICalls
from pydatacuration.utils.search_ds_meta import get_depositor_record
from pydatacuration.utils.search_ds_meta import get_metadata_cm_field
from pydatacuration.utils.search_result_utils import get_search_result


class MiscChecker:
    """Misc checker for checks that do not fit into other categories."""

    def __init__(
        self, ds_metadata: dict, check_result_writer: CheckResultWriter, dv_api_calls_instance: DVAPICalls
    ) -> None:
        """Initialize the MiscChecker class."""
        self.ds_metadata = ds_metadata

        # The check result writer instance to write the check results to the database
        self.check_result_writer = check_result_writer

        # API calls service
        self.dv_api_calls = dv_api_calls_instance

        # Spell checker instance
        self.spell_checker = SpellCheckerCustomized()

    def check_depositor_record(self, collection_alias: str | None = None) -> None:
        """Check if the depositor has deposited data in the dataverse collection.

        Args:
            collection_alias (str | None): The alias of the dataverse collection to check. If None, it will check the depositor history across all dataverse collections.

        Note: This check only works if the depositor inputs their name in a consistent way across all datasets. By default, the dataset initial creator will be listed as the depositor in the metadata, with the format (LAST NAME, FIRST NAME). But anyone with edit access to the dataset can change the depositor information, so the information might be in accurate.  # noqa: E501

        """  # noqa: E501
        depositor_history = []

        depositor = get_depositor_record(self.ds_metadata)

        if isinstance(depositor, str) and depositor.strip():
            logger.debug(f'Checking depositor history for depositor: {depositor} in collection: {collection_alias}')
            response_json = self.dv_api_calls.search_depositor_record(
                depositor=depositor, collection_alias=collection_alias
            )
            if response_json:
                dataset_publish_history = get_search_result(response_json)

                # Extend the string to the depositor_history list
                depositor_history.extend(
                    f'{depositor}: {dataset.get("name")} ({dataset.get("url")}) - Dataverse Name: {dataset.get("name_of_dataverse")}'  # noqa: E501
                    for dataset in dataset_publish_history
                )

            self.check_result_writer.write(
                check_id='depositor_history',
                check_name='Depositor history',
                description='Previous datasets depositor in this Dataverse collection',
                unit='depositor record',
                results=depositor_history,
            )

        else:
            logger.debug('No valid depositor found from the dataset metadata. Skipping depositor history check.')

    def check_spelling(self) -> None:
        """Check for spelling mistakes in the metadata."""
        potential_typos = []

        field_list = ['title', 'subtitle', 'alternativeTitle', 'dsDescription.dsDescriptionValue', 'notesText']

        for field in field_list:
            return_value, field_exists = get_metadata_cm_field(self.ds_metadata, field)

            if field_exists:
                typos = self.spell_checker.check_spelling(return_value[0])
                if typos:
                    typo_messages = {f'{field}: `{item}`' for item in typos}
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

        self.check_result_writer.write(
            check_name='Fields for Title, Subtitle, Alternative Title, Description, and Notes',
            check_id='potential_typos',
            description='Fields for Title, Subtitle, Alternative Title, Description, and Notes',  # noqa: E501
            unit='typo',
            results=potential_typos,
        )
