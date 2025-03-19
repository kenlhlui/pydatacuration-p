"""HTTPX client for handing HTTP requests and responses."""
import asyncio
from types import TracebackType
from typing import Optional
from urllib.parse import urljoin

import httpx

from .custom_logging import CustomLogger


class HTTPXClient:
    """HTTPX client for handling HTTP requests and responses."""

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
        """Synchronous GET request."""
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

    async def _async_semaphore_client(self, api_endpoint: str) -> httpx.Response | list[str]:
        """Asynchronous HTTP client with semaphore."""
        url = urljoin(self.base_url, api_endpoint)
        async with self.semaphore:
            # Create a fresh client for each request
            async with httpx.AsyncClient(
                headers=self.headers,
                timeout=0,
                follow_redirects=True
            ) as client:
                try:
                    response = await client.get(url)
                    if response.status_code != self.httpx_success_status:
                        self.logger.error(f'HTTP request Error for {url}: {response.status_code}')
                    return response
                except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                    self.logger.error(f'HTTP request Error for {url}: {exc}')
                    return [url, 'Error']

    async def async_get(self, url_list: list) -> list:
        """Asynchronous GET request."""
        tasks = [self._async_semaphore_client(url) for url in url_list]
        return await asyncio.gather(*tasks)
