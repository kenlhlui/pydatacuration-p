"""The module for SQLite/PostgreSQL database handling using SQLModel."""

from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any
from typing import Literal

from sqlalchemy import Inspector
from sqlalchemy import ScalarResult
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
from sqlmodel import inspect
from sqlmodel import select

from pydatacuration.utils.custom_logging import logger

from .sqlmodels import DatabaseModels


class DatabaseHandler:  # noqa: PLR0904
    """A class to handle SQLite and PostgreSQL operations using SQLModel."""

    def __init__(
        self,
        schema_name: str,
        db_path: Path | None = None,
        connection_string: str | None = None,
    ) -> None:
        """Initialize the Database connection.

        Args:
            schema_name: The name of the schema to use.
            db_path: Path to SQLite database file (for SQLite only).
            connection_string: Full database URL (e.g., 'postgresql://user:pass@host/db').
                              If provided, overrides db_path.

        Examples:
            # SQLite
            handler = DatabaseHandler('my_schema', db_path=Path('data.db'))

            # PostgreSQL
            handler = DatabaseHandler(
                'my_schema',
                connection_string='postgresql://user:pass@localhost/mydb'
            )

        """
        self.schema_name = schema_name

        # Determine connection string
        if connection_string:
            self.connection_string = connection_string
        elif db_path:
            self.connection_string = f'sqlite:///{db_path}'
        else:
            msg = 'Either db_path or connection_string must be provided'
            raise ValueError(msg)

        # Initialize models with connection type
        self.models = DatabaseModels(schema_name, is_sqlite=self.connection_string.startswith('sqlite'))

        # Create engine
        self._engine: Engine | None = None
        self.system_schemas = {'information_schema', 'pg_catalog', 'pg_toast'}

    @property
    def engine(self) -> Engine:
        """Get or create the database engine.

        Returns:
            The SQLAlchemy engine for database operations.

        """
        if self._engine is None:
            # PostgreSQL-specific settings for schema support
            connect_args = {}
            if self.connection_string.startswith('postgresql'):
                connect_args = {'options': f'-c search_path={self.schema_name},public'}

            self._engine = create_engine(
                self.connection_string,
                connect_args=connect_args,
                echo=False,  # Set to True for SQL debugging
                pool_timeout=10,
                pool_recycle=300,
            )
        return self._engine

    @contextmanager
    def get_connection(self) -> Generator[tuple[Session, Engine], None, None]:
        """Get a connection using the SQLModel interface.

        Yields:
            tuple: (session, engine) for database operations.

        """
        session = Session(self.engine)
        try:
            yield session, self.engine
        finally:
            session.close()

    @contextmanager
    def get_readonly_connection(self) -> Generator[tuple[Session, Engine], None, None]:
        """Get a read-only connection using the SQLModel interface.

        Yields:
            tuple: (session, engine) for read-only database operations.

        """
        # For PostgreSQL, use read-only transaction settings
        # For SQLite, use the same engine as writes (SQLite handles concurrency differently)
        if self.connection_string.startswith('postgresql'):
            connect_args = {'options': f'-c search_path={self.schema_name},public -c default_transaction_read_only=on'}
            engine = create_engine(
                self.connection_string,
                connect_args=connect_args,
                echo=False,
            )
        else:
            # For SQLite, reuse the main engine - it's simpler and more reliable
            engine = self.engine

        session = Session(engine)
        try:
            yield session, engine
        finally:
            session.close()
            # Only dispose of PostgreSQL engines we created
            if self.connection_string.startswith('postgresql') and engine != self.engine:
                engine.dispose()

    def check_schema_exists(self, schema_name: str) -> bool:
        """Check if a schema exists in the database.

        Args:
            schema_name: The name of the schema to check.

        Returns:
            bool: True if the schema exists, False otherwise.

        """
        try:
            with self.get_readonly_connection() as (_session, _engine):
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

    def create_schema(self) -> None:
        """Create a schema in the database.

        For PostgreSQL, creates a true schema.
        For SQLite, this is a no-op as SQLite doesn't support schemas.

        """
        try:
            if self.connection_string.startswith('postgresql'):
                logger.info(f'Creating schema: {self.schema_name}')
                with self.get_connection() as (session, engine), engine.begin() as conn:
                    conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"'))
                logger.info(f'Created schema: {self.schema_name}')
            else:
                logger.info('SQLite does not support schemas; skipping schema creation')
        except Exception as e:
            logger.error(f'Error creating schema {self.schema_name}: {e}')

    def create_tables(self) -> None:
        """Create all tables in the database.

        For PostgreSQL, creates the schema if it doesn't exist.
        For SQLite, schemas are simulated using table name prefixes.

        """
        # Create schema first if PostgreSQL
        if self.connection_string.startswith('postgresql'):
            self.create_schema()

        # Create all tables
        try:
            SQLModel.metadata.create_all(self.engine)
            logger.info(f'Created tables in schema: {self.schema_name}')
        except Exception as e:
            logger.error(f'Error creating tables: {e}')

    def check_table_has_records(self, table_name: str) -> bool:
        """Check whether a table has any records.

        Args:
            table_name: The name of the table to check.

        Returns:
            bool: True if the table has records, False otherwise.

        """
        try:
            with self.get_readonly_connection() as (session, engine):
                # Build the full table reference
                if self.connection_string.startswith('postgresql'):
                    full_table_name = f'"{self.schema_name}".{table_name}'
                else:
                    full_table_name = table_name

                result = session.exec(text(f'SELECT COUNT(*) FROM {full_table_name}')).first()
                logger.info(f'Query result for existing records in table {table_name}: {result}')
                if result and result > 0:
                    logger.info(f'Found existing record in {full_table_name}')
                    return True
            return False
        except Exception as e:
            logger.error(f'Error checking records in table {table_name}: {e}')
            return False

    def merge_records_to_table(self, sqlmodel: SQLModel) -> None:
        """Merge records into a table in the database using SQLModel.

        Note: This will replace existing records with the same primary key.

        Args:
            sqlmodel: The SQLModel instance to merge records for.

        """
        logger.debug(f'Merging records into table: {sqlmodel.__tablename__}')
        try:
            with self.get_connection() as (session, engine):
                # Only create the specific table for this model, not all tables in metadata
                sqlmodel.__table__.create(engine, checkfirst=True)  # type: ignore[attr-defined]
                session.merge(sqlmodel)
                session.commit()
        except Exception as e:
            logger.error(f'Error merging records to table {sqlmodel.__tablename__}: {e}')

    def write_records_to_table(self, sqlmodel: SQLModel) -> None:
        """Write records into a table in the database using SQLModel.

        Args:
            sqlmodel: The SQLModel instance to write records for.

        """
        logger.debug(f'Writing records into table: {sqlmodel.__tablename__}')
        try:
            with self.get_connection() as (session, engine):
                # Only create the specific table for this model, not all tables in metadata
                sqlmodel.__table__.create(engine, checkfirst=True)  # type: ignore[attr-defined]
                session.add(sqlmodel)
                logger.info(f'Wrote data into table: {sqlmodel.__tablename__}')
                session.commit()
                logger.info(f'Committed data to table: {sqlmodel.__tablename__}')
        except Exception as e:
            logger.error(f'Error writing records to table {sqlmodel.__tablename__}: {e}')

    def read_table_records(
        self, model: type[SQLModel], mode: Literal['json', 'python'] | str = 'json'
    ) -> list[dict[str, Any]]:
        """Read all records from a table in the database.

        Args:
            model: The SQLModel class to read records for.
            mode: Optional mode for model_dump (default is 'json').

        Returns:
            list[dict[str, Any]]: List of all records in the table.

        """
        try:
            with self.get_readonly_connection() as (session, _engine):
                result: ScalarResult[SQLModel] = session.exec(select(model))
                rows = result.all()
                if rows:
                    return [row.model_dump(mode=mode) for row in rows]
        except Exception as e:
            logger.error(f'Error fetching records from table {model.__tablename__}: {e}')

        # Return empty instance if no records found
        empty_instance = model()
        return [empty_instance.model_dump(mode='json')]

    def read_project_metadata_record(self, mode: Literal['json', 'python'] | str = 'json') -> dict[str, Any]:
        """Read project metadata record.

        Args:
            mode: Optional mode for model_dump (default is 'json').

        Returns:
            dict[str, Any]: Project metadata dictionary.

        """
        return self.read_table_records(self.models.project_metadata_record(), mode=mode)[0]

    def read_check_results(self, mode: Literal['json', 'python'] | str = 'json') -> dict[str, Any]:
        """Read check results from the check_results table.

        Args:
            mode: Optional mode for model_dump (default is 'json').

        Returns:
            dict[str, Any]: Check results dictionary.

        """
        model_class = self.models.check_results()
        check_results = {'check_results': self.read_table_records(model_class, mode=mode)}
        return check_results

    def read_checklist(self, mode: Literal['json', 'python'] | str = 'json') -> dict[str, Any]:
        """Read checklist table.

        Args:
            mode: Optional mode for model_dump (default is 'json').

        Returns:
            dict[str, Any]: Checklist dictionary.

        """
        model_class = self.models.checklist()
        checklist = {'checklist': self.read_table_records(model_class, mode=mode)}
        return checklist

    def read_schema_tables(self) -> list[str]:
        """Get the names of the tables inside a schema.

        Returns:
            list[str]: List of table names in the schema.

        """
        try:
            with self.get_readonly_connection() as (_session, engine):
                inspector = inspect(engine)
                if self.connection_string.startswith('postgresql'):
                    table_names = inspector.get_table_names(schema=self.schema_name)
                else:
                    # SQLite doesn't support schemas, get all tables
                    table_names = inspector.get_table_names()
                return table_names or []
        except Exception as e:
            logger.error(f'Error fetching schema tables for {self.schema_name}: {e}')
            return []

    def read_check_item_table_names(self) -> list[str]:
        """Get the names of the tables inside a schema, without the project_metadata table.

        Returns:
            list[str]: List of check item table names.

        """
        table_names = self.read_schema_tables()
        filtered_names = [name for name in table_names if name != 'project_metadata']
        logger.debug(f'Check item tables: {filtered_names}')
        return filtered_names

    def get_all_schema_names(self) -> list[str]:
        """Get all schema names from the database.

        Returns:
            list[str]: List of schema names, excluding system schemas.

        """
        try:
            with self.get_readonly_connection() as (_session, engine):
                inspector = inspect(engine)
                all_schemas = inspector.get_schema_names()
                # Filter out system schemas
                user_schemas = [schema for schema in all_schemas if schema not in self.system_schemas]
                logger.debug(f'Found user schemas: {user_schemas}')
                return user_schemas
        except Exception as e:
            logger.error(f'Error fetching schema names: {e}')
            return []

    def drop_schema(self, schema_name: str) -> None:
        """Drop a schema from the database.

        Args:
            schema_name: The name of the schema to drop.

        """
        try:
            with self.get_connection() as (_session, engine), engine.begin() as conn:
                if self.connection_string.startswith('postgresql'):
                    conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
                    logger.info(f'Dropped schema: {schema_name}')
                else:
                    logger.warning('SQLite does not support schema dropping; use drop table instead')
        except Exception as e:
            logger.error(f'Error dropping schema {schema_name}: {e}')

    def update_checklist_item(
        self, item_id: str, status: str | None = None, comments: str | None = None, time_spent: timedelta | None = None
    ) -> bool:
        """Update a checklist item in the database.

        Args:
            item_id: The checklist item ID to update.
            status: The status value (P, F, TBD, NA).
            comments: The comments value.
            time_spent: The time spent value.

        Returns:
            bool: True if update was successful, False otherwise.

        """
        try:
            logger.debug(f'Updating checklist item {item_id} in schema {self.schema_name}')

            with self.get_connection() as (session, engine):
                # First check if the item exists
                checklist_model = self.models.checklist()
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
                    existing_item.time_spent = time_spent
                    logger.debug(f'Updated time_spent for item {item_id}: {time_spent}')

                # Update the last modified timestamp if it exists
                if hasattr(existing_item, 'last_modified_datetime'):
                    existing_item.last_modified_datetime = datetime.now(UTC)

                session.add(existing_item)
                session.commit()

                logger.info(f'Successfully updated checklist item {item_id}')
                return True

        except Exception as e:
            logger.error(f'Error updating checklist item {item_id}: {e}')
            return False

    def sql_update_checklist_item(
        self, item_id: str, status: str | None = None, comments: str | None = None, time_spent: timedelta | None = None
    ) -> bool:
        """Alias for update_checklist_item for compatibility with DuckDB interface.

        Args:
            item_id: The checklist item ID to update.
            status: The status value (P, F, TBD, NA).
            comments: The comments value.
            time_spent: The time spent value.

        Returns:
            bool: True if update was successful, False otherwise.

        """
        return self.update_checklist_item(item_id=item_id, status=status, comments=comments, time_spent=time_spent)

    def read_row(self, sqlmodel: type[SQLModel], column: str, value: str) -> dict[str, Any] | None:
        """Get a single row from a table based on a column value.

        Args:
            sqlmodel: The SQLModel class to query.
            column: The column to filter on.
            value: The value to match in the specified column.

        Returns:
            dict[str, Any] | None: The row data as a dictionary, or None if not found.

        """
        try:
            with self.get_readonly_connection() as (session, _engine):
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

    def get_session(self) -> Session:
        """Get a database session for performing operations.

        Returns:
            A SQLModel Session for database operations.

        Example:
            with handler.get_session() as session:
                project = ProjectMetadata(...)
                session.add(project)
                session.commit()

        """
        return Session(self.engine)

    def close(self) -> None:
        """Close the database connection."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
