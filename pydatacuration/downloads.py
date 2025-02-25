# pylint: disable=C0301
import asyncio
import os
import sys

import httpx
import jmespath
import orjson


class Downloads:
    """Class to download a dataset from a Dataverse repository.

    Args:
        base_url (str): Base URL of the Dataverse repository
        api_token (str): API token of the Dataverse repository
        pid (str): Persistent identifier of the dataset
        download_dir (str): The master directory to save the downloaded files
    """
    def __init__(self, base_url, api_token, pid, download_dir):
        self.base_url = base_url
        self.api_token = api_token
        self.pid = pid
        self.download_dir = download_dir
        self.client = httpx.Client(headers={'X-Dataverse-key': self.api_token}, timeout=None, follow_redirects=True)
        self.async_client = httpx.AsyncClient(headers={'X-Dataverse-key': self.api_token}, timeout=None, follow_redirects=True)
        self.semaphore = asyncio.Semaphore(5)

    def _metadata_dir(self) -> str:
        """Create the metadata directory."""
        metadata_dir = os.path.join(self.download_dir, 'dataset', 'metadata')
        if not os.path.exists(metadata_dir):
            os.makedirs(metadata_dir, exist_ok=True)

        return metadata_dir

    def _files_dir(self) -> str:
        """Create the files directory
        """
        files_dir = os.path.join(self.download_dir, 'dataset', 'files')
        if not os.path.exists(files_dir):
            os.makedirs(files_dir, exist_ok=True)

        return files_dir

    def _get_data_file(self, file_id, file_path):
        """Get the data file of the dataset.

        Returns:
            str: Path to the downloaded data file
        """
        url = f'{self.base_url}/api/access/datafile/{file_id}'
        file_path = f'{self.download_dir}/temp_data/{file_path}'
        try:
            with self.client.stream("GET", url, params={'format': 'original'}) as response:
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_bytes():
                            f.write(chunk)
                return file_path
        except httpx.HTTPStatusError as e:
            print(f'HTTP error occurred: {e}')
            sys.exit(1)

    def _get_file_list(self, metadata):
        file_list =[]

        query_string = 'data.latestVersion.files[*].{file_id:dataFile.id, file_name:dataFile.filename, originalFileName:dataFile.originalFileName, directoryLabel: directoryLabel, md5: dataFile.md5}'
        temp_file_list = jmespath.search(query_string, metadata)
        
        for item in temp_file_list:
            file_id = item.get('file_id')
            directory_label = item.get('directoryLabel', None) or ''
            file_name = item.get('originalFileName', None) or item.get('file_name')
            file_path = os.path.join(directory_label, file_name)
            file_list.append((file_id, file_path))
        return file_list

    def _get_dir_list(self, metadata):
        query_string = 'data.latestVersion.files[].directoryLabel'
        return jmespath.search(query_string, metadata)

    def make_dir_structure(self, metadata):
        # Make the directory structure
        dir_list = self._get_dir_list(metadata)
        if dir_list:
            dir_set = set(dir_list)
            for directory in dir_set:
                directory = os.path.join(self._files_dir(), directory)
                os.makedirs(directory, exist_ok=True)

    async def _get_data_file_async(self, file_id, file_path):
        """Get the data file of the dataset asynchronously

        Args:
            file_id (str): The file ID
            file_path (str): The relative path of the file
        
        Returns:
            str: Path to the downloaded data file
        """
        url = f'{self.base_url}/api/access/datafile/{file_id}'
        file_path = os.path.join(self._files_dir(), file_path)

        try:
            async with self.semaphore:
                async with self.async_client.stream("GET", url, params={'format': 'original'}) as response:
                    if response.status_code == 200:
                        with open(file_path, mode='wb') as f:
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                f.write(chunk)
                    return file_path
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")

    async def save_files_async(self, file_list):
        """Download the files of the dataset asynchronously

        Args:
            file_list (list): List of tuples containing the file ID and the relative path of the file
        
        Returns:
            list: List of successful downloads
        """
        async with self.async_client:
            tasks = [self._get_data_file_async(file_id, file_path) for file_id, file_path in file_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = [r for r in results if r is not None]
            return successful

    def _get_ds_metadata(self):
        """Get metadata of a dataset
        
        Returns:
            dict: Metadata of the dataset
        """
        url = f"{self.base_url}/api/datasets/:persistentId/?persistentId={self.pid}"

        try:
            response = self.client.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

    def save_ds_metadata(self):
        """Save the dataset metadata to a JSON file
        """
        file_path = os.path.join(self._metadata_dir(), 'ds_metadata.json')
        try:
            response = self._get_ds_metadata()
            if response.status_code == 200:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(orjson.dumps(response.json(), option=orjson.OPT_INDENT_2).decode())
        except Exception as e:
            print(f" An error occurred: {e}\n Program exiting...")
            sys.exit(1)

    def get_ds_zip(self):
        """Get a dataset as a zip file

        Returns:
            str: Path to the downloaded zip file
        """
        file_path = os.path.join(self._files_dir(), 'ds.zip')
        url = self.base_url + 'api/access/dataset/:persistentId/?persistentId=' + self.pid

        try:
            with self.client.stream("GET", url) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            return file_path

        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            sys.exit(1)

        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

    async def get_ds_zip_async(self):
        """Get a dataset as a zip file asynchronously.

        Returns:
            str: Path to the downloaded zip file
        """
        file_path = os.path.join(self._files_dir(), 'ds.zip')
        url = self.base_url + 'api/access/dataset/:persistentId/?persistentId=' + self.pid + '&format=original'

        try:
            async with self.async_client.stream('GET', url) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
            return file_path

        except httpx.HTTPStatusError as e:
            print(f'HTTP error occurred: {e}')
            sys.exit(1)

        except Exception as e:
            print(f'An error occurred: {e}')
            sys.exit(1)

    async def downloader(self) -> dict:
        """Download the dataset as a zip file asynchronously.

        Returns:
            dict: Metadata of the dataset
        """
        # Initiating the downloads
        print('\nDownloading dataset metadata...')
        ds_metadata = self._get_ds_metadata().json()
        self.save_ds_metadata()
        print('\nDataset metadata downloaded')

        # Download the data files using async method
        print('\nDownloading data files...')
        file_list = self._get_file_list(ds_metadata)
        self.make_dir_structure(ds_metadata)

        await self.save_files_async(file_list)
        print('Data files downloaded\n')
        return ds_metadata
