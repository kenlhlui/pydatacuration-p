import sys
import typing
import orjson
import jmespath
import re

class MetadataChecker:
    def __init__(self, metadata_json_path):
        self.metadata_json_path = metadata_json_path
        self.metadata = self._read_json(metadata_json_path)

    def _read_json(self, json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = orjson.loads(f.read())
            return data
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            print("Exiting...")
            sys.exit(1)

    def _read_metadata_cm_field(self, field, subfield=None):
        # TODO: fix the logic of subfield

        if subfield:
            query_string = f"data.latestVersion.metadataBlocks.citation.fields[?typeName==`{field}`].value[].[{subfield}][].value" # pylint: disable=line-too-long
            result = jmespath.search(query_string, self.metadata)
        else:
            query_string = f"data.latestVersion.metadataBlocks.citation.fields[?typeName==`{field}`]" # pylint: disable=line-too-long
            result = jmespath.search(query_string, self.metadata)
        return result

    def check_metadata_cm_field(self, field) -> typing.Tuple[str, bool]:
        """
        Check if a metadata field exists in the metadata JSON file

        Args:
            field (str): Metadata field to check.\n
            Use '.' to specify subfields; e.g. "title", "author.authorName"
        
        Returns:
            result (str): Value of the metadata field\n
            exists (bool): True if the metadata field exists, False otherwise
        """
        # Check the input of field has . in it and split it into field and subfield
        if "." in field:
            field, subfield = field.split(".")
        else:
            subfield = None

        result = self._read_metadata_cm_field(field, subfield)
        if result:
            return result, True

        return None, False
