"""The main module for making API calls to the Dataverse repository."""

from pydatacuration.httpx_client import HTTPXClient


class DvCalls:
    """The main class for making API calls to the Dataverse repository."""

    def __init__(self, httpx_client: HTTPXClient) -> None:
        """Initialize the DvCalls instance.

        Args:
            httpx_client (HTTPXClient): The httpx_client instance for making API calls.

        """
        self.client = httpx_client

    def get_ds_search_record(self, ds_version_id: str | int) -> dict:
        """Get the dataset search record for a given dataset version ID.

        Args:
            ds_version_id (str | int): The dataset version ID.

        Returns:
            dict: The dataset search record or an empty dictionary if not found.
        """
        # See https://github.com/IQSS/dataverse/issues/2038 for fq field;
        # Also check the source code the the available fq fields https://github.com/IQSS/dataverse/blob/develop/src/main/java/edu/harvard/iq/dataverse/search/SearchFields.java
        # Use 'datasetVersionId' here; in ds_metadata it is data.latestVersion.id
        # Don't mess up with data.id or data.latestVersion.datasetId which are the same and is the persistent id in the dataverse system  # noqa: E501
        endpoint = f'/api/search?q=*&type=dataset&per_page=1&fq=datasetVersionId:{ds_version_id}'

        response = self.client.sync_get(endpoint)

        if response and response.json():
            return response.json()
        return {}

    def get_depositor_record(self, depositor: str, collection_alias: str | None = None) -> dict:
        """Get the dataset search record for a given depositor.

        Args:
            depositor (str): The depositor's identifier (e.g., email).
            collection_alias (str | None): The alias of the collection to search in.

        Returns:
            dict: The dataset search record for the depositor or an empty dictionary if not found.
        """
        # Check if the depositor has record by search API
        # See https://github.com/IQSS/dataverse/issues/2038 for fq field;
        # Note that fq supports searching the fields of the database schema
        # i.e. The fields in the Native JSON export of a dataset
        # The schema can be found inside the .tsv files for each metadata block: https://github.com/IQSS/dataverse/tree/master/scripts/api/data/metadatablocks
        endpoint = f'/api/search?q=*&type=dataset&per_page=1000&fq=depositor:"{depositor}"'

        if collection_alias:  # Only check the specified collection
            endpoint = f'{endpoint}&subtree={collection_alias}'

        response = self.client.sync_get(endpoint)

        if response and response.json():
            return response.json()

        return {}
