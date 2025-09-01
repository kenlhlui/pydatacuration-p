"""The module provides an interface for interacting with DuckDB databases."""

import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest import result

import duckdb
from sqlalchemy import Inspector
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
from sqlmodel import desc
from sqlmodel import inspect
from sqlmodel import select

from .custom_logging import logger
from .sqlmodels import DuckDBmodels


class DuckDB:
    def __init__(self, schema_name: str, db_file: Path) -> None:
        """Initialize the DuckDB connection.

        Args:
            schema_name (str): The name of the schema to use.
            db_file (Path): The path to the DuckDB database file.

        """
        self.schema_name = schema_name
        self.db_file = db_file
        self.duckdb_models = DuckDBmodels(schema_name)
        self.system_schemas = {'system.information_schema', 'system.main', 'temp.main', 'duckdb.main'}

    @contextmanager
    def get_connection(self):
        """Get a connection to the DuckDB database using duckdb connect."""
        time.sleep(0.01)  # Small delay to avoid connection issues
        conn = duckdb.connect(self.db_file)
        try:
            logger.debug(f'Opened connection to DuckDB at {self.db_file}')
            yield conn
        finally:
            conn.close()
            logger.debug(f'Closed connection to DuckDB at {self.db_file}')

    @contextmanager
    def get_readonly_connection(self):
        """Get a read-only connection to the DuckDB database using duckdb connect."""
        time.sleep(0.01)
        conn = duckdb.connect(self.db_file, read_only=True)
        try:
            logger.debug(f'Opened read-only connection to DuckDB at {self.db_file}')
            yield conn
        finally:
            conn.close()
            logger.debug(f'Closed read-only connection to DuckDB at {self.db_file}')

    @contextmanager
    def sql_get_connection(self):
        """Get a connection using the SQLmodel interface."""
        time.sleep(0.01)  # Small delay to avoid connection issues
        engine = create_engine(f'duckdb:///{self.db_file}', echo=False, pool_timeout=10, pool_recycle=300)
        session = Session(engine)
        try:
            logger.debug(f'Opened SQLModel engine connection to DuckDB at {self.db_file}')
            yield session, engine
        finally:
            # Explicitly close the engine to free up connections
            session.close()
            engine.dispose()
            logger.debug(f'Closed SQLModel engine connection to DuckDB at {self.db_file}')

    @contextmanager
    def sql_get_readonly_connection(self):
        """Get a read-only connection using the SQLmodel interface."""
        engine = create_engine(
            f'duckdb:///{self.db_file}', echo=False, connect_args={'read_only': True}, pool_timeout=10, pool_recycle=300
        )
        session = Session(engine)
        try:
            logger.debug(f'Opened SQLModel engine (read-only) connection to DuckDB at {self.db_file}')
            yield session, engine
        finally:
            # Explicitly close the engine to free up connections
            session.close()
            engine.dispose()
            logger.debug(f'Closed SQLModel engine (read-only) connection to DuckDB at {self.db_file}')

    def sql_check_schema_exists(self, schema_name: str) -> bool:
        """Check if a schema exists in the DuckDB database.

        Args:
            schema_name (str): The name of the schema to check.

        Returns:
            bool: True if the schema exists, False otherwise.
        """
        try:
            logger.debug(f'Checking if schema exists (SQLModel): {schema_name}')
            with self.sql_get_readonly_connection() as (_session, _engine):
                inspector: Inspector = inspect(_engine)
                result = inspector.has_schema(schema_name)
            logger.debug(f'Schema {schema_name} exists: {result}')
            return result
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
            logger.info(f'Created database at {self.db_file}')
        except Exception as e:
            logger.error(f'Error creating database at {self.db_file}: {e}')

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

    def sql_merge_records_to_table(self, sql_model: type[SQLModel]) -> None:
        """Merge records into a table in the DuckDB database using SQLmodel.

        * Note: This will replace existing records with the same primary key.

        Args:
            sql_model (type[SQLModel]): The SQLModel class to merge records for.

        """
        logger.debug(f'Merging records into table: {sql_model.__tablename__}')
        try:
            with self.sql_get_connection() as (session, engine):
                SQLModel.metadata.create_all(engine)  # create the table under the schema
                ds = sql_model
                session.merge(ds)
                logger.info(f'Merged sample data into table: {sql_model.__tablename__}')
                session.commit()
                logger.info(f'Committed sample data to table: {sql_model.__tablename__}')
        except Exception as e:
            logger.error(f'Error merging records to table {sql_model.__tablename__}: {e}')

    def sql_write_records_to_table(self, sql_model: type[SQLModel], ) -> None:
        """Write records into a table in the DuckDB database using SQLmodel.

        Args:
            sql_model (type[SQLModel]): The SQLModel class to write records for.

        """
        logger.debug(f'Writing records into table: {sql_model.__tablename__}')
        try:
            with self.sql_get_connection() as (session, engine):
                SQLModel.metadata.create_all(engine)  # create the table under the schema
                session.add(sql_model)
                logger.info(f'Wrote sample data into table: {sql_model.__tablename__}')
                session.commit()
                logger.info(f'Committed sample data to table: {sql_model.__tablename__}')
        except Exception as e:
            logger.error(f'Error writing records to table {sql_model.__tablename__}: {e}')

    def sql_read_table_records(self, model: type[SQLModel]) -> dict[str, Any]:
        """Read all records from a table in the DuckDB database.

        Args:
            model (type[SQLModel]): The SQLModel class to read records for.

        Returns:
            dict[str, Any]: Dictionary of all records in the table.
        """
        try:
            with self.sql_get_readonly_connection() as (session, _engine):
                SQLModel.metadata.clear()
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
        model_class = self.duckdb_models.check_result_json_single()
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
        filtered_names = [name for name in table_names if name != 'project_metadata']
        logger.debug(f'Check item tables: {filtered_names}')
        return filtered_names

    def get_all_schema_names(self) -> list[str]:
        """Get all schema names from the DuckDB database.

        Returns:
            list[str]: List of schema names, excluding system schemas
        """
        try:
            with self.sql_get_readonly_connection() as (_session, engine):
                inspector = inspect(engine)
                all_schemas = inspector.get_schema_names()
                # Filter out system schemas
                user_schemas = [schema for schema in all_schemas if schema not in self.system_schemas]
                logger.debug(f'Found user schemas: {user_schemas}')
                return user_schemas
        except Exception as e:
            logger.error(f'Error fetching schema names: {e}')
            return []
