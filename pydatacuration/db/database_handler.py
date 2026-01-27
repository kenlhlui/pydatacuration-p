"""The module for SQLite/PostgreSQL database handling using SQLModel."""

import datetime
from collections.abc import Generator
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy import Inspector
from sqlalchemy import ScalarResult
from sqlalchemy import column
from sqlalchemy import func
from sqlalchemy import table
from sqlalchemy.engine import Engine
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import Table
from sqlmodel import create_engine
from sqlmodel import inspect
from sqlmodel import select

from pydatacuration.db.sqlmodels import DatabaseModels
from pydatacuration.utils.custom_logging import logger


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

        # Initialize models (unified table naming convention for all database types)
        self.models = DatabaseModels(schema_name)

        # Create engine
        self._engine: Engine | None = None

    @property
    def engine(self) -> Engine:
        """Get or create the database engine.

        Returns:
            The SQLAlchemy engine for database operations.

        """
        if self._engine is None:
            self._engine = create_engine(
                self.connection_string,
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
        except Exception:
            session.rollback()
            raise
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
            connect_args = {'options': '-c default_transaction_read_only=on'}
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
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            # Only dispose of PostgreSQL engines we created
            if self.connection_string.startswith('postgresql') and engine != self.engine:
                engine.dispose()

    def check_schema_exists(self, schema_name: str) -> bool:
        """Check if a schema exists in the database by looking for tables with the schema prefix.

        Args:
            schema_name: The name of the schema to check.

        Returns:
            bool: True if tables with the schema prefix exist, False otherwise.

        """
        try:
            with self.get_readonly_connection() as (_session, _engine):
                inspector: Inspector = inspect(_engine)
                table_names = inspector.get_table_names()
                # Check if any table starts with the schema prefix
                prefix = f'{schema_name}__'
                result = any(name.startswith(prefix) for name in table_names)
                logger.info(f'Schema {schema_name} exists (by table prefix): {result}')
                return result
        except Exception as e:
            logger.error(f'Error checking schema {schema_name}: {e}')
            return False

    def create_schema(self) -> None:
        """Create a schema in the database.

        With unified table naming (schema_name__table_name), this is a no-op.
        The schema is implicitly created when tables are created with the prefix.

        """
        logger.info(f'Schema {self.schema_name} will be created via table naming convention')

    def create_tables(self) -> None:
        """Create all tables in the database.

        Tables are created with the unified naming convention: schema_name__table_name.

        """
        try:
            SQLModel.metadata.create_all(self.engine)
            logger.info(f'Created tables with schema prefix: {self.schema_name}')
        except Exception as e:
            logger.error(f'Error creating tables: {e}')

    def check_table_has_records(self, table_name: str) -> bool:
        """Check whether a table has any records.

        Args:
            table_name: The name of the table to check (without schema prefix).

        Returns:
            bool: True if the table has records, False otherwise.

        """
        try:
            with self.get_readonly_connection() as (session, engine):
                # Build the full table name with schema prefix
                full_table_name = table(f'{self.schema_name}__{table_name}')

                result = session.exec(select(func.count()).select_from(full_table_name)).first()

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

        # Return empty instance if no records found for return type consistency
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
        """Get the names of the tables inside a schema (with the schema prefix).

        Returns:
            list[str]: List of table names in the schema (with prefix stripped).

        """
        try:
            with self.get_readonly_connection() as (_session, engine):
                inspector = inspect(engine)
                all_tables = inspector.get_table_names()
                # Filter tables that start with the schema prefix and strip the prefix
                prefix = f'{self.schema_name}__'
                table_names = [name[len(prefix) :] for name in all_tables if name.startswith(prefix)]
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
        """Get all schema names from the database by extracting unique prefixes from table names.

        Returns:
            list[str]: List of schema names (unique table prefixes).

        """
        try:
            with self.get_readonly_connection() as (_session, engine):
                inspector = inspect(engine)
                all_tables = inspector.get_table_names()
                # Extract unique schema prefixes from table names (format: schema__table)
                schema_names = set()
                for table_name in all_tables:
                    if '__' in table_name:
                        schema_prefix = table_name.split('__')[0]
                        schema_names.add(schema_prefix)
                user_schemas = list(schema_names)
                logger.debug(f'Found user schemas: {user_schemas}')
                return user_schemas
        except Exception as e:
            logger.error(f'Error fetching schema names: {e}')
            return []

    def drop_schema(self, schema_name: str) -> None:
        """Drop a schema from the database by dropping all tables with the schema prefix.

        Args:
            schema_name: The name of the schema to drop.

        """
        try:
            with self.get_connection() as (_session, engine):
                inspector = inspect(engine)
                all_tables = inspector.get_table_names()
                prefix = f'{schema_name}__'
                tables_to_drop: list[str] = [name for name in all_tables if name.startswith(prefix)]
                tables_to_drop_models: list[Table] = [
                    SQLModel.metadata.tables[name] for name in tables_to_drop if name in SQLModel.metadata.tables
                ]
                SQLModel.metadata.drop_all(bind=engine, tables=tables_to_drop_models)

                logger.info(f'Dropped schema: {schema_name} ({len(tables_to_drop)} tables)')
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
                    existing_item.last_modified_datetime = datetime.datetime.now().astimezone()

                session.add(existing_item)
                session.commit()

                logger.info(f'Successfully updated checklist item {item_id}')
                return True

        except Exception as e:
            logger.error(f'Error updating checklist item {item_id}: {e}')
            return False

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
