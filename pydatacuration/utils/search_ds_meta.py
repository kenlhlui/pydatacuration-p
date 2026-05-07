"""A collection of functions that outputs the values of the nested dataset metadata file."""

from pathlib import Path

import jmespath


def get_ds_title(ds_metadata: dict) -> str:
    """Get the dataset title from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.

    Returns:
        str: The dataset title. If no title is provided, returns 'No Title'.
    """
    return (
        jmespath.search(
            'data.latestVersion.metadataBlocks.citation.fields[?typeName == `title`].value | [0]', ds_metadata
        )
        or 'Unknown Title'
    )


def get_depositor_record(ds_metadata: dict) -> str | None:
    """Get the dataset depositor from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.

    Returns:
        str | None: The dataset depositor. If no depositor is provided, returns None.
    """
    return jmespath.search(
        'data.latestVersion.metadataBlocks.citation.fields[?typeName==`depositor`].value|[0]', ds_metadata
    )


def get_author_cm_field(ds_metadata: dict) -> list[dict]:
    """Get the dataset author Citation Metadata field from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.

    Returns:
        list[dict]: The dataset author Citation Metadata field in a nested dictionary format. If no author field is provided, returns an empty list.
    """  # noqa: E501
    query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`author`].value[].{authorName:authorName.value, authorAffiliation: authorAffiliation.value, authorIdentifierScheme: authorIdentifierScheme.value, authorIdentifier:authorIdentifier.value}'  # noqa: E501

    return jmespath.search(query_string, ds_metadata) or []


def get_metadata_cm_field(ds_metadata: dict, field: str) -> tuple[list | None, bool]:
    """Get the value of a metadata field from the metadata JSON file.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.
        field (str): Metadata field to check.
            Use '.' to specify subfields; e.g. "title", "author.authorName"

    Returns:
        result (list | None): Value of the metadata field or None if it doesn't exist
        exists (bool): True if the metadata field exists, False otherwise
    """
    if '.' in field:
        field, subfield = field.split('.')
        query_string = (
            f'data.latestVersion.metadataBlocks.citation.fields[?typeName==`{field}`].value[].[{subfield}][].value'  # noqa: E501
        )
    else:
        query_string = f'data.latestVersion.metadataBlocks.citation.fields[?typeName==`{field}`].value[]'

    result = jmespath.search(query_string, ds_metadata)
    return (result, True) if result else (None, False)


def get_related_dataset(ds_metadata: dict) -> list[str] | None:
    """Get the related dataset information from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.

    Returns:
        list[str] | None: A list of related dataset information. If no related dataset information is provided,
        returns None.
    """
    query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`relatedDatasets`].value[*][]'  # noqa: E501

    return jmespath.search(query_string, ds_metadata) or None


def get_data_sources(ds_metadata: dict) -> list[str] | None:
    """Get the data sources information from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.
    """
    query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`dataSources`].value[*][]'  # noqa: E501

    return jmespath.search(query_string, ds_metadata) or None


def get_related_publication(ds_metadata: dict) -> list[str] | None:
    """Get the related publication information from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.

    Returns:
        list[str] | None: A list of related publication information. If no related publication information is provided,
        returns None.
    """
    query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`publication`].value[*].publicationCitation[].value'  # noqa: E501

    return jmespath.search(query_string, ds_metadata) or None


def get_keywords(ds_metadata: dict) -> list[str] | None:
    """Get the dataset keywords from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.

    Returns:
        list[str] | None: A list of dataset keywords. If no keywords are provided,

    """
    query_string = (
        'data.latestVersion.metadataBlocks.citation.fields[?typeName==`keyword`].value[*].keywordValue.value[]'  # noqa: E501
    )

    return jmespath.search(query_string, ds_metadata) or None


def get_file_list(ds_metadata: dict) -> list[tuple[int, str]]:
    """Get the dataset file list from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.

    Returns:
        list[tuple[int, str]]: A list of (file_id, file_path) tuples. Empty if no files found.
    """
    file_list = []

    query_string = 'data.latestVersion.files[*].{file_id:dataFile.id, file_name:dataFile.filename, originalFileName:dataFile.originalFileName, directoryLabel: directoryLabel, md5: dataFile.md5}'  # noqa: E501
    temp_file_list = jmespath.search(query_string, ds_metadata)
    if not temp_file_list:
        return []

    for item in temp_file_list:
        file_id = item.get('file_id')
        directory_label = item.get('directoryLabel') or ''
        file_name = item.get('originalFileName') or item.get('file_name')
        file_path = Path(directory_label, file_name)
        file_list.append((file_id, str(file_path)))
    return file_list


def get_directory_set(ds_metadata: dict) -> set[str] | None:
    """Get the dataset directory set from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.

    Returns:
        set[str] | None: A set of dataset directories. If no directories are found in the metadata, returns None.
    """
    query_string = 'data.latestVersion.files[].directoryLabel'
    dir_list = jmespath.search(query_string, ds_metadata)

    return set(dir_list) or None


def get_file_list_metadata(ds_metadata: dict) -> list:
    """Get the file list metadata from the dataset metadata.

    Returns:
        list: A list of dictionaries containing the file path and the checksum.
    """
    return ds_metadata.get('data', {}).get('latestVersion', {}).get('files', [])
