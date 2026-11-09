"""Migrate a database from the old schema-per-project layout to the shared 4-table layout.

Old layout: one schema per project, each holding project_metadata, checklist_metadata, checklist and check_results.
New layout: those 4 tables once, in the default schema (main / public), keyed by project_number.

Each project is copied in its own transaction and its row counts are checked. Projects already present in the
new tables are skipped, so the script can be re-run. The old schemas are left untouched: back up the database
before running, and drop the old schemas yourself once you have checked the result.

Timestamps: the old datetime columns hold naive local time; the new ones hold naive UTC. Pass the time zone the
old data was recorded in with --source-tz (default America/Toronto, the Docker default). Times inside the repeated
hour when clocks fall back are ambiguous; the database picks one of the two readings.
Dates: log_last_update_date is set to the UTC date of the converted last_modified_datetime. log_init_date has no
time of day, so it can't be converted and is copied as is. checklist_metadata.last_updated comes from the checklist
YAML, not the clock, and is copied as is.

Usage:
    uv run python scripts/db_migration.py --db-file workdir/db/db.duckdb
    uv run python scripts/db_migration.py --db-file workdir/db/db.duckdb --source-tz America/Vancouver
    DB_TYPE=postgresql uv run python scripts/db_migration.py
"""

from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

import typer
from loguru import logger
from sqlalchemy import Connection
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import cast
from sqlalchemy import column
from sqlalchemy import func
from sqlalchemy import insert
from sqlalchemy import literal
from sqlalchemy import select
from sqlalchemy import table
from sqlmodel import SQLModel

from pydatacuration.db import get_database


# Parent table first, for the foreign keys.
TABLE_NAMES = ('project_metadata', 'checklist_metadata', 'checklist', 'check_results')

app = typer.Typer()


def find_old_schemas(conn: Connection) -> list[str]:
    """Return the names of the old per-project schemas (every non-default schema with a project_metadata table)."""
    info_tables = table('tables', column('table_schema'), column('table_name'), schema='information_schema')
    query = select(info_tables.c.table_schema).where(
        info_tables.c.table_name == 'project_metadata',
        info_tables.c.table_schema != func.current_schema(),
    )
    return sorted(conn.execute(query).scalars())


def migrate_schema(conn: Connection, schema: str, source_tz: str) -> str | None:
    """Copy one old project schema into the new tables, converting datetimes from source_tz to UTC.

    Args:
        conn (Connection): A connection inside an open transaction.
        schema (str): The old project schema to copy.
        source_tz (str): IANA time zone the old datetimes were recorded in (e.g. America/Toronto).

    Returns:
        str | None: The migrated project number, or None if the schema was skipped.

    Raises:
        RuntimeError: If the copied row counts do not match.
    """
    old_project_metadata = table('project_metadata', column('project_number'), schema=schema)
    project_numbers = conn.execute(select(old_project_metadata.c.project_number)).scalars().all()
    if len(project_numbers) != 1:
        logger.warning(f'Skipping schema {schema}: expected 1 project_metadata row, found {len(project_numbers)}')
        return None
    project_number = project_numbers[0]

    new_project_metadata = SQLModel.metadata.tables['project_metadata']
    already_migrated = conn.execute(
        select(func.count())
        .select_from(new_project_metadata)
        .where(new_project_metadata.c.project_number == project_number)
    ).scalar_one()
    if already_migrated:
        logger.info(f'Skipping schema {schema}: project {project_number} is already migrated')
        return None

    for name in TABLE_NAMES:
        new_table = SQLModel.metadata.tables[name]
        # The old tables have the same columns as the new ones, minus project_number on the child tables.
        columns = [c.name for c in new_table.columns if c.name != 'project_number']
        old_table = table(name, *(column(c) for c in columns), schema=schema)
        # Old datetimes are naive local time in source_tz; the new ones are naive UTC.
        # timezone(tz, ts) reads ts as local time in tz; timezone('UTC', ...) turns that back into naive UTC.
        values = {
            c: func.timezone('UTC', func.timezone(source_tz, old_table.c[c]))
            if isinstance(new_table.c[c].type, DateTime)
            else old_table.c[c]
            for c in columns
        }
        if name == 'project_metadata':
            # A bare date can't be converted to UTC, but this one was always written together with
            # last_modified_datetime, so take the date of the converted datetime.
            values['log_last_update_date'] = cast(values['last_modified_datetime'], Date)

        conn.execute(
            insert(new_table).from_select(
                ['project_number', *columns], select(literal(project_number), *values.values())
            )
        )

        old_count = conn.execute(select(func.count()).select_from(old_table)).scalar_one()
        new_count = conn.execute(
            select(func.count()).select_from(new_table).where(new_table.c.project_number == project_number)
        ).scalar_one()
        if old_count != new_count:
            msg = f'{schema}.{name}: copied {new_count} rows, expected {old_count}'
            raise RuntimeError(msg)
        logger.debug(f'{schema}.{name}: copied {new_count} rows')

    return project_number


@app.command()
def main(
    db_file: Annotated[
        Path | None, typer.Option(help='DuckDB file to migrate. Not needed when DB_TYPE=postgresql.')
    ] = None,
    source_tz: Annotated[
        str, typer.Option(help='Time zone the old timestamps were recorded in. They are converted to UTC.')
    ] = 'America/Toronto',
) -> None:
    """Copy every old per-project schema into the shared tables."""
    ZoneInfo(source_tz)  # Fail early on an unknown time zone name.
    db = get_database(db_file=db_file)
    db.create_tables()

    migrated, skipped = [], []
    with db.get_connection() as (_session, engine):
        with engine.connect() as conn:
            schemas = find_old_schemas(conn)
        logger.info(f'Found {len(schemas)} old project schemas')

        for schema in schemas:
            # One transaction per project: a failure rolls back that project only, and stops the run.
            with engine.begin() as conn:
                project_number = migrate_schema(conn, schema, source_tz)
            (migrated if project_number else skipped).append(schema)
            if project_number:
                logger.info(f'Migrated schema {schema} as project {project_number}')

    logger.info(f'Done: {len(migrated)} migrated, {len(skipped)} skipped')


if __name__ == '__main__':
    app()
