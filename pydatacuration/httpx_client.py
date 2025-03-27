"""HTTPX client for handing HTTP requests and responses."""
import asyncio
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

from .custom_logging import CustomLogger


class HTTPXClient:
    """HTTPX client for handling HTTP requests and responses."""

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Return an AsyncClient instance."""
        return httpx.AsyncClient(
            headers=self.headers,
            timeout=None,
            follow_redirects=True
        )

    def __init__(self, base_url: str, api_token: str) -> None:
        """Initialize the HTTPX client.

        Args:
            base_url (str): Base URL of the Dataverse repository
            api_token (str): API token of the Dataverse repository
        """
        self.base_url = base_url
        self.api_token = api_token
        self.headers = {'X-Dataverse-key': api_token}
        self.httpx_success_status = 200
        self.logger = CustomLogger.get_logger(__name__)
        self.semaphore = asyncio.Semaphore(10)
        self.async_sleep_time = 0  # TODO: make this configurable

    def sync_get(self, api_endpoint: str) -> httpx.Response:
        """Synchronous GET request.

        Args:
            api_endpoint (str): API endpoint to be appended to the base URL.

        """
        url = urljoin(self.base_url, api_endpoint)

        # Add explicit limits and timeouts
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

        # Create a completely new client with explicit timeouts
        with httpx.Client(
            headers=self.headers,
            timeout=None,
            follow_redirects=True,
            limits=limits
        ) as client:
            try:
                response = client.get(url)
                if response.status_code != self.httpx_success_status:
                    self.logger.error(f'HTTP request Error for {url}: {response.status_code}')
                    response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                self.logger.error(f'HTTP request Error for {url}: {exc}')
                raise

    @staticmethod
    async def write_stream_file(file_path: Path, content: bytes) -> None:
        """Write content bytes to a file."""
        # Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        Path(file_path).touch(exist_ok=True)
        with file_path.open('wb') as f:
            f.write(content)

    async def async_stream_files(self, url: str, *args: str, **kwargs: Any) -> bytes | None:
        """Asynchronous streaming GET request that returns the full content."""
        transport = httpx.AsyncHTTPTransport(local_address='0.0.0.0', retries=3)  # Force using IPV4
        try:
            async with self.semaphore, httpx.AsyncClient(
                headers=self.headers,
                timeout=None,
                follow_redirects=True,
                transport=transport,
            ) as client, client.stream('GET', url, *args, **kwargs) as response:
                if response.status_code == self.httpx_success_status:
                    # Check for empty files
                    content_length = int(response.headers.get('content-length', '-1'))
                    if content_length == 0:
                        # Return empty bytes for empty files
                        return b''

                    # For non-empty files, read all content
                    content = []
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        content.append(chunk)
                    return b''.join(content)
                return None
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            self.logger.error(f'HTTP request Error for {url}: {exc}')
            return None
