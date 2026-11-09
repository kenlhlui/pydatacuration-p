"""PostgreSQL backend for the database interface."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlmodel import Session
from sqlmodel import create_engine

from pydatacuration.db.base import DatabaseBackend
from pydatacuration.db.settings import DBType
from pydatacuration.db.sqlmodels import DBModels


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL backend implementation.

    Uses a persistent connection pool to a PostgreSQL server.
    Shared tables scoped by ``project_number``, same as the DuckDB backend.
    """

    def __init__(self, database_url: str, project_number: str | None = None) -> None:
        """Initialize the PostgreSQL backend.

        Args:
            database_url (str): SQLAlchemy-compatible connection URL,
                e.g. ``postgresql+psycopg://user:pass@host:5432/dbname``.
            project_number (str | None): The project to scope queries to.
        """
        super().__init__(project_number)
        self.database_url = database_url
        self._db_models = DBModels(db_type=DBType(db_type='postgresql'))

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
        """Return the DBModels factory."""
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

    def create_database(self) -> None:  # noqa: PLR6301
        """No-op for PostgreSQL — the database is created externally (e.g., via Docker/admin).

        This is for compatibility with duckdb in the base.py.
        """
