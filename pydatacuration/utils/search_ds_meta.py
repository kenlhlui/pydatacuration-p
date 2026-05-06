"""A collection of functions that outputs the values of the nested dataset metadata file."""

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


def get_depositor(ds_metadata: dict) -> str:
    """Get the dataset depositor from the dataset metadata.

    Args:
        ds_metadata (dict): The dataset metadata dictionary.

    Returns:
        str: The dataset depositor. If no depositor is provided, returns 'Unknown Depositor'.
    """
    return (
        jmespath.search(
            'data.latestVersion.metadataBlocks.citation.fields[?typeName==`depositor`].value|[0]', ds_metadata
        )
        or 'Unknown Depositor'
    )
