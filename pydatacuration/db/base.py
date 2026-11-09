"""Abstract base class for database backends."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from datetime import timedelta
from typing import Any
from typing import Literal

from loguru import logger
from sqlalchemy import Engine
from sqlalchemy import ScalarResult
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy.schema import CreateTable
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import col
from sqlmodel import func
from sqlmodel import inspect
from sqlmodel import select

from pydatacuration.db.sqlmodels import SCHEMA_VERSION
from pydatacuration.db.sqlmodels import Checklist
from pydatacuration.db.sqlmodels import ChecklistMetadata
from pydatacuration.db.sqlmodels import CheckResult
from pydatacuration.db.sqlmodels import ProjectMetadata
from pydatacuration.db.sqlmodels import SchemaVersion
from pydatacuration.db.sqlmodels import TableModel
from pydatacuration.db.sqlmodels import utc_now
from pydatacuration.db.sqlmodels import utc_today


class DatabaseBackend(ABC):  # noqa: PLR0904
    """Abstract base class defining the interface for all database backends.

    Subclasses must implement connection management and backend-specific operations.
    Shared CRUD logic (SQLAlchemy/SQLModel-based) is provided as concrete methods.
    """

    def __init__(self, project_number: str | None = None) -> None:
        """Initialize the database backend.

        Args:
            project_number (str | None): The project to scope queries to. ``None`` for cross-project operations only.
        """
        self.project_number = project_number

    def _require_project_number(self) -> str:
        """Return the bound project number, or raise if this backend is not bound to a project."""
        if self.project_number is None:
            msg = 'This operation requires a backend bound to a project_number.'
            raise ValueError(msg)
        return self.project_number

    # ------------------------------------------------------------------
    # Abstract connection context managers
    # ------------------------------------------------------------------

    @contextmanager
    @abstractmethod
    def get_connection(self) -> Generator[tuple[Session, Engine], None, None]:
        """Get a read-write SQLAlchemy Session + Engine.

        Yields:
            tuple[Session, Engine]: A session and engine pair for read-write operations.
        """
        ...

    @contextmanager
    @abstractmethod
    def get_readonly_connection(self) -> Generator[tuple[Session, Engine], None, None]:
        """Get a read-only SQLAlchemy Session + Engine.

        Yields:
            tuple[Session, Engine]: A session and engine pair for read-only operations.
        """
        ...

    # ------------------------------------------------------------------
    # Abstract backend-specific operations
    # ------------------------------------------------------------------

    @abstractmethod
    def create_database(self) -> None:
        """Create or ensure the database exists."""
        ...

    def create_tables(self) -> None:
        """Create the shared tables if they do not exist (parent table first, for the foreign keys).

        Uses CREATE TABLE IF NOT EXISTS rather than ``metadata.create_all``: duckdb-engine's existence check ignores
        the schema, so a same-named table in an old per-project schema would make it skip creating the table.
        """
        tables = [
            SQLModel.metadata.tables[name]
            for name in ('project_metadata', 'checklist_metadata', 'checklist', 'check_results')
        ]
        try:
            is_empty = self.get_schema_version() is None
            with self.get_connection() as (_session, engine), engine.begin() as conn:
                for table in tables:
                    conn.execute(CreateTable(table, if_not_exists=True))
            # Only a new database is known to have the current layout. An old one keeps its version
            # until scripts/db_migration.py has moved its data.
            if is_empty:
                self.set_schema_version(SCHEMA_VERSION)
        except Exception as e:
            logger.error(f'Error creating tables: {e}')

    def get_schema_version(self) -> int | None:
        """Return the database's schema version.

        Returns:
            int | None: The version in the schema_version table. Without one: 1 (the old layout) if there is a
                project_metadata table in any schema, or None if the database is empty.
        """
        with self.get_readonly_connection() as (_session, engine), engine.connect() as conn:
            inspector = inspect(conn)
            if inspector.has_table('schema_version', schema=inspector.default_schema_name):
                version = conn.execute(select(SchemaVersion.version)).scalar()
                if version is not None:
                    return version
            has_project_metadata = any(
                inspector.has_table('project_metadata', schema=schema) for schema in inspector.get_schema_names()
            )
        return 1 if has_project_metadata else None

    def set_schema_version(self, version: int) -> None:
        """Record the database's schema version, creating the schema_version table if needed."""
        version_table = SQLModel.metadata.tables['schema_version']
        with self.get_connection() as (_session, engine), engine.begin() as conn:
            conn.execute(CreateTable(version_table, if_not_exists=True))
            conn.execute(delete(version_table))
            conn.execute(insert(version_table).values(version=version))
        logger.info(f'Set the database schema version to {version}')

    def merge_records_to_table(self, sqlmodel: SQLModel) -> None:
        """Merge records into a table (upsert by primary key).

        Args:
            sqlmodel (SQLModel): The SQLModel instance to merge.
        """
        logger.debug(f'Merging records into table: {sqlmodel.__tablename__}')
        try:
            with self.get_connection() as (session, _engine):
                session.merge(sqlmodel)
                session.commit()
        except Exception as e:
            logger.error(f'Error merging records to table {sqlmodel.__tablename__}: {e}')

    # Question: This function is not used anywhere. Do we want to keep it?
    def write_records_to_table(self, sqlmodel: SQLModel) -> None:
        """Write (insert) records into a table.

        Args:
            sqlmodel (SQLModel): The SQLModel instance to insert.
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
        self, model: type[TableModel], mode: Literal['json', 'python'] | str = 'json'
    ) -> list[dict[str, Any]]:
        """Read all records from a table.

        Args:
            model (type[TableModel]): The table class to read records for.
            mode (str): Optional mode for model_dump (default is 'json').

        Returns:
            list[dict[str, Any]]: List of record dictionaries.
        """
        try:
            with self.get_readonly_connection() as (session, _engine):
                result: ScalarResult[TableModel] = session.exec(
                    select(model).where(col(model.project_number) == self._require_project_number())
                )
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
        return self.read_table_records(ProjectMetadata, mode=mode)[0]

    def read_check_results(self, mode: Literal['json', 'python'] | str = 'json') -> dict[str, Any]:
        """Read check results.

        Args:
            mode (str): Optional mode for model_dump (default is 'json').

        Returns:
            dict[str, Any]: Check results dictionary.
        """
        return {'check_results': self.read_table_records(CheckResult, mode=mode)}

    def read_checklist(self) -> list[Checklist]:
        """Read checklist table, returning model instances.

        Objects are expunged from the session so they remain usable after
        the connection context manager closes (important for PostgreSQL
        where detached objects lose attribute access).
        """
        try:
            with self.get_connection() as (session, _engine):
                rows = session.exec(
                    select(Checklist)
                    .where(Checklist.project_number == self._require_project_number())
                    .order_by(col(Checklist.id))
                ).all()
                # Expunge objects so they survive session close
                for row in rows:
                    session.expunge(row)
                return list(rows)
        except Exception as e:
            logger.error(f'Error reading checklist: {e}')
            return []

    def read_checklist_metadata(self) -> dict[str, Any] | None:
        """Read checklist metadata record."""
        try:
            with self.get_connection() as (session, _engine):
                record = session.exec(
                    select(ChecklistMetadata).where(ChecklistMetadata.project_number == self._require_project_number())
                ).first()
                if record:
                    return record.model_dump()
                logger.warning('No checklist metadata record found.')
                return None
        except Exception as e:
            logger.error(f'Error reading checklist metadata: {e}')
            return None

    def read_all_project_metadata_records(self) -> list[dict[str, Any]]:
        """Read the project metadata record of every project in a single query.

        Only the columns needed for the project table are selected.

        Returns:
            list[dict[str, Any]]: One dict per project; empty if the table does not exist yet.
        """
        columns = (
            'project_number',
            'curator_name',
            'dataset_title',
            'dataset_pid',
            'dataset_id',
            'dataset_url',
            'last_modified_datetime',
        )
        try:
            with self.get_readonly_connection() as (session, engine):
                inspector = inspect(engine)
                # Explicit schema: duckdb-engine would otherwise also match old per-project schemas.
                if not inspector.has_table('project_metadata', schema=inspector.default_schema_name):
                    return []
                query = select(*(getattr(ProjectMetadata, c) for c in columns))
                return [dict(row) for row in session.exec(query).mappings()]
        except Exception as e:
            logger.error(f'Error fetching project metadata records: {e}')
            return []

    def delete_project(self, project_number: str) -> None:
        """Delete all rows of a project from every table.

        Child rows are deleted and committed before the project_metadata row: DuckDB has no ON DELETE CASCADE,
        and checks foreign keys against the state before the transaction, so one transaction would fail.
        Not atomic, but idempotent: a failed run can simply be repeated.

        Args:
            project_number (str): The project to delete.
        """
        child_models: list[type[TableModel]] = [CheckResult, Checklist, ChecklistMetadata]
        try:
            with self.get_connection() as (session, _engine):
                for model in child_models:
                    session.exec(delete(model).where(col(model.project_number) == project_number))
                session.commit()
                session.exec(delete(ProjectMetadata).where(col(ProjectMetadata.project_number) == project_number))
                session.commit()
                logger.info(f'Deleted project: {project_number}')
        except Exception as e:
            logger.error(f'Error deleting project {project_number}: {e}')

    def update_checklist_item(
        self,
        item_id: str,
        status: str | None = None,
        comments: str | None = None,
        time_spent: timedelta | None = None,
        clear_time_spent: bool = False,
    ) -> bool:
        """Update a checklist item in the database.

        Args:
            item_id (str): The checklist item ID to update.
            status (str, optional): The status value (P, F, TBD, NA).
            comments (str, optional): The comments value.
            time_spent (timedelta, optional): The time spent value.
            clear_time_spent (bool, optional): If True, sets time_spent to None regardless of the time_spent argument.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        try:
            project_number = self._require_project_number()
            logger.debug(f'Updating checklist item {item_id} in project {project_number}')

            with self.get_connection() as (session, _engine):
                existing_item = session.exec(
                    select(Checklist).where(
                        Checklist.project_number == project_number,
                        Checklist.id == item_id,
                    )
                ).first()

                if not existing_item:
                    logger.warning(f'Checklist item {item_id} not found in project {project_number}')
                    return False

                if status is not None:
                    existing_item.status = status
                    logger.debug(f'Updated status for item {item_id}: {status}')

                if comments is not None:
                    existing_item.comments = comments
                    logger.debug(f'Updated comments for item {item_id}')

                if (time_spent is not None or clear_time_spent) and hasattr(existing_item, 'time_spent'):
                    existing_item.time_spent = None if clear_time_spent else time_spent
                    logger.debug(f'Updated time_spent for item {item_id}: {existing_item.time_spent}')

                if hasattr(existing_item, 'last_modified_datetime'):
                    existing_item.last_modified_datetime = utc_now()

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

    def read_row(self, sqlmodel: type[TableModel], column: str, value: str) -> dict[str, Any] | None:
        """Get a single row from a table based on a column value.

        Args:
            sqlmodel (type[TableModel]): The table class to query.
            column (str): The column to filter on.
            value (str): The value to match in the specified column.

        Returns:
            dict[str, Any] | None: The row data as a dictionary, or None if not found.
        """
        try:
            with self.get_readonly_connection() as (session, _engine):
                column_attr = getattr(sqlmodel, column)
                query = select(sqlmodel).where(
                    col(sqlmodel.project_number) == self._require_project_number(), column_attr == value
                )
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
        sqlmodel: type[TableModel],
        column: str,
        values: list[Any],
        mode: Literal['json', 'python'] | str = 'json',
    ) -> list[dict[str, Any]]:
        """Get rows where column value is in the provided list.

        Args:
            sqlmodel: The table class to query.
            column: The column to filter on.
            values: List of values to match.
            mode: Optional mode for model_dump.

        Returns:
            List of row data as dictionaries.
        """
        try:
            with self.get_readonly_connection() as (session, _engine):
                column_attr = getattr(sqlmodel, column)
                query = select(sqlmodel).where(
                    col(sqlmodel.project_number) == self._require_project_number(), column_attr.in_(values)
                )
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
                existing_record = session.exec(
                    select(ProjectMetadata).where(ProjectMetadata.project_number == self._require_project_number())
                ).first()

                if existing_record:
                    existing_record.log_last_update_date = utc_today()
                    existing_record.last_modified_datetime = utc_now()
                    session.add(existing_record)
                    session.commit()
                    logger.debug(f'Updated project_metadata timestamps for project {self.project_number}')
        except Exception as e:
            logger.error(f'Error updating project_metadata timestamps: {e}')

    def get_status_count(self) -> dict[str | None, int]:
        """Get the count of checklist items by status.

        Args:
            sqlmodel (type[SQLModel]): The SQLModel class representing the table.

        Returns:
            int: The number of rows in the table.
        """
        # FIXME: move this business logic to new module
        try:
            with self.get_connection() as (session, _engine):
                status_counts = dict(
                    session.exec(
                        select(Checklist.status, func.count(col(Checklist.id)))
                        .where(Checklist.project_number == self._require_project_number())
                        .group_by(col(Checklist.status))
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
        # FIXME: move this business logic to new module
        try:
            with self.get_connection() as (session, _engine):
                count = session.exec(
                    select(func.count(col(Checklist.time_spent))).where(
                        Checklist.project_number == self._require_project_number(),
                        col(Checklist.time_spent).is_not(None),
                    )
                ).one()
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
        # FIXME: move this business logic to new module
        try:
            with self.get_connection() as (session, _engine):
                count = session.exec(
                    select(func.count()).where(
                        Checklist.project_number == self._require_project_number(),
                        col(Checklist.comments).is_not(None),
                        func.trim(col(Checklist.comments)) != '',  # noqa: PLC1901
                    )
                ).one()
                return count
        except Exception as e:
            logger.error(f'Error getting comment input count: {e}')
            return 0
