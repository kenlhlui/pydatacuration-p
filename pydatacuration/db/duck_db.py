"""The module provides a DuckDB backend for the database interface."""

import time
from contextlib import contextmanager
from pathlib import Path

from sqlmodel import Session
from sqlmodel import create_engine
from sqlmodel import text

from pydatacuration.db.base import DatabaseBackend
from pydatacuration.db.settings import DBType
from pydatacuration.db.sqlmodels import DBModels
from pydatacuration.utils.custom_logging import logger


class DuckDBBackend(DatabaseBackend):
    """DuckDB backend implementation.

    Uses a single DuckDB file with schemas per project/ticket.
    All operations go through SQLAlchemy/SQLModel via the ``duckdb-engine`` driver.
    """

    _SYSTEM_SCHEMAS: frozenset[str] = frozenset(
        {
            'system.information_schema',
            'system.main',
            'temp.main',
            'db.main',
        }
    )

    def __init__(self, schema_name: str, db_file: Path) -> None:
        """Initialize the DuckDB backend.

        Args:
            schema_name (str): The name of the schema to use.
            db_file (Path): The path to the DuckDB database file.
        """
        super().__init__(schema_name)
        self.db_file = db_file
        self._db_models = DBModels(schema_name, db_type=DBType(db_type='duckdb'))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def models(self) -> DBModels:
        """Return the DBModels factory bound to this schema."""
        return self._db_models

    @property
    def system_schemas(self) -> frozenset[str]:
        """DuckDB-specific system schemas."""
        return self._SYSTEM_SCHEMAS

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

    def create_schema(self) -> None:
        """Create a schema in the DuckDB database."""
        try:
            logger.info(f'Creating schema: {self.schema_name}')
            with self.get_connection() as (_session, engine), engine.begin() as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}";'))
                logger.info(f'Created schema: {self.schema_name}')
        except Exception as e:
            logger.error(f'Error creating schema {self.schema_name}: {e}')

    def create_database(self) -> None:
        """Create the DuckDB database file (opening an engine connection creates it)."""
        try:
            with self.get_connection():
                pass
            logger.info(f'Created database at {self.db_file}')
        except Exception as e:
            logger.error(f'Error creating database at {self.db_file}: {e}')
