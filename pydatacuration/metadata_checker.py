"""MetadataChecker class for checking metadata fields in a JSON file."""

import sys
from pathlib import Path

import jmespath
import orjson

from .custom_logging import CustomLogger
from .directory_manager import DirectoryManager


class MetadataChecker:
    def __init__(self, metadata: dict) -> None:
        """Initialize the MetadataChecker class.

        Args:
            metadata_json_path (Path | str): Path to the metadata JSON file.
                metadata (dict): Metadata from the JSON file.
        """
        self.logger = CustomLogger.get_logger(__name__)
        self.metadata = metadata

    def _read_metadata_cm_field(self, field: str, subfield=None):
        # TODO: fix the logic of subfield

        if subfield:
            query_string = (
                f'data.latestVersion.metadataBlocks.citation.fields[?typeName==`{field}`].value[].[{subfield}][].value'  # noqa: E501
            )
            result = jmespath.search(query_string, self.metadata)
        else:
            query_string = f'data.latestVersion.metadataBlocks.citation.fields[?typeName==`{field}`].value[]'
            result = jmespath.search(query_string, self.metadata)
        return result

    def check_metadata_cm_field(self, field: str) -> tuple[str, bool]:
        r"""Check if a metadata field exists in the metadata JSON file.

        Args:
            field (str): Metadata field to check.\n
            Use '.' to specify subfields; e.g. "title", "author.authorName"

        Returns:
            result (str): Value of the metadata field\n
            exists (bool): True if the metadata field exists, False otherwise
        """
        # Check the input of field has . in it and split it into field and subfield
        if '.' in field:
            field, subfield = field.split('.')
        else:
            subfield = None

        result = self._read_metadata_cm_field(field, subfield)
        if result:
            return result, True

        return None, False

    def check_author_cm_field(self) -> list[dict]:
        r"""Check if the author metadata fields exist in the metadata JSON file.

        Returns:
            result (list[dict]): List of dictionaries containing author metadata fields
        """
        query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`author`].value[].{authorName:authorName.value, authorAffiliation: authorAffiliation.value, authorIdentifierScheme: authorIdentifierScheme.value, authorIdentifier:authorIdentifier.value}'
        result = jmespath.search(query_string, self.metadata)

        return result
