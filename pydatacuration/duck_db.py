"""The module provides an interface for interacting with DuckDB databases."""

import time
from contextlib import contextmanager
from pathlib import Path

import duckdb
from netCDF4 import Dataset
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
from sqlmodel import text

from .custom_logging import logger
from .sqlmodels import project_metadata_table


class DuckDB:
    def __init__(
        self,
        schema_name: str,
        database: Path | str = ':memory:',
    ) -> None:
        """Initialize the DuckDB connection.

        Args:
            schema_name (str): The name of the schema to use.
            database (Path | str): The path to the DuckDB database file or ':memory:' for an in-memory database.

        """
        self.schema_name = schema_name
        self.database = Path(database, 'duckdb.db')
        self.connection: duckdb.DuckDBPyConnection | None = None

    def connect(self, retries: int = 3, delay: float = 1.0) -> None:
        """Establish a connection to the DuckDB database with retry logic."""
        for attempt in range(retries):
            try:
                self.connection: duckdb.DuckDBPyConnection = duckdb.connect(self.database)
                logger.info(f'Connected to DuckDB database at {self.database}')
                return
            except Exception as e:
                if 'lock' in str(e).lower() and attempt < retries - 1:
                    logger.warning(f'Lock detected, retrying in {delay}s... (attempt {attempt + 1}/{retries})')
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(f'Failed to connect after {retries} attempts: {e}')
                    raise

    def close(self) -> None:
        """Close the connection to the DuckDB database."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info('Closed the DuckDB connection.')

    @contextmanager
    def get_connection(self):
        """Context manager for safe database connections."""
        if not self.connection:
            self.connect()
        try:
            yield self.connection
        finally:
            # Keep connection open for reuse, but you could close it here if needed
            pass

    def check_schema_exists(self, schema_name: str) -> bool:
        """Check if a schema exists in the DuckDB database."""
        if not self.connection:
            self.connect()
        result = self.connection.sql(
            f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}';"
        )
        return len(result) > 0

    def delete_schema(self, schema_name: str) -> None:
        """Delete a schema from the DuckDB database."""
        if not self.connection:
            self.connect()
        self.connection.sql(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;')
        logger.info(f'Deleted schema: {schema_name}')

    def create_schema(self, schema_name: str) -> None:
        """Create a schema in the DuckDB database."""
        if not self.connection:
            self.connect()
        self.connection.sql(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";')
        logger.info(f'Created schema: {schema_name}')

    def execute_with_retry(self, sql: str, retries: int = 3):
        """Execute SQL with retry logic for handling locks."""
        for attempt in range(retries):
            try:
                with self.get_connection() as conn:
                    return conn.sql(sql)
            except Exception as e:
                if 'lock' in str(e).lower() and attempt < retries - 1:
                    logger.warning(f'Lock detected during SQL execution, retrying... (attempt {attempt + 1}/{retries})')
                    time.sleep(0.5 * (2**attempt))  # Exponential backoff
                else:
                    raise
        return None

    @classmethod
    def create_read_only_connection(cls, database_path: str):
        """Create a read-only connection to avoid write locks."""
        return duckdb.connect(f'{database_path}?access_mode=read_only')

    def use_wal_mode(self):
        """Enable WAL mode for better concurrency (if supported)."""
        try:
            with self.get_connection() as conn:
                conn.sql('PRAGMA journal_mode=WAL;')
                logger.info('Enabled WAL mode for better concurrency')
        except Exception as e:
            logger.warning(f'Could not enable WAL mode: {e}')

    def create_metadata_table(self) -> None:
        """Create the metadata table in the DuckDB database."""
        if not self.connection:
            self.connect()
        #! placeholder
        # self.connection.sql(f"""
        #     CREATE TABLE IF NOT EXISTS "{self.schema_name}"."metadata" (
        #         id INTEGER PRIMARY KEY,
        #         key TEXT NOT NULL,
        #         value TEXT NOT NULL
        #     );
        # """)
        logger.info(f'Created metadata table in schema: {self.schema_name}')

    def main(self) -> None:
        if self.check_schema_exists(self.schema_name):
            self.delete_schema(self.schema_name)
        self.create_schema(self.schema_name)
        self.create_metadata_table()

    # Create the database
    def create_database(self) -> None:
        self.connect()
        self.close()

    # The below uses sqlmodel to create the duckdb shcema
    def sql_create_schema(self) -> None:
        self.close()

        conn = create_engine(f'duckdb:///{self.database}', echo=True).connect()

        # Create the Schema
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}";'))
        logger.info(f'Created schema: {self.schema_name}')
        conn.commit()
        logger.info(f'Creating table in schema: {self.schema_name}')
        # Create table base on SQLModel
        conn.close()
        logger.info('Closed the DuckDB connection.')

    def sql_create_tables(self, sql_model: type[SQLModel]) -> None:
        self.close()

        # Use duckdb_engine connection string
        engine = create_engine(f'duckdb:///{self.database}', echo=True)

        # Now create the table under the schema
        SQLModel.metadata.create_all(engine)

        # Insert sample data
        with Session(engine) as session:
            ds = sql_model
            session.add(ds)
            session.commit()
