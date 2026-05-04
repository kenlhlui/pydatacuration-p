"""Module for calling the Dataverse API."""

from loguru import logger

from pydatacuration.services.api_calls.httpx_client import HTTPXClient


class DVAPICalls:
    """Class to call the Dataverse API."""

    def __init__(self, httpx_client: HTTPXClient) -> None:
        """Initialize the DVAPICalls class."""
        self.httpx_client = httpx_client

    def get_ds_metadata(self, pid: str) -> dict:
        """Get metadata of a dataset.

        Args:
            pid (str): Persistent identifier of the dataset

        Returns:
            dict: Metadata of the dataset
        """
        endpoint = f'/api/datasets/:persistentId/?persistentId={pid}'

        logger.info(f'Fetching dataset metadata from {endpoint}...')
        response = self.httpx_client.sync_get(endpoint)
        response.raise_for_status()
        if response.status_code == self.httpx_client.httpx_success_status and response.json():
            return response.json()
        return {}

    def get_dv_tree(self) -> dict:
        """Get the tree structure of the dataverse repository.

        Returns:
            dict: Tree structure of the dataverse repository
        """
        endpoint = '/api/info/metrics/tree'

        logger.info(f'Fetching dataverse tree structure from {endpoint}...')
        response = self.httpx_client.sync_get(endpoint)
        response.raise_for_status()
        if response.status_code == self.httpx_client.httpx_success_status and response.json():
            return response.json()
        logger.error(f'Error: {response.status_code} - {response.text}')
        return {}

    def search_depositor_record(self, depositor: str, collection_alias: str | None = None) -> dict:
        """Get the depositor record from the Dataverse repository using the search API.

            - Check if the depositor has record by search API
            - See https://github.com/IQSS/dataverse/issues/2038 for fq field;
            - Note that fq supports searching the fields of the database schema
            - i.e. The fields in the Native JSON export of a dataset
            - The schema can be found inside the .tsv files for each metadata block: https://github.com/IQSS/dataverse/tree/master/scripts/api/data/metadatablocks

        Returns:
            dict: A dictionary containing the dataverse tree information.
        """
        # If collection_alias is provided, search within the specified dataverse collection
        if collection_alias:
            response = self.httpx_client.sync_get(
                f'/api/search?q=*&type=dataset&per_page=1000&subtree={collection_alias}&fq=depositor:"{depositor}"'
            )  # noqa: E501
            return response.json()
        # If no collection_alias is provided, search in all dataverses
        response = self.httpx_client.sync_get(f'/api/search?q=*&type=dataset&per_page=1000&fq=depositor:"{depositor}"')  # noqa: E501
        return response.json()

    def search_dataset_by_version_id(self, ds_version_id: str | int) -> dict:
        """Get the dataverse tree information from the Dataverse repository.

            - See https://github.com/IQSS/dataverse/issues/2038 for fq field;
            - Also check the source code the the available fq fields https://github.com/IQSS/dataverse/blob/develop/src/main/java/edu/harvard/iq/dataverse/search/SearchFields.java
            - Use 'datasetVersionId' here; in ds_metadata it is data.latestVersion.id
            - Don't mess up with data.id or data.latestVersion.datasetId which are the same and is the persistent id in the dataverse system

        Returns:
            dict: A dictionary containing the dataverse tree information.
        """  # noqa: E501
        response = self.httpx_client.sync_get(
            f'/api/search?q=*&type=dataset&per_page=1&fq=datasetVersionId:{ds_version_id}'
        )
        return response.json()

    def get_ds_access_status(self, pid: str) -> int:
        """Check if the user has access to the dataset.

        Args:
            pid (str): Persistent identifier of the dataset


        Returns:
                int: HTTP status code of the access check
        """
        endpoint = f'/api/datasets/:persistentId/?persistentId={pid}'

        response = self.httpx_client.sync_get(endpoint, raise_for_status=False)

        return response.status_code
