"""PostgreSQL backend for the database interface."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlmodel import Session
from sqlmodel import create_engine
from sqlmodel import text

from pydatacuration.db.base import DatabaseBackend
from pydatacuration.db.sqlmodels import DBModels
from pydatacuration.utils.custom_logging import logger


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL backend implementation.

    Uses a persistent connection pool to a PostgreSQL server.
    Schemas are used per project/ticket, same as the DuckDB backend.
    """

    _SYSTEM_SCHEMAS: set[str] = {
        'pg_catalog',
        'information_schema',
        'public',
        'pg_toast',
    }

    def __init__(self, schema_name: str, database_url: str) -> None:
        """Initialize the PostgreSQL backend.

        Args:
            schema_name (str): The name of the schema to use.
            database_url (str): SQLAlchemy-compatible connection URL,
                e.g. ``postgresql+psycopg://user:pass@host:5432/dbname``.
        """
        super().__init__(schema_name)
        self.database_url = database_url
        self._db_models = DBModels(schema_name, backend='postgresql')

        # Persistent engine with connection pooling
        self._engine = create_engine(
            self.database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def models(self) -> DBModels:
        """Return the DBModels factory bound to this schema."""
        return self._db_models

    @property
    def system_schemas(self) -> set[str]:
        """PostgreSQL-specific system schemas."""
        return self._SYSTEM_SCHEMAS

    # Backward-compatible alias used by existing consumers
    @property
    def duckdb_models(self) -> DBModels:
        """Backward-compatible alias for ``models``."""
        return self._db_models

    # ------------------------------------------------------------------
    # Connection context managers
    # ------------------------------------------------------------------

    @contextmanager
    def get_connection(self) -> Generator[tuple[Session, Any], None, None]:
        """Get a read-write SQLAlchemy Session + Engine.

        Yields:
            tuple[Session, Engine]: A session and engine for read-write operations.
        """
        session = Session(self._engine)
        try:
            yield session, self._engine
        finally:
            session.close()

    @contextmanager
    def get_readonly_connection(self) -> Generator[tuple[Session, Any], None, None]:
        """Get a read-only SQLAlchemy Session + Engine.

        For PostgreSQL, we use the same engine (PostgreSQL handles concurrent
        reads natively). The session is opened in a non-committing mode.

        Yields:
            tuple[Session, Engine]: A session and engine for read-only operations.
        """
        session = Session(self._engine)
        try:
            yield session, self._engine
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Backend-specific operations
    # ------------------------------------------------------------------

    def create_schema(self) -> None:
        """Create a schema in the PostgreSQL database."""
        try:
            logger.info(f'Creating schema: {self.schema_name}')
            with self._engine.begin() as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}";'))
                logger.info(f'Created schema: {self.schema_name}')
        except Exception as e:
            logger.error(f'Error creating schema {self.schema_name}: {e}')

    def create_database(self) -> None:  # noqa: PLR6301
        """No-op for PostgreSQL — the database is created externally (e.g., via Docker/admin)."""
        logger.info(
            'PostgreSQL database already exists (managed externally). Skipping create_database().'
        )

    # ------------------------------------------------------------------
    # Backward-compatible aliases for old connection method names
    # ------------------------------------------------------------------

    @contextmanager
    def sql_get_connection(self) -> Generator[tuple[Session, Any], None, None]:
        """Backward-compatible alias for ``get_connection``."""
        with self.get_connection() as (session, engine):
            yield session, engine

    @contextmanager
    def sql_get_readonly_connection(self) -> Generator[tuple[Session, Any], None, None]:
        """Backward-compatible alias for ``get_readonly_connection``."""
        with self.get_readonly_connection() as (session, engine):
            yield session, engine

    def dispose(self) -> None:
        """Dispose the connection pool. Call on application shutdown."""
        self._engine.dispose()
        logger.info('PostgreSQL connection pool disposed.')
