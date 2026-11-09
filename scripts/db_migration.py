"""Migrate a database from the old schema-per-project layout to the shared 4-table layout.

Old layout: one schema per project, each holding project_metadata, checklist_metadata, checklist and check_results.
New layout: those 4 tables once, in the default schema (main / public), keyed by project_number.

Each project is copied in its own transaction and its row counts are checked. Projects already present in the
new tables are skipped, so the script can be re-run. The old schemas are left untouched: back up the database
before running, and drop the old schemas yourself once you have checked the result.

Usage:
    uv run python scripts/db_migration.py --db-file workdir/db/db.duckdb
    DB_TYPE=postgresql uv run python scripts/db_migration.py
"""

from pathlib import Path
from typing import Annotated

import typer
from loguru import logger
from sqlalchemy import Connection
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


def migrate_schema(conn: Connection, schema: str) -> str | None:
    """Copy one old project schema into the new tables.

    Args:
        conn (Connection): A connection inside an open transaction.
        schema (str): The old project schema to copy.

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

        conn.execute(
            insert(new_table).from_select(['project_number', *columns], select(literal(project_number), *old_table.c))
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
) -> None:
    """Copy every old per-project schema into the shared tables."""
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
                project_number = migrate_schema(conn, schema)
            (migrated if project_number else skipped).append(schema)
            if project_number:
                logger.info(f'Migrated schema {schema} as project {project_number}')

    logger.info(f'Done: {len(migrated)} migrated, {len(skipped)} skipped')


if __name__ == '__main__':
    app()
