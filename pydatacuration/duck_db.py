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
        db_file_path: Path
    ) -> None:
        """Initialize the DuckDB connection.

        Args:
            schema_name (str): The name of the schema to use.
            db_file (Path): The path to the DuckDB database file.

        """
        self.schema_name = schema_name
        self.db_file_path = db_file_path

    @contextmanager
    def get_connection(self):
        """Get a connection to the DuckDB database."""
        time.sleep(0.1)  # Small delay to avoid connection issues
        conn = duckdb.connect(self.db_file_path)
        try:
            logger.debug(f'Opened connection to DuckDB at {self.db_file_path}')
            yield conn
        finally:
            conn.close()
            logger.debug(f'Closed connection to DuckDB at {self.db_file_path}')

    @contextmanager
    def get_readonly_connection(self):
        """Get a read-only connection to the DuckDB database."""
        time.sleep(0.1)  # Small delay to avoid connection issues
        conn = duckdb.connect(self.db_file_path, read_only=True)
        try:
            logger.debug(f'Opened read-only connection to DuckDB at {self.db_file_path}')
            yield conn
        finally:
            conn.close()
            logger.debug(f'Closed read-only connection to DuckDB at {self.db_file_path}')

    def check_schema_exists(self, schema_name: str) -> bool:
        """Check if a schema exists in the DuckDB database."""
        try:
            logger.info(f'Checking if schema exists: {schema_name}')
            with self.get_connection() as conn:
                result = conn.sql(
                    f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}';"
                )
            return len(result) > 0
        except Exception as e:
            logger.error(f'Error checking schema {schema_name}: {e}')
            return False

    def delete_schema(self, schema_name: str) -> None:
        """Delete a schema from the DuckDB database."""
        try:
            with self.get_connection() as conn:
                conn.sql(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;')
            logger.info(f'Deleted schema: {schema_name}')
        except Exception as e:
            logger.error(f'Error deleting schema {schema_name}: {e}')

    def create_schema(self) -> None:
        """Create a schema in the DuckDB database."""
        try:
            logger.info(f'Creating schema: {self.schema_name}')
            with self.get_connection() as conn:
                conn.sql(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}";')
                logger.info(f'Created schema: {self.schema_name}')
        except Exception as e:
            logger.error(f'Error creating schema {self.schema_name}: {e}')

    def create_database(self) -> None:
        """Create the database file."""
        try:
            with self.get_connection():
                # Just opening and closing creates the database file
                pass
            logger.info(f'Created database at {self.db_file_path}')
        except Exception as e:
            logger.error(f'Error creating database at {self.db_file_path}: {e}')

    def check_table_has_records(self, table_name: str) -> bool:
        """Check whether there is an existing record."""
        try:
            with self.get_readonly_connection() as conn:
                logger.debug(f'Checking for existing records in table: {table_name} from {self.schema_name}')
                result = conn.sql(f'SELECT COUNT(*) FROM "{self.schema_name}".{table_name};').fetchone()
                logger.debug(f'Query result for existing records in table {table_name}: {result}')
                if result and result[0] > 0:
                    logger.info(f'Found existing record in "{self.schema_name}".{table_name}')
                    return True
            return False
        except Exception as e:
            logger.error(f'Error checking records in table {table_name}: {e}')
            return False

    def sql_write_records_to_table(self, sql_model: type[SQLModel]) -> None:
        """Write records to a table in the DuckDB database using SQLmodel.

        Args:
            sql_model (type[SQLModel]): The SQLModel class to write records for.

        """
        logger.info(f'Writing records to table: {sql_model.__tablename__}')
        # Use duckdb_engine connection string
        engine = create_engine(f'duckdb:///{self.db_file_path}', echo=False)

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
        SELECT dataset_pid, dataset_title, dataset_id, dataset_url, dataset_path
        FROM "{self.schema_name}".project_metadata
        LIMIT 1;
        """
        try:
            with self.get_readonly_connection() as conn:
                logger.info(f'Executing SQL to fetch dataset metadata for ticket {ticket_number} with read-only mode')
                result = conn.sql(sql).fetchone()
                if result:
                    dataset_pid = result[0] or ''
                    logger.debug(f'Fetched metadata for ticket {ticket_number}: {result}')
                    return {
                        'dataset_pid': dataset_pid,
                        'dataset_title': result[1] or '',
                        'dataset_id': result[2] or '',
                        'dataset_url': f'{base_url}/dataset.xhtml?persistentId={dataset_pid}' if base_url and dataset_pid else (result[3] or ''),
                        'dataset_path': result[4] or ''
                    }
        except Exception as e:
            logger.error(f'Error fetching metadata for ticket {ticket_number}: {e}')
        return {'dataset_pid': '', 'dataset_title': '', 'dataset_id': '', 'dataset_url': '', 'dataset_path': ''}
