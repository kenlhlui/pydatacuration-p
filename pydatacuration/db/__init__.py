"""Database package — multi-backend support for DuckDB and PostgreSQL.

The ``DB_BACKEND`` environment variable selects the backend:
    * ``duckdb``      (default) — file-based, zero-config
    * ``postgresql``  — server-based, needs a connection URL

For PostgreSQL the connection URL is resolved in this order:
    1. ``DATABASE_URL`` env var (highest priority)
    2. Assembled from individual ``POSTGRES_*`` env vars

Example ``.env`` (Docker Compose — use the service name as the host)::

    DB_BACKEND=postgresql
    DATABASE_URL=postgresql+psycopg://curation:curation@postgres:5432/curation

Or with individual vars::

    DB_BACKEND=postgresql
    POSTGRES_USER=curation
    POSTGRES_PASSWORD=curation
    POSTGRES_HOST=postgres
    POSTGRES_PORT=5432
    POSTGRES_DB=curation

For standalone (non-Docker) usage, set ``POSTGRES_HOST=localhost`` instead.
"""

import os
from pathlib import Path
from typing import Literal

from pydatacuration.db.base import DatabaseBackend
from pydatacuration.db.sqlmodels import BackendType
from pydatacuration.db.sqlmodels import DBModels
from pydatacuration.utils.custom_logging import logger


# Re-export key symbols for convenient imports
__all__ = [
    'BackendType',
    'DBModels',
    'DatabaseBackend',
    'get_backend_type',
    'get_database',
    'get_database_url',
]


def get_backend_type() -> BackendType:
    """Read ``DB_BACKEND`` from the environment.

    Returns:
        BackendType: ``'duckdb'`` or ``'postgresql'``.

    Raises:
        ValueError: If the env var contains an unsupported value.
    """
    raw = os.getenv('DB_BACKEND', 'duckdb').strip().lower()
    if raw in {'duckdb', 'postgresql', 'postgres'}:
        return 'postgresql' if raw in {'postgresql', 'postgres'} else 'duckdb'
    msg = f'Unsupported DB_BACKEND value: {raw!r}. Expected "duckdb" or "postgresql".'
    raise ValueError(msg)


def get_database_url() -> str:
    """Build a PostgreSQL connection URL from environment variables.

    Resolution order:
        1. ``DATABASE_URL`` (returned as-is)
        2. Individual ``POSTGRES_*`` vars assembled into a URL

    Returns:
        str: A SQLAlchemy-compatible PostgreSQL URL.

    Raises:
        ValueError: If neither ``DATABASE_URL`` nor the required ``POSTGRES_*`` vars are set.
    """
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Ensure the scheme uses psycopg driver if a bare postgresql:// is given
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        return database_url

    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB')

    if not all([user, password, db_name]):
        msg = (
            'PostgreSQL backend requires either DATABASE_URL or '
            'POSTGRES_USER + POSTGRES_PASSWORD + POSTGRES_DB environment variables.'
        )
        raise ValueError(msg)

    return f'postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}'


def get_database(
    schema_name: str,
    db_file: Path | None = None,
    backend: BackendType | None = None,
) -> DatabaseBackend:
    """Factory that returns the appropriate database backend instance.

    Args:
        schema_name: The schema (ticket) name.
        db_file: Path to the DuckDB file (only used when backend is ``'duckdb'``).
        backend: Explicit backend override. If ``None``, reads ``DB_BACKEND`` env var.

    Returns:
        DatabaseBackend: A concrete backend (``DuckDBBackend`` or ``PostgreSQLBackend``).

    Raises:
        ValueError: If the backend is ``'duckdb'`` and ``db_file`` is not provided.
    """
    resolved_backend = backend or get_backend_type()

    if resolved_backend == 'duckdb':
        if db_file is None:
            msg = "DuckDB backend requires a 'db_file' path."
            raise ValueError(msg)

        from pydatacuration.db.duck_db import (  # noqa: PLC0415
            DuckDBBackend,  # Note: Import here to avoid unnecessary dependencies when using PostgreSQL
        )

        logger.info(f'Using DuckDB backend with file: {db_file}')

        return DuckDBBackend(schema_name=schema_name, db_file=db_file)

    # PostgreSQL
    from pydatacuration.db.postgres import (  # noqa: PLC0415
        PostgreSQLBackend,  # Note: Import here to avoid unnecessary dependencies when using DuckDB
    )

    url = get_database_url()
    logger.info(f'Using PostgreSQL backend with URL: {url}')
    return PostgreSQLBackend(schema_name=schema_name, database_url=url)
