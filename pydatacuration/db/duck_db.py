"""The module provides a DuckDB backend for the database interface."""

import time
from contextlib import contextmanager
from pathlib import Path

from loguru import logger
from sqlmodel import Session
from sqlmodel import create_engine

from pydatacuration.db.base import DatabaseBackend


class DuckDBBackend(DatabaseBackend):
    """DuckDB backend implementation.

    Uses a single DuckDB file with shared tables, scoped by ``project_number``.
    All operations go through SQLAlchemy/SQLModel via the ``duckdb-engine`` driver.
    """

    def __init__(self, db_file: Path, project_number: str | None = None) -> None:
        """Initialize the DuckDB backend.

        Args:
            db_file (Path): The path to the DuckDB database file.
            project_number (str | None): The project to scope queries to.
        """
        super().__init__(project_number)
        self.db_file = db_file

    # ------------------------------------------------------------------
    # Connection context managers (SQLAlchemy only — no raw duckdb.connect)
    # ------------------------------------------------------------------

    @contextmanager
    def get_connection(self):
        """Get a read-write SQLAlchemy Session + Engine.

        Yields:
            tuple[Session, Engine]: A session and engine for read-write operations.
        """
        time.sleep(0.01)  # Small delay to avoid DuckDB file-lock contention
        engine = create_engine(f'duckdb:///{self.db_file}', echo=False, pool_timeout=10, pool_recycle=300)
        session = Session(engine)
        try:
            yield session, engine
        finally:
            session.close()
            engine.dispose()

    @contextmanager
    def get_readonly_connection(self):
        """Get a read-only SQLAlchemy Session + Engine.

        Yields:
            tuple[Session, Engine]: A session and engine for read-only operations.
        """
        time.sleep(0.01)
        engine = create_engine(
            f'duckdb:///{self.db_file}',
            echo=False,
            connect_args={'read_only': True},
            pool_timeout=10,
            pool_recycle=300,
        )
        session = Session(engine)
        try:
            yield session, engine
        finally:
            session.close()
            engine.dispose()

    # ------------------------------------------------------------------
    # Backend-specific operations
    # ------------------------------------------------------------------

    def get_schema_version(self) -> int | None:
        """Return the database's schema version, or None if the file does not exist yet (see the base class)."""
        if not self.db_file.exists():
            return None
        return super().get_schema_version()

    def create_database(self) -> None:
        """Create the DuckDB database file (opening an engine connection creates it)."""
        try:
            with self.get_connection():
                pass
            logger.info(f'Created database at {self.db_file}')
        except Exception as e:
            logger.error(f'Error creating database at {self.db_file}: {e}')
