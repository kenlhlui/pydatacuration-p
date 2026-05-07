"""Downloads class to download a dataset's metadata and files from a Dataverse repository."""

import asyncio
from pathlib import Path
from urllib.parse import urljoin

from loguru import logger

from pydatacuration.backend.models.setup_form import SetupForm
from pydatacuration.services.api_calls.call_dv import DVAPICalls
from pydatacuration.services.api_calls.httpx_client import HTTPXClient
from pydatacuration.utils.directory_manager import DirectoryManager
from pydatacuration.utils.search_ds_meta import get_directory_set
from pydatacuration.utils.search_ds_meta import get_file_list
from pydatacuration.utils.utils import orjson_export


class Downloads:
    """Class to download a dataset from a Dataverse repository."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        pid: str,
        main_dir: Path,
        project_number: str,
    ) -> None:
        """Initialize the class.

        Args:
            base_url (str): Base URL of the Dataverse repository
            api_token (str): API token of the Dataverse repository
            pid (str): Persistent identifier of the dataset
            main_dir (Path): The directory to save the downloaded files
            project_number (str): The project number for the dataset, used for directory organization
        """
        self.base_url = base_url
        self.api_token = api_token
        self.pid = pid
        self.download_dir = main_dir
        self.project_number = project_number

        self.success_code = 200

        self.httpx_client = HTTPXClient(self.base_url, self.api_token)
        self.dv_api_calls = DVAPICalls(self.httpx_client)
        self.semaphore = asyncio.Semaphore(5)
        self.directory_manager = DirectoryManager(self.project_number, self.download_dir)

    @classmethod
    def from_setup_form(
        cls,
        setup_form: SetupForm,
        main_dir: Path,
    ) -> 'Downloads':
        """Create a Downloads instance from a SetupForm instance.

        Args:
            setup_form (SetupForm): An instance of the setup form containing base_url and api_token
            main_dir (Path): The directory to save the downloaded files
        """
        return cls(
            base_url=str(setup_form.base_url) if setup_form.base_url else '',
            api_token=str(setup_form.api_token) if setup_form.api_token else '',
            pid=setup_form.pid,
            main_dir=main_dir,
            project_number=setup_form.project_number,
        )

    def make_dir_structure(self, metadata: dict) -> None:
        """Make the directory structure for the dataset.

        Args:
            metadata (dict): Metadata of the dataset

        """
        dir_set = get_directory_set(metadata)

        if not dir_set:
            return

        base_path = Path(self.directory_manager.files_dir)

        for directory in dir_set:
            (base_path / directory).mkdir(parents=True, exist_ok=True)

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
            logger.info(f'Error downloading {file_path}: {e}')
            return None

    async def save_files_async(self, file_list: list) -> list:
        """Download the files of the dataset asynchronously.

        Args:
            file_list (list): List of files to download

        Returns:
            list[tuple[str, str]]: List of downloaded files
        """
        logger.info(f'Starting download of {len(file_list)} files...')
        tasks = [self._get_data_file_async(file_id, file_path) for file_id, file_path in file_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = [r for r in results if r is not None]
        logger.info(f'Finished downloading files: {successful}')
        return successful

    def export_metadata(self, file_name: str, dictionary: dict) -> None:
        """Save the dataset metadata to a JSON file."""
        file_path = Path(self.directory_manager.metadata_dir, file_name)
        try:
            logger.info(f'Saving dataset metadata to {file_path}...')
            orjson_export(file_path, dictionary)

        except Exception as e:
            logger.error(f'An error occurred: {e}')

    async def downloader(self) -> dict:
        """Download the dataset as a zip file asynchronously."""
        # Get the dataset metadata (sync HTTP — offloaded to thread to avoid blocking event loop)
        ds_metadata = await asyncio.to_thread(self.dv_api_calls.get_ds_metadata, self.pid)
        self.export_metadata('ds_metadata.json', ds_metadata)

        # Get the tree structure of the whole dataverse repository (sync HTTP — can be slow for large repos)
        dv_tree = await asyncio.to_thread(self.dv_api_calls.get_dv_tree)
        self.export_metadata('dv_tree.json', dv_tree)

        # Download the data files using async method
        file_list = get_file_list(ds_metadata)
        await asyncio.to_thread(self.make_dir_structure, ds_metadata)
        await self.save_files_async(file_list)

        return ds_metadata
