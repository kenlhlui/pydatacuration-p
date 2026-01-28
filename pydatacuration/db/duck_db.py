"""The module provides an interface for interacting with DuckDB databases."""

import time
from contextlib import contextmanager
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any
from typing import Literal

import duckdb
from sqlalchemy import Inspector
from sqlalchemy import ScalarResult
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
from sqlmodel import inspect
from sqlmodel import select
from sqlmodel import text

from pydatacuration.db.sqlmodels import DuckDBmodels
from pydatacuration.utils.custom_logging import logger


class DuckDB:  # noqa: PLR0904
    """Class for interacting with DuckDB databases."""

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
            yield conn
        finally:
            conn.close()

    @contextmanager
    def get_readonly_connection(self):
        """Get a read-only connection to the DuckDB database using duckdb connect."""
        time.sleep(0.01)
        conn = duckdb.connect(self.db_file, read_only=True)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def sql_get_connection(self):
        """Get a connection using the SQLmodel interface."""
        engine = create_engine(f'duckdb:///{self.db_file}', echo=False, pool_timeout=10, pool_recycle=300)
        session = Session(engine)
        try:
            yield session, engine
        finally:
            # Explicitly close the engine to free up connections
            session.close()
            engine.dispose()

    @contextmanager
    def sql_get_readonly_connection(self):
        """Get a read-only connection using the SQLmodel interface."""
        engine = create_engine(
            f'duckdb:///{self.db_file}', echo=False, connect_args={'read_only': True}, pool_timeout=10, pool_recycle=300
        )
        session = Session(engine)
        try:
            yield session, engine
        finally:
            # Explicitly close the engine to free up connections
            session.close()
            engine.dispose()

    def sql_check_schema_exists(self, schema_name: str) -> bool:
        """Check if a schema exists in the DuckDB database.

        Args:
            schema_name (str): The name of the schema to check.

        Returns:
            bool: True if the schema exists, False otherwise.
        """
        try:
            with self.sql_get_readonly_connection() as (_session, _engine):
                inspector: Inspector = inspect(_engine)

                # Try the schema name as-is first
                result = inspector.has_schema(schema_name)
                logger.info(f'Schema {schema_name} exists (direct): {result}')

                if not result:
                    # Try without quotes if it has them
                    clean_name = schema_name.strip('"')
                    if clean_name != schema_name:
                        result = inspector.has_schema(clean_name)
                        logger.info(f'Schema {clean_name} exists (unquoted): {result}')

                return result
        except Exception as e:
            logger.error(f'Error checking schema {schema_name}: {e}')
            return False

    # def delete_schema(self, schema_name: str) -> None:
    #     """Delete a schema from the DuckDB database."""
    #     try:
    #         with self.get_connection() as conn:
    #             conn.sql(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;')
    #         logger.info(f'Deleted schema: {schema_name}')
    #     except Exception as e:
    #         logger.error(f'Error deleting schema {schema_name}: {e}')

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
                result = conn.sql(f'SELECT COUNT(*) FROM "{self.schema_name}".{table_name};').fetchone()
                logger.info(f'Query result for existing records in table {table_name}: {result}')
                if result and result[0] > 0:
                    logger.info(f'Found existing record in "{self.schema_name}".{table_name}')
                    return True
            return False
        except Exception as e:
            logger.error(f'Error checking records in table {table_name}: {e}')
            return False

    def sql_merge_records_to_table(self, sqlmodel: type[SQLModel]) -> None:
        """Merge records into a table in the DuckDB database using SQLmodel.

        * Note: This will replace existing records with the same primary key.

        Args:
            sql_model (type[SQLModel]): The SQLModel class to merge records for.

        """
        logger.debug(f'Merging records into table: {sqlmodel.__tablename__}')
        try:
            with self.sql_get_connection() as (session, engine):
                # Only create the specific table for this model, not all tables in metadata
                sqlmodel.__table__.create(engine, checkfirst=True)
                ds = sqlmodel
                session.merge(ds)
                session.commit()
        except Exception as e:
            logger.error(f'Error merging records to table {sqlmodel.__tablename__}: {e}')

    def sql_write_records_to_table(
        self,
        sqlmodel: type[SQLModel],
    ) -> None:
        """Write records into a table in the DuckDB database using SQLmodel.

        Args:
            sql_model (type[SQLModel]): The SQLModel class to write records for.

        """
        logger.debug(f'Writing records into table: {sqlmodel.__tablename__}')
        try:
            with self.sql_get_connection() as (session, engine):
                # Only create the specific table for this model, not all tables in metadata
                sqlmodel.__table__.create(engine, checkfirst=True)
                session.add(sqlmodel)
                logger.info(f'Wrote sample data into table: {sqlmodel.__tablename__}')
                session.commit()
                logger.info(f'Committed sample data to table: {sqlmodel.__tablename__}')
        except Exception as e:
            logger.error(f'Error writing records to table {sqlmodel.__tablename__}: {e}')

    def sql_read_table_records(
        self, model: type[SQLModel], mode: Literal['json', 'python'] | str = 'json'
    ) -> list[dict[str, Any]]:
        """Read all records from a table in the DuckDB database.

        Args:
            model (type[SQLModel]): The SQLModel class to read records for.
            mode (str): Optional mode for model_dump (default is 'json').

        Returns:
            dict[str, Any]: Dictionary of all records in the table.
        """
        try:
            with self.sql_get_readonly_connection() as (session, _engine):
                SQLModel.metadata.clear()
                result: ScalarResult[SQLModel] = session.exec(select(model))
                rows = result.all()
                if rows:
                    new_result = [row.model_dump(mode=mode) for row in rows]
                    return new_result
        except Exception as e:
            logger.error(f'Error fetching metadata for table project_metadata: {e}')

        # Create an INSTANCE of the model class (add parentheses)
        empty_instance = model()
        return empty_instance.model_dump(mode='json')

    def read_project_metadata_record(self, mode: Literal['json', 'python'] | str = 'json') -> dict[str, Any]:
        """Read project metadata record.

        Args:
            mode (str): Optional mode for model_dump (default is 'json').

        Returns:
            dict[str, Any]: Project metadata dictionary

        """
        return self.sql_read_table_records(self.duckdb_models.project_metadata_record(), mode=mode)[0]

    def read_check_results(self, mode: Literal['json', 'python'] | str = 'json') -> dict[str, Any]:
        """Read check results for specific table (with check_id as table_name).

        Returns:
            dict[str, Any]: Check results dictionary

        """
        model_class = self.duckdb_models.check_results()
        check_results = {'check_results': self.sql_read_table_records(model_class, mode=mode)}
        return check_results

    def read_checklist(self):
        """Read checklist table, returning model instances."""
        with self.sql_get_connection() as (session, engine):
            checklist_model = self.duckdb_models.checklist()
            rows = session.exec(select(checklist_model)).all()
            return rows

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

    def sql_drop_schema(self, schema_name: str) -> None:
        """Drop the current schema."""
        try:
            with self.sql_get_connection() as (_session, engine), engine.begin() as conn:
                conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;'))
                logger.info(f'Dropped schema: {schema_name}')
        except Exception as e:
            logger.error(f'Error dropping schema {schema_name}: {e}')

    def sql_update_checklist_item(
        self, item_id: str, status: str | None = None, comments: str | None = None, time_spent: timedelta | None = None
    ) -> bool:
        """Update a checklist item in the DuckDB database.

        Args:
            item_id (str): The checklist item ID to update
            status (str, optional): The status value (P, F, TBD, NA)
            comments (str, optional): The comments value
            time_spent (str, optional): The time spent value

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            logger.debug(f'Updating checklist item {item_id} in schema {self.schema_name}')

            with self.sql_get_connection() as (session, engine):
                # First check if the item exists
                checklist_model = self.duckdb_models.checklist()
                existing_item = session.exec(select(checklist_model).where(checklist_model.id == item_id)).first()

                if not existing_item:
                    logger.warning(f'Checklist item {item_id} not found in schema {self.schema_name}')
                    return False

                # Update the fields that were provided
                if status is not None:
                    existing_item.status = status
                    logger.debug(f'Updated status for item {item_id}: {status}')

                if comments is not None:
                    existing_item.comments = comments
                    logger.debug(f'Updated comments for item {item_id}')

                if time_spent is not None and hasattr(existing_item, 'time_spent'):
                    # Assuming there's a time_spent field in the model
                    existing_item.time_spent = time_spent
                    logger.debug(f'Updated time_spent for item {item_id}: {time_spent}')

                # Update the last modified timestamp if it exists
                if hasattr(existing_item, 'last_modified_datetime'):
                    existing_item.last_modified_datetime = datetime.now()

                session.add(existing_item)
                session.commit()

                logger.info(f'Successfully updated checklist item {item_id}')
                return True

        except Exception as e:
            logger.error(f'Error updating checklist item {item_id}: {e}')
            return False

    def sql_read_row(self, sqlmodel: type[SQLModel], column: str, value: str) -> dict[str, Any] | None:
        """Get a single row from a table based on a column value.

        Args:
            sqlmodel (type[SQLModel]): The SQLModel class to query.
            column (str): The column to filter on.
            value (str): The value to match in the specified column.

        Returns:
            dict[str, Any] | None: The row data as a dictionary, or None if not found.

        """
        try:
            with self.sql_get_readonly_connection() as (session, _engine):
                # Get the actual column attribute from the model
                column_attr = getattr(sqlmodel, column)
                query = select(sqlmodel).where(column_attr == value)
                result = session.exec(query)
                row = result.first()
                if row:
                    return row.model_dump(mode='json')
                return None
        except Exception as e:
            logger.error(f'Error reading row from {sqlmodel.__tablename__}: {e}')
            return None

    def sql_read_with_in_filter(
        self,
        sqlmodel: type[SQLModel],
        column: str,
        values: list[Any],
        mode: Literal['json', 'python'] | str = 'json',
    ) -> list[dict[str, Any]]:
        """Get rows where column value is in the provided list.

        Args:
            sqlmodel: The SQLModel class to query.
            column: The column to filter on.
            values: List of values to match.
            mode: Optional mode for model_dump.

        Returns:
            List of row data as dictionaries.
        """
        try:
            with self.sql_get_readonly_connection() as (session, _engine):
                column_attr = getattr(sqlmodel, column)
                query = select(sqlmodel).where(column_attr.in_(values))
                result = session.exec(query)
                rows = result.all()
                return [row.model_dump(mode=mode) for row in rows]
        except Exception as e:
            logger.error(f'Error reading with IN filter from {sqlmodel.__tablename__}: {e}')
            return []
