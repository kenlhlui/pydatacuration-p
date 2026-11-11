"""Module for calling the Dataverse API."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import httpx2

from loguru import logger

from pydatacuration.services.api_calls.httpx_client import HTTPXClient


class DataverseClient:
    """Class to call the Dataverse API."""

    def __init__(self, httpx_client: HTTPXClient) -> None:
        """Initialize the DataverseClient class."""
        self.httpx_client = httpx_client

    def get_ds_metadata(self, pid: str, return_owners: bool = True) -> dict:
        """Get metadata of a dataset.

        Args:
            pid (str): Persistent identifier of the dataset
            return_owners (bool): Whether to return owner (i.e. dataverse collection path) information

        Returns:
            dict: Metadata of the dataset
        """
        endpoint = '/api/datasets/:persistentId/'
        params = {
            'persistentId': pid,
            'returnOwners': 'true' if return_owners else 'false',
        }

        logger.info(f'Fetching dataset metadata from {endpoint}...')
        response = self.httpx_client.sync_get(endpoint, params=params)
        response.raise_for_status()
        if response.is_success and response.json():
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
        if response.is_success and response.json():
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
        endpoint = '/api/search'
        # Escape backslashes first, then quotes, so depositor stays inside the Solr phrase
        escaped_depositor = depositor.replace('\\', '\\\\').replace('"', '\\"')
        params = {'q': '*', 'type': 'dataset', 'per_page': 1000, 'fq': f'depositor:"{escaped_depositor}"'}
        if collection_alias:
            params['subtree'] = collection_alias
        response = self.httpx_client.sync_get(endpoint, params=params)
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
            '/api/search',
            params={'q': '*', 'per_page': 1, 'type': 'dataset', 'fq': f'datasetVersionId:{ds_version_id}'},
        )
        return response.json()

    def get_ds_access_status(self, pid: str) -> httpx2.Response:
        """Check if the user has access to the dataset.

        Args:
            pid (str): Persistent identifier of the dataset

        Returns:
            httpx2.Response: The HTTP response from the access check
        """
        endpoint = '/api/datasets/:persistentId/'
        params = {'persistentId': pid}

        return self.httpx_client.sync_get(endpoint, params=params, raise_for_status=False)

    def get_ds_export_metadata(self, pid: str, exporter: str = 'OAI_ORE', version: str = ':latest') -> httpx2.Response:
        """Get the exported metadata of a dataset.

        Args:
            pid (str): Persistent identifier of the dataset
            exporter (str): The exporter to use for the metadata export
            version (str): The version of the dataset to export

        Returns:
            httpx2.Response: The HTTP response containing the exported metadata
        """
        endpoint = '/api/datasets/export'
        params = {
            'exporter': exporter,
            'persistentId': pid,
        }
        if version:
            params['version'] = version

        return self.httpx_client.sync_get(endpoint, params=params, raise_for_status=False)
