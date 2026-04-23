"""Abstract base class for database backends."""

from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Literal

from sqlalchemy import ScalarResult
from sqlmodel import SQLModel
from sqlmodel import func
from sqlmodel import inspect
from sqlmodel import select
from sqlmodel import text

from pydatacuration.utils.custom_logging import logger


class DatabaseBackend(ABC):  # noqa: PLR0904
    """Abstract base class defining the interface for all database backends.

    Subclasses must implement connection management and backend-specific operations.
    Shared CRUD logic (SQLAlchemy/SQLModel-based) is provided as concrete methods.
    """

    def __init__(self, schema_name: str) -> None:
        """Initialize the database backend.

        Args:
            schema_name (str): The name of the schema to use.
        """
        self.schema_name = schema_name

    # ------------------------------------------------------------------
    # Properties that subclasses must provide
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def models(self):
        """Return the DBModels instance for this backend.

        Returns:
            DBModels: The models factory bound to this backend's schema and type information.
        """
        ...

    @property
    @abstractmethod
    def system_schemas(self) -> set[str]:
        """Return the set of system schema names to exclude from user-facing queries.

        Returns:
            set[str]: System schema names.
        """
        ...

    # ------------------------------------------------------------------
    # Abstract connection context managers
    # ------------------------------------------------------------------

    @contextmanager
    @abstractmethod
    def get_connection(self):
        """Get a read-write SQLAlchemy Session + Engine.

        Yields:
            tuple[Session, Engine]: A session and engine pair for read-write operations.
        """
        ...

    @contextmanager
    @abstractmethod
    def get_readonly_connection(self):
        """Get a read-only SQLAlchemy Session + Engine.

        Yields:
            tuple[Session, Engine]: A session and engine pair for read-only operations.
        """
        ...

    # ------------------------------------------------------------------
    # Abstract backend-specific operations
    # ------------------------------------------------------------------

    @abstractmethod
    def create_schema(self) -> None:
        """Create the schema in the database."""
        ...

    @abstractmethod
    def create_database(self) -> None:
        """Create or ensure the database exists."""
        ...

    def merge_records_to_table(self, sqlmodel: type[SQLModel]) -> None:
        """Merge records into a table (upsert by primary key).

        Args:
            sqlmodel (type[SQLModel]): The SQLModel instance to merge.
        """
        logger.debug(f'Merging records into table: {sqlmodel.__tablename__}')
        try:
            with self.get_connection() as (session, engine):
                sqlmodel.__table__.create(engine, checkfirst=True)
                session.merge(sqlmodel)
                session.commit()
        except Exception as e:
            logger.error(f'Error merging records to table {sqlmodel.__tablename__}: {e}')

    # Question: This function is not used anywhere. Do we want to keep it?
    def write_records_to_table(self, sqlmodel: type[SQLModel]) -> None:
        """Write (insert) records into a table.

        Args:
            sqlmodel (type[SQLModel]): The SQLModel instance to insert.
        """
        logger.debug(f'Writing records into table: {sqlmodel.__tablename__}')
        try:
            with self.get_connection() as (session, engine):
                sqlmodel.__table__.create(engine, checkfirst=True)
                session.add(sqlmodel)
                logger.info(f'Wrote sample data into table: {sqlmodel.__tablename__}')
                session.commit()
                logger.info(f'Committed sample data to table: {sqlmodel.__tablename__}')
        except Exception as e:
            logger.error(f'Error writing records to table {sqlmodel.__tablename__}: {e}')

    def read_table_records(
        self, model: type[SQLModel], mode: Literal['json', 'python'] | str = 'json'
    ) -> list[dict[str, Any]]:
        """Read all records from a table.

        Args:
            model (type[SQLModel]): The SQLModel class to read records for.
            mode (str): Optional mode for model_dump (default is 'json').

        Returns:
            list[dict[str, Any]]: List of record dictionaries.
        """
        try:
            with self.get_readonly_connection() as (session, _engine):
                result: ScalarResult[SQLModel] = session.exec(select(model))
                rows = result.all()
                if rows:
                    return [row.model_dump(mode=mode) for row in rows]
        except Exception as e:
            logger.error(f'Error fetching records from table: {e}')

        empty_instance = model()
        return [empty_instance.model_dump(mode='json')]

    def read_project_metadata_record(self, mode: Literal['json', 'python'] | str = 'json') -> dict[str, Any]:
        """Read project metadata record.

        Args:
            mode (str): Optional mode for model_dump (default is 'json').

        Returns:
            dict[str, Any]: Project metadata dictionary.
        """
        return self.read_table_records(self.models.project_metadata_record(), mode=mode)[0]

    def read_check_results(self, mode: Literal['json', 'python'] | str = 'json') -> dict[str, Any]:
        """Read check results.

        Args:
            mode (str): Optional mode for model_dump (default is 'json').

        Returns:
            dict[str, Any]: Check results dictionary.
        """
        model_class = self.models.check_results()
        return {'check_results': self.read_table_records(model_class, mode=mode)}

    def read_checklist(self):
        """Read checklist table, returning model instances.

        Objects are expunged from the session so they remain usable after
        the connection context manager closes (important for PostgreSQL
        where detached objects lose attribute access).
        """
        try:
            with self.get_connection() as (session, _engine):
                checklist_model = self.models.checklist()
                rows = session.exec(select(checklist_model).order_by(checklist_model.id)).all()
                # Expunge objects so they survive session close
                for row in rows:
                    session.expunge(row)
                return rows
        except Exception as e:
            logger.error(f'Error reading checklist: {e}')
            return []

    def read_checklist_metadata(self) -> dict[str, Any] | None:
        """Read checklist metadata record."""
        try:
            with self.get_connection() as (session, _engine):
                checklist_metadata_model = self.models.checklist_metadata()
                record = session.exec(select(checklist_metadata_model)).first()
                if record:
                    return record.model_dump()
                logger.warning('No checklist metadata record found.')
                return None
        except Exception as e:
            logger.error(f'Error reading checklist metadata: {e}')
            return None

    def read_schema_tables(self) -> list[str]:
        """Get the names of the tables inside the current schema.

        Returns:
            list[str]: Schema tables list.
        """
        try:
            with self.get_readonly_connection() as (_session, engine):
                inspector = inspect(engine)
                table_names = inspector.get_table_names(schema=self.schema_name)
                return table_names or []
        except Exception as e:
            logger.error(f'Error fetching schema tables for {self.schema_name}: {e}')
            return []

    def read_check_item_table_names(self) -> list[str]:
        """Get the names of the tables inside a schema, without the project_metadata table.

        Returns:
            list[str]: Schema tables list.
        """
        table_names = self.read_schema_tables()
        filtered_names = [name for name in table_names if name != 'project_metadata']
        logger.debug(f'Check item tables: {filtered_names}')
        return filtered_names

    def get_all_schema_names(self) -> list[str]:
        """Get all user schema names from the database.

        Returns:
            list[str]: List of schema names, excluding system schemas.
        """
        try:
            with self.get_readonly_connection() as (_session, engine):
                inspector = inspect(engine)
                all_schemas = inspector.get_schema_names()
                user_schemas = [schema for schema in all_schemas if schema not in self.system_schemas]
                return user_schemas
        except Exception as e:
            logger.error(f'Error fetching schema names: {e}')
            return []

    def drop_schema(self, schema_name: str) -> None:
        """Drop a schema.

        Args:
            schema_name (str): The schema to drop.
        """
        try:
            with self.get_connection() as (_session, engine), engine.begin() as conn:
                conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;'))
                logger.info(f'Dropped schema: {schema_name}')
        except Exception as e:
            logger.error(f'Error dropping schema {schema_name}: {e}')

    def update_checklist_item(
        self, item_id: str, status: str | None = None, comments: str | None = None, time_spent: timedelta | None = None
    ) -> bool:
        """Update a checklist item in the database.

        Args:
            item_id (str): The checklist item ID to update.
            status (str, optional): The status value (P, F, TBD, NA).
            comments (str, optional): The comments value.
            time_spent (timedelta, optional): The time spent value.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        try:
            logger.debug(f'Updating checklist item {item_id} in schema {self.schema_name}')

            with self.get_connection() as (session, _engine):
                checklist_model = self.models.checklist()
                existing_item = session.exec(select(checklist_model).where(checklist_model.id == item_id)).first()

                if not existing_item:
                    logger.warning(f'Checklist item {item_id} not found in schema {self.schema_name}')
                    return False

                if status is not None:
                    existing_item.status = status
                    logger.debug(f'Updated status for item {item_id}: {status}')

                if comments is not None:
                    existing_item.comments = comments
                    logger.debug(f'Updated comments for item {item_id}')

                if time_spent is not None and hasattr(existing_item, 'time_spent'):
                    existing_item.time_spent = time_spent
                    logger.debug(f'Updated time_spent for item {item_id}: {time_spent}')

                if hasattr(existing_item, 'last_modified_datetime'):
                    existing_item.last_modified_datetime = datetime.now()

                session.add(existing_item)
                session.commit()

                logger.info(f'Successfully updated checklist item {item_id}')

            # Update metadata timestamp OUTSIDE the connection context
            # to avoid holding two connections simultaneously (important for PostgreSQL pool)
            self.update_project_metadata_timestamp()
            return True

        except Exception as e:
            logger.error(f'Error updating checklist item {item_id}: {e}')
            return False

    def read_row(self, sqlmodel: type[SQLModel], column: str, value: str) -> dict[str, Any] | None:
        """Get a single row from a table based on a column value.

        Args:
            sqlmodel (type[SQLModel]): The SQLModel class to query.
            column (str): The column to filter on.
            value (str): The value to match in the specified column.

        Returns:
            dict[str, Any] | None: The row data as a dictionary, or None if not found.
        """
        try:
            with self.get_readonly_connection() as (session, _engine):
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

    def read_with_in_filter(
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
            with self.get_readonly_connection() as (session, _engine):
                column_attr = getattr(sqlmodel, column)
                query = select(sqlmodel).where(column_attr.in_(values))
                result = session.exec(query)
                rows = result.all()
                return [row.model_dump(mode=mode) for row in rows]
        except Exception as e:
            logger.error(f'Error reading with IN filter from {sqlmodel.__tablename__}: {e}')
            return []

    def update_project_metadata_timestamp(self) -> None:
        """Update the project_metadata last modified timestamps."""
        try:
            with self.get_connection() as (session, _engine):
                project_metadata_model = self.models.project_metadata_record()
                existing_record = session.exec(select(project_metadata_model)).first()

                if existing_record:
                    existing_record.log_last_update_date = datetime.today()
                    existing_record.last_modified_datetime = datetime.now()
                    session.add(existing_record)
                    session.commit()
                    logger.debug(f'Updated project_metadata timestamps for schema {self.schema_name}')
        except Exception as e:
            logger.error(f'Error updating project_metadata timestamps: {e}')

    def get_status_count(self) -> dict[str | None, int]:
        """Get the count of checklist items by status.

        Args:
            sqlmodel (type[SQLModel]): The SQLModel class representing the table.

        Returns:
            int: The number of rows in the table.
        """
        try:
            with self.get_connection() as (session, _engine):
                checklist_model = self.models.checklist()
                status_counts = dict(
                    session.exec(
                        select(checklist_model.status, func.count(checklist_model.id)).group_by(checklist_model.status)
                    ).all()
                )
                if status_counts:
                    logger.debug(f'Status counts: {status_counts}')
                    return status_counts
        except Exception as e:
            logger.error(f'Error getting status count: {e}')
        return {}

    def get_time_spent_input_count(self) -> int:
        """Get how many time_spent inputs have been entered.

        Args:
            sqlmodel (type[SQLModel]): The SQLModel class representing the table.

        Returns:
            int: The number of rows with time_spent values.
        """
        try:
            with self.get_connection() as (session, _engine):
                checklist_model = self.models.checklist()
                time_spent_counts = session.exec(
                    select(checklist_model.time_spent).where(checklist_model.time_spent != None)  # noqa: E711
                ).all()
                count = len(time_spent_counts)
                logger.debug(f'Time spent input count: {count}')
                return count
        except Exception as e:
            logger.error(f'Error getting time spent input count: {e}')
            return 0

    def get_comment_input_count(self) -> int:
        """Get how many comment inputs have been entered.

        Returns:
            int: The number of rows with comments.
        """
        try:
            with self.get_connection() as (session, _engine):
                checklist_model = self.models.checklist()
                comment_counts = session.exec(
                    select(checklist_model.comments).where(checklist_model.comments != None)  # noqa: E711
                ).all()
                count = len(comment_counts)
                logger.debug(f'Comment input count: {count}')
                return count
        except Exception as e:
            logger.error(f'Error getting comment input count: {e}')
            return 0
