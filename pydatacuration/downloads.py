"""Downloads class to download a dataset from a Dataverse repository."""
import asyncio
import sys
from pathlib import Path
from urllib.parse import urljoin

import httpx
import jmespath
import orjson

from .custom_logging import CustomLogger
from .httpx_client import HTTPXClient
from .utils import orjson_export


class Downloads:
    """Class to download a dataset from a Dataverse repository."""
    def __init__(self, base_url: str, api_token: str, pid: str, download_dir: Path, ticket_number: str) -> None:
        """Initialize the class.

        Args:
            base_url (str): Base URL of the Dataverse repository
            api_token (str): API token of the Dataverse repository
            pid (str): Persistent identifier of the dataset
            download_dir (Path): The parent directory to save the downloaded files
        """
        self.base_url = base_url
        self.pid = pid
        self.download_dir = download_dir
        self.ticket_number = ticket_number

        self.success_code = 200

        self.httpx_client = HTTPXClient(base_url, api_token)
        self.semaphore = asyncio.Semaphore(5)
        self.logger = CustomLogger.get_logger(__name__)

    def _metadata_dir(self) -> Path:
        """Create the metadata directory.

        Returns:
            metadata_dir (Path): Path to the metadata directory
        """
        # TODO: integrate this with directory_manager module
        metadata_dir = Path(self.download_dir, 'dataset', 'metadata')
        metadata_dir.mkdir(parents=True, exist_ok=True)

        return metadata_dir

    def _files_dir(self) -> Path:
        """Create the files directory.

        Returns:
            files_dir (Path): Path to the files directory
        """
        # TODO: integrate this with directory_manager module
        files_dir = Path(self.download_dir, 'dataset', 'files')
        files_dir.mkdir(parents=True, exist_ok=True)

        return files_dir

    @staticmethod
    def _get_file_list(metadata: dict) -> list:
        file_list = []

        query_string = 'data.latestVersion.files[*].{file_id:dataFile.id, file_name:dataFile.filename, originalFileName:dataFile.originalFileName, directoryLabel: directoryLabel, md5: dataFile.md5}'  # noqa: E501
        temp_file_list = jmespath.search(query_string, metadata)

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
                Path.mkdir(Path(self._files_dir(), directory), parents=True, exist_ok=True)

    async def _get_data_file_async(self, file_id: str, file_path: str) -> Path | None:
        """Get the data file of the dataset asynchronously."""
        api_endpoint = f'/api/access/datafile/{file_id}'
        file_path_obj = Path(self._files_dir(), file_path)

        try:
            url = urljoin(self.base_url, api_endpoint)

            # Pass the client to async_stream_files
            content = await self.httpx_client.async_stream_files(
                url,
                client=self.httpx_client.async_client,
                params={'format': 'original'}
            )

            if content is not None:
                # Write the content to file
                await self.httpx_client.write_stream_file(file_path_obj, content)
                return file_path_obj

            return None
        except Exception as e:
            self.logger.print(f'Error downloading {file_path}: {e}')
            return None

    async def save_files_async(self, file_list: list) -> list:
        """Download the files of the dataset asynchronously.

        Args:
            file_list (list): List of files to download

        Returns:
            list: List of downloaded files
        """
        tasks = [self._get_data_file_async(file_id, file_path)
                for file_id, file_path in file_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = [r for r in results if r is not None]
        return successful

    def _get_dv_tree(self) -> dict:
        """Get the tree structure of the dataverse repository.

        Returns:
            dict: Tree structure of the dataverse repository
        """
        url = f'{self.base_url}/api/info/metrics/tree'

        try:
            response = self.httpx_client.sync_get(url)
            response.raise_for_status()
            if response.status_code == self.success_code and response.json():
                return response.json()
            self.logger.error(f'Error: {response.status_code} - {response.text}')
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            self.logger.error(f'HTTP error occurred: {e}')
            sys.exit(1)
        except Exception as e:
            self.logger.error(f'An error occurred: {e}')
            sys.exit(1)

    def _get_ds_metadata(self) -> dict:
        """Get metadata of a dataset.

        Returns:
            dict: Metadata of the dataset
        """
        url = f'{self.base_url}/api/datasets/:persistentId/?persistentId={self.pid}'

        try:
            response = self.httpx_client.sync_get(url)
            response.raise_for_status()
            if response.status_code == self.success_code and response.json():
                return response.json()
            sys.exit(1)
            return {}

        except httpx.HTTPStatusError as e:
            self.logger.print(f'HTTP error occurred: {e}')
            sys.exit(1)
        except Exception as e:
            self.logger.print(f'An error occurred: {e}')
            sys.exit(1)

    def save_ds_metadata(self) -> None:
        """Save the dataset metadata to a JSON file."""
        file_path = Path(self._metadata_dir(), 'ds_metadata.json')
        try:
            response_json = self._get_ds_metadata()
            # Save the metadata to dataset/metadata directory
            orjson_export(file_path, response_json)

        except Exception as e:
            self.logger.print(f'An error occurred: {e}\nProgram exiting...')
            sys.exit(1)

    async def downloader(self) -> tuple:
        """Download the dataset as a zip file asynchronously.

        Returns:
            tuple: Tuple containing the dataset metadata and the dataverse tree structure
        """
        # Get the dataset metadata
        self.logger.print('Downloading dataset metadata...')
        ds_metadata_json = self._get_ds_metadata()
        self.save_ds_metadata()
        self.logger.print('Dataset metadata downloaded')

        # Get the tree structure of the whole dataverse repository
        self.logger.print('Downloading dataverse tree structure...')
        dv_tree = self._get_dv_tree()
        self.logger.print('Dataverse tree structure downloaded')

        # Download the data files using async method
        self.logger.print('Downloading data files...')
        file_list = self._get_file_list(ds_metadata_json)
        self.make_dir_structure(ds_metadata_json)

        await self.save_files_async(file_list)
        self.logger.print('Data files downloaded')
        return ds_metadata_json, dv_tree
