"""Downloads class to download a dataset's metadata and files from a Dataverse repository."""

import asyncio
from pathlib import Path
from urllib.parse import urljoin

import httpx
import jmespath
from loguru import logger

from pydatacuration.utils.directory_manager import DirectoryManager
from pydatacuration.utils.utils import orjson_export

from .httpx_client import HTTPXClient


class Downloads:
    """Class to download a dataset from a Dataverse repository."""

    def __init__(self, base_url: str, api_token: str, pid: str, main_dir: Path, ticket_number: str) -> None:
        """Initialize the class.

        Args:
            base_url (str): Base URL of the Dataverse repository
            api_token (str): API token of the Dataverse repository
            pid (str): Persistent identifier of the dataset
            main_dir (Path): The directory to save the downloaded files
            ticket_number (str): The ticket number for the dataset, used for directory organization
        """
        self.base_url = base_url
        self.pid = pid
        self.download_dir = main_dir
        self.ticket_number = ticket_number

        self.success_code = 200

        self.httpx_client = HTTPXClient(base_url, api_token)
        self.semaphore = asyncio.Semaphore(5)
        self.directory_manager = DirectoryManager(ticket_number, main_dir)
        self.logger = logger

    @staticmethod
    def _get_file_list(metadata: dict) -> list:
        file_list = []

        query_string = 'data.latestVersion.files[*].{file_id:dataFile.id, file_name:dataFile.filename, originalFileName:dataFile.originalFileName, directoryLabel: directoryLabel, md5: dataFile.md5}'  # noqa: E501
        temp_file_list = jmespath.search(query_string, metadata)
        if not temp_file_list:
            return []

        for item in temp_file_list:
            file_id = item.get('file_id')
            directory_label = item.get('directoryLabel', None) or ''
            file_name = item.get('originalFileName', None) or item.get('file_name')
            file_path = Path(directory_label, file_name)
            file_list.append((file_id, str(file_path)))
        return file_list

    @staticmethod
    def _get_dir_list(metadata: dict) -> list:
        """Get the directory list of the dataset.

        Args:
            metadata (dict): Metadata of the dataset

        Returns:
            dir_list (list): List of directories
        """
        query_string = 'data.latestVersion.files[].directoryLabel'
        dir_list = jmespath.search(query_string, metadata)
        return dir_list

    def make_dir_structure(self, metadata: dict) -> None:
        """Make the directory structure for the dataset.

        Args:
            metadata (dict): Metadata of the dataset
        """
        dir_list = self._get_dir_list(metadata)
        if dir_list:
            dir_set = set(dir_list)
            for directory in dir_set:
                Path.mkdir(Path(self.directory_manager.files_dir, directory), parents=True, exist_ok=True)

    async def _get_data_file_async(self, file_id: str, file_path: str) -> Path | None:
        """Get the data file of the dataset asynchronously."""
        api_endpoint = f'/api/access/datafile/{file_id}'
        file_path_obj = Path(self.directory_manager.files_dir, file_path)

        try:
            url = urljoin(self.base_url, api_endpoint)

            # Pass the client to async_stream_files
            content = await self.httpx_client.async_stream_files(
                url, client=self.httpx_client.async_client, params={'format': 'original'}
            )

            if content is not None:
                # Write the content to file
                await self.httpx_client.write_stream_file(file_path_obj, content)
                return file_path_obj

            return None
        except Exception as e:
            self.logger.info(f'Error downloading {file_path}: {e}')
            return None

    async def save_files_async(self, file_list: list) -> list:
        """Download the files of the dataset asynchronously.

        Args:
            file_list (list): List of files to download

        Returns:
            list: List of downloaded files
        """
        self.logger.info(f'Starting download of {len(file_list)} files...')
        tasks = [self._get_data_file_async(file_id, file_path) for file_id, file_path in file_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = [r for r in results if r is not None]
        self.logger.info(f'Finished downloading files: {successful}')
        return successful

    def _get_dv_tree(self) -> dict:
        """Get the tree structure of the dataverse repository.

        Returns:
            dict: Tree structure of the dataverse repository
        """
        url = f'{self.base_url}/api/info/metrics/tree'

        try:
            self.logger.info(f'Fetching dataverse tree structure from {url}...')
            response = self.httpx_client.sync_get(url)
            response.raise_for_status()
            if response.status_code == self.success_code and response.json():
                return response.json()
            self.logger.error(f'Error: {response.status_code} - {response.text}')
            return {}
        except httpx.HTTPStatusError as e:
            self.logger.error(f'HTTP error occurred: {e}')
            return {}
        except Exception as e:
            self.logger.error(f'An error occurred: {e}')
            return {}

    def _get_ds_metadata(self) -> dict:
        """Get metadata of a dataset.

        Returns:
            dict: Metadata of the dataset
        """
        url = f'{self.base_url}/api/datasets/:persistentId/?persistentId={self.pid}'

        try:
            self.logger.info(f'Fetching dataset metadata from {url}...')
            response = self.httpx_client.sync_get(url)
            response.raise_for_status()
            if response.status_code == self.success_code and response.json():
                return response.json()
            return {}
        except httpx.HTTPStatusError as e:
            self.logger.info(f'HTTP error occurred: {e}')
            return {}
        except Exception as e:
            self.logger.info(f'An error occurred: {e}')
            return {}

    def export_metadata(self, file_name: str, dictionary: dict) -> None:
        """Save the dataset metadata to a JSON file."""
        file_path = Path(self.directory_manager.metadata_dir, file_name)
        try:
            self.logger.info(f'Saving dataset metadata to {file_path}...')
            orjson_export(file_path, dictionary)

        except Exception as e:
            self.logger.info(f'An error occurred: {e}')

    async def downloader(self) -> None:
        """Download the dataset as a zip file asynchronously."""
        # Get the dataset metadata (sync HTTP — offloaded to thread to avoid blocking event loop)
        ds_metadata = await asyncio.to_thread(self._get_ds_metadata)
        self.export_metadata('ds_metadata.json', ds_metadata)

        # Get the tree structure of the whole dataverse repository (sync HTTP — can be slow for large repos)
        dv_tree = await asyncio.to_thread(self._get_dv_tree)
        self.export_metadata('dv_tree.json', dv_tree)

        # Download the data files using async method
        file_list = await asyncio.to_thread(self._get_file_list, ds_metadata)
        await asyncio.to_thread(self.make_dir_structure, ds_metadata)
        await self.save_files_async(file_list)
