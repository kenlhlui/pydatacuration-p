"""The module provides an interface for interacting with DuckDB databases."""

import time
from contextlib import contextmanager
from pathlib import Path

import duckdb
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine

from .custom_logging import logger


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

    def create_schema(self) -> None:
        """Create a schema in the DuckDB database."""
        if not self.connection:
            self.connect()
        self.connection.sql(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}";')
        logger.info(f'Created schema: {self.schema_name}')
        self.close()
        logger.info('Closed the DuckDB connection after creating schema.')

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
        logger.info(f'Creating read-only connection to {database_path}')
        return duckdb.connect(f'{database_path}?access_mode=read_only')

    def use_wal_mode(self):
        """Enable WAL mode for better concurrency (if supported)."""
        try:
            with self.get_connection() as conn:
                conn.sql('PRAGMA journal_mode=WAL;')
                logger.info('Enabled WAL mode for better concurrency')
        except Exception as e:
            logger.warning(f'Could not enable WAL mode: {e}')

    # Create the database
    def create_database(self) -> None:
        self.connect()
        self.close()

    def sql_write_records_to_table(self, sql_model: type[SQLModel]) -> None:
        self.close()

        # Use duckdb_engine connection string
        engine = create_engine(f'duckdb:///{self.database}', echo=False)

        # Now create the table under the schema
        SQLModel.metadata.create_all(engine)

        # Insert sample data
        with Session(engine) as session:
            ds = sql_model
            session.add(ds)
            logger.info(f'Inserted sample data into table: {sql_model.__tablename__}')
            session.commit()
            logger.info(f'Committed sample data to table: {sql_model.__tablename__}')

    def get_metadata_dict(self, ticket_number: str, base_url: str = '') -> dict:
        """Get dataset metadata as dictionary for API response using read-only mode."""
        sql = f"""
        SELECT dataset_pid, dataset_title, dataset_id, dataset_url
        FROM "{self.schema_name}".project_metadata 
        WHERE ticket_number = '{ticket_number}'
        LIMIT 1;
        """
        logger.info(f'Executing SQL to get metadata: {sql.strip()}')
        # Use read-only connection to avoid locks
        conn = self.create_read_only_connection(str(self.database))

        try:
            result = conn.sql(sql).fetchone()
            logger.info(f'Query result: {result}')

            if result:
                dataset_pid = result[0] or ''
                logger.info(f'Fetched metadata for ticket {ticket_number}: PID={dataset_pid}, Title={result[1]}, ID={result[2]}, URL={result[3]}')
                return {
                    'dataset_pid': dataset_pid,
                    'dataset_title': result[1] or '',
                    'dataset_id': result[2] or '',
                    'dataset_url': f'{base_url}/dataset.xhtml?persistentId={dataset_pid}' if base_url and dataset_pid else (result[3] or '')
                }
        finally:
            conn.close()

        return {'dataset_pid': '', 'dataset_title': '', 'dataset_id': '', 'dataset_url': ''}
