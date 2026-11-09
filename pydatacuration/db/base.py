"""Abstract base class for database backends."""

from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Literal

from loguru import logger
from sqlalchemy import ScalarResult
from sqlalchemy import delete
from sqlmodel import SQLModel
from sqlmodel import func
from sqlmodel import inspect
from sqlmodel import select


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
    def create_database(self) -> None:
        """Create or ensure the database exists."""
        ...

    def create_tables(self) -> None:
        """Create the shared tables if they do not exist (parent table first, for the foreign keys)."""
        tables = [
            self.models.project_metadata_record().__table__,
            self.models.checklist_metadata().__table__,
            self.models.checklist().__table__,
            self.models.check_results().__table__,
        ]
        try:
            with self.get_connection() as (_session, engine):
                SQLModel.metadata.create_all(engine, tables=tables)
        except Exception as e:
            logger.error(f'Error creating tables: {e}')

    def merge_records_to_table(self, sqlmodel: type[SQLModel]) -> None:
        """Merge records into a table (upsert by primary key).

        Args:
            sqlmodel (type[SQLModel]): The SQLModel instance to merge.
        """
        logger.debug(f'Merging records into table: {sqlmodel.__tablename__}')
        try:
            with self.get_connection() as (session, _engine):
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
                result: ScalarResult[SQLModel] = session.exec(
                    select(model).where(model.project_number == self._require_project_number())
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

    def read_checklist(self) -> list[SQLModel]:
        """Read checklist table, returning model instances.

        Objects are expunged from the session so they remain usable after
        the connection context manager closes (important for PostgreSQL
        where detached objects lose attribute access).
        """
        try:
            with self.get_connection() as (session, _engine):
                checklist_model = self.models.checklist()
                rows = session.exec(
                    select(checklist_model)
                    .where(checklist_model.project_number == self._require_project_number())
                    .order_by(checklist_model.id)
                ).all()
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
                record = session.exec(
                    select(checklist_metadata_model).where(
                        checklist_metadata_model.project_number == self._require_project_number()
                    )
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
        model = self.models.project_metadata_record()
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
                if not inspect(engine).has_table(model.__tablename__):
                    return []
                query = select(*(getattr(model, c) for c in columns))
                return [dict(row) for row in session.execute(query).mappings()]
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
        child_models = [self.models.check_results(), self.models.checklist(), self.models.checklist_metadata()]
        project_metadata_model = self.models.project_metadata_record()
        try:
            with self.get_connection() as (session, _engine):
                for model in child_models:
                    session.execute(delete(model).where(model.project_number == project_number))
                session.commit()
                session.execute(
                    delete(project_metadata_model).where(project_metadata_model.project_number == project_number)
                )
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
                checklist_model = self.models.checklist()
                existing_item = session.exec(
                    select(checklist_model).where(
                        checklist_model.project_number == project_number,
                        checklist_model.id == item_id,
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
                query = select(sqlmodel).where(
                    sqlmodel.project_number == self._require_project_number(), column_attr == value
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
                query = select(sqlmodel).where(
                    sqlmodel.project_number == self._require_project_number(), column_attr.in_(values)
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
                project_metadata_model = self.models.project_metadata_record()
                existing_record = session.exec(
                    select(project_metadata_model).where(
                        project_metadata_model.project_number == self._require_project_number()
                    )
                ).first()

                if existing_record:
                    existing_record.log_last_update_date = datetime.today()
                    existing_record.last_modified_datetime = datetime.now()
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
                checklist_model = self.models.checklist()
                status_counts = dict(
                    session.exec(
                        select(checklist_model.status, func.count(checklist_model.id))
                        .where(checklist_model.project_number == self._require_project_number())
                        .group_by(checklist_model.status)
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
                checklist_model = self.models.checklist()
                count = session.exec(
                    select(func.count(checklist_model.time_spent)).where(
                        checklist_model.project_number == self._require_project_number(),
                        checklist_model.time_spent != None,  # noqa: E711
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
                checklist_model = self.models.checklist()
                count = session.exec(
                    select(func.count()).where(
                        checklist_model.project_number == self._require_project_number(),
                        checklist_model.comments.is_not(None),
                        func.trim(checklist_model.comments) != '',  # noqa: PLC1901
                    )
                ).one()
                return count
        except Exception as e:
            logger.error(f'Error getting comment input count: {e}')
            return 0
