"""The module provides an interface for interacting with DuckDB databases."""

import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import duckdb
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
from sqlmodel import inspect
from sqlmodel import select

from .custom_logging import logger
from .sqlmodels import DuckDBmodels


class DuckDB:
    def __init__(self, schema_name: str, db_file_path: Path) -> None:
        """Initialize the DuckDB connection.

        Args:
            schema_name (str): The name of the schema to use.
            db_file (Path): The path to the DuckDB database file.

        """
        self.schema_name = schema_name
        self.db_file_path = db_file_path
        self.duckdb_models = DuckDBmodels(schema_name)

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

    @contextmanager
    def sql_get_connection(self):
        """Get a connection using the SQLmodel interface."""
        time.sleep(0.1)  # Small delay to avoid connection issues
        engine = create_engine(f'duckdb:///{self.db_file_path}', echo=False)
        try:
            logger.debug(f'Opened SQLModel engine connection to DuckDB at {self.db_file_path}')
            yield Session(engine), engine
        finally:
            # Explicitly close the engine to free up connections
            engine.dispose()
            logger.debug(f'Closed SQLModel engine connection to DuckDB at {self.db_file_path}')

    @contextmanager
    def sql_get_readonly_connection(self):
        """Get a read-only connection using the SQLmodel interface."""
        time.sleep(0.1)  # Small delay to avoid connection issues
        engine = create_engine(f'duckdb:///{self.db_file_path}', echo=False, connect_args={'read_only': True})
        try:
            logger.debug(f'Opened SQLModel engine (read-only) connection to DuckDB at {self.db_file_path}')
            yield Session(engine), engine
        finally:
            # Explicitly close the engine to free up connections
            engine.dispose()
            logger.debug(f'Closed SQLModel engine (read-only) connection to DuckDB at {self.db_file_path}')

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
        logger.debug(f'Writing records to table: {sql_model.__tablename__}')
        try:
            with self.sql_get_connection() as (session, engine):
                SQLModel.metadata.create_all(engine)  # create the table under the schema
                ds = sql_model
                session.add(ds)
                logger.info(f'Inserted sample data into table: {sql_model.__tablename__}')
                session.commit()
                logger.info(f'Committed sample data to table: {sql_model.__tablename__}')
        except Exception as e:
            logger.error(f'Error writing records to table {sql_model.__tablename__}: {e}')

    def sql_read_table_records(self, model: type[SQLModel]):
        """Read all records from a table in the DuckDB database.

        Args:
            model (type[SQLModel]): The SQLModel class to read records for.

        Returns:
            dict[str, Any]: Dictionary of all records in the table.
        """
        try:
            # Clear any existing table definitions
            SQLModel.metadata.clear()
            with self.sql_get_readonly_connection() as (session, _engine):
                result: SQLModel | None = session.exec(select(model)).first()
                if result:
                    return result.model_dump(mode='json')
        except Exception as e:
            logger.error(f'Error fetching metadata for table project_metadata: {e}')

        # Create an INSTANCE of the model class (add parentheses)
        empty_instance = model()
        return empty_instance.model_dump(mode='json')

    def read_project_metadata_record(self) -> dict[str, Any]:
        """Read project metadata record.

        Returns:
            dict[str, Any]: Project metadata dictionary

        """
        return self.sql_read_table_records(self.duckdb_models.project_metadata_record())

    def read_check_results(self, table_name: str) -> dict[str, Any]:
        """Read check results for specific table (with check_id as table_name).

        Args:
            table_name (str): Name of the table

        Returns:
            dict[str, Any]: Check results dictionary

        """
        model_class = self.duckdb_models.check_result_json(table_name)
        return self.sql_read_table_records(model_class)

    def read_schema_tables(self) -> list[str]:
        """Get the names of the tables inside a schema.

        Returns:
            list[str]: Schema tables list

        """
        try:
            with self.sql_get_readonly_connection() as (_session, engine):
                inspector = inspect(engine)
                table_names = inspector.get_table_names(schema=self.schema_name)
                return table_names or []
        except Exception as e:
            logger.error(f'Error fetching schema tables for {self.schema_name}: {e}')
            return []

    def read_check_item_table_names(self) -> list[str]:
        """Get the names of the tables inside a schema, without the project_metadata table.

        Returns:
            list[str]: Schema tables list

        """
        table_names = self.read_schema_tables()
        return [name for name in table_names if name != 'project_metadata']
