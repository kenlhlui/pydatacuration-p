"""PostgreSQL backend for the database interface."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from loguru import logger
from sqlmodel import Session
from sqlmodel import create_engine
from sqlmodel import text

from pydatacuration.db.base import DatabaseBackend
from pydatacuration.db.settings import DBType
from pydatacuration.db.sqlmodels import DBModels


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL backend implementation.

    Uses a persistent connection pool to a PostgreSQL server.
    Schemas are used per project, same as the DuckDB backend.
    """

    _SYSTEM_SCHEMAS: frozenset[str] = frozenset(
        {
            'pg_catalog',
            'information_schema',
            'public',
            'pg_toast',
        }
    )

    def __init__(self, schema_name: str, database_url: str) -> None:
        """Initialize the PostgreSQL backend.

        Args:
            schema_name (str): The name of the schema to use.
            database_url (str): SQLAlchemy-compatible connection URL,
                e.g. ``postgresql+psycopg://user:pass@host:5432/dbname``.
        """
        super().__init__(schema_name)
        self.database_url = database_url
        self._db_models = DBModels(schema_name, db_type=DBType(db_type='postgresql'))

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
    def system_schemas(self) -> frozenset[str]:
        """PostgreSQL-specific system schemas."""
        return self._SYSTEM_SCHEMAS

    # ------------------------------------------------------------------
    # Connection context managers
    # ------------------------------------------------------------------

    @contextmanager
    def get_connection(self) -> Generator[tuple[Session, Any], None, None]:
        """Get a read-write SQLAlchemy Session + Engine.

        Yields:
            tuple[Session, Engine]: A session and engine for read-write operations.
        """
        session = Session(self._engine, expire_on_commit=False)
        try:
            yield session, self._engine
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    get_readonly_connection = get_connection  # For PostgreSQL, we use the same engine (PostgreSQL handles concurrent reads natively). This is for compatibility with duckdb in the base.py.  # noqa: E501

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
        """No-op for PostgreSQL — the database is created externally (e.g., via Docker/admin).

        This is for compatibility with duckdb in the base.py.
        """
