"""Database package — multi-backend support for DuckDB and PostgreSQL.

The ``DB_TYPE`` environment variable selects the backend:
    * ``duckdb``      (default) — file-based, zero-config
    * ``postgresql``  — server-based, needs a connection URL

For PostgreSQL the connection URL is resolved in this order:
    1. ``DATABASE_URL`` env var (highest priority)
    2. Assembled from individual ``POSTGRES_*`` env vars

Example ``.env`` (Docker Compose — use the service name as the host)::

    DB_TYPE=postgresql
    DATABASE_URL=postgresql+psycopg://curation:curation@postgres:5432/curation

Or with individual vars::

    DB_TYPE=postgresql
    POSTGRES_USER=curation
    POSTGRES_PASSWORD=curation
    POSTGRES_HOST=postgres
    POSTGRES_PORT=5432
    POSTGRES_DB=curation

For standalone (non-Docker) usage, set ``POSTGRES_HOST=localhost`` instead.
"""

from pathlib import Path

from loguru import logger

from pydatacuration.db.base import DatabaseBackend
from pydatacuration.db.settings import DBSettings
from pydatacuration.db.settings import DBType
from pydatacuration.db.sqlmodels import DBModels


# Re-export key symbols for convenient imports
__all__ = [
    'DBModels',
    'DBSettings',
    'DBType',
    'DatabaseBackend',
    'get_database',
    'get_database_url',
    'get_db_type',
]


def get_db_type() -> str:
    """Read ``DB_TYPE`` from the environment.

    Returns:
        str: ``'duckdb'`` or ``'postgresql'``.
    """
    return DBSettings().db_type


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
    return DBSettings().build_postgres_url()


def get_database(
    schema_name: str,
    db_file: Path | None = None,
    backend: DBType | None = None,
) -> DatabaseBackend:
    """Factory that returns the appropriate database backend instance.

    Args:
        schema_name: The schema (project) name.
        db_file: Path to the DuckDB file (only used when backend is ``'duckdb'``).
        backend: Explicit backend override. If ``None``, reads ``DB_TYPE`` env var.

    Returns:
        DatabaseBackend: A concrete backend (``DuckDBBackend`` or ``PostgreSQLBackend``).

    Raises:
        ValueError: If the backend is ``'duckdb'`` and ``db_file`` is not provided.
    """
    db_settings = DBSettings()

    resolved_backend = backend.db_type if backend is not None else db_settings.db_type

    if resolved_backend == 'duckdb':
        if db_file is None:
            msg = "DuckDB backend requires a 'db_file' path."
            raise ValueError(msg)

        from pydatacuration.db.duck_db import (  # noqa: PLC0415
            DuckDBBackend,  # Note: Import here to avoid unnecessary dependencies when using PostgreSQL
        )

        logger.debug(f'Using DuckDB backend with file: {db_file}')

        return DuckDBBackend(schema_name=schema_name, db_file=db_file)

    # PostgreSQL
    from pydatacuration.db.postgres import (  # noqa: PLC0415
        PostgreSQLBackend,  # Note: Import here to avoid unnecessary dependencies when using DuckDB
    )

    logger.debug(f'Using PostgreSQL backend with host: {db_settings.postgres_host}')
    return PostgreSQLBackend(schema_name=schema_name, database_url=db_settings.build_postgres_url())
