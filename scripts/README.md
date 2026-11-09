# Scripts

## `db_migration.py`

Migrates a database from the old layout (one schema per project) to the current layout (4 shared tables keyed by `project_number`).

| | Old layout | New layout |
|---|---|---|
| Where the tables live | One schema per project, e.g. `"CUR-0922".checklist` | The default schema (`main` in DuckDB, `public` in PostgreSQL) |
| Tables | `project_metadata`, `checklist_metadata`, `checklist`, `check_results` in every project schema | The same 4 tables, once |
| How a project is identified | By its schema name | By the `project_number` column in every table |

After the upgrade, the app reads only the new tables. Projects still in the old layout won't appear in the app until they're migrated.

### What it does

1. Creates the 4 new tables if they don't exist yet.
2. Finds every old project schema: any schema other than the default one that has a `project_metadata` table.
3. Copies each project in its own transaction:
   - Copies `project_metadata`, `checklist_metadata`, `checklist` and `check_results` with `INSERT … SELECT`. The project number comes from the old schema's `project_metadata` row and is added to every row.
   - Compares old and new row counts for each table. On a mismatch, it rolls back that project and stops.
4. Leaves the old schemas untouched.

It's safe to re-run:
- Projects already in the new tables are skipped.
- A schema without exactly one `project_metadata` row is skipped, with a warning.

### Before you run it

- **Back up the database.** For DuckDB, copy the file, e.g. `cp workdir/db/db.duckdb workdir/db/db.duckdb.pre-migration`. For PostgreSQL, use `pg_dump`.
- **Stop the app.** DuckDB allows only one writer, so the migration fails if the app holds the file open.
- **Set `DB_TYPE`** to match the database you're migrating (`duckdb` or `postgresql`). The script reads it from the environment or `.env`, like the app does.
- **PostgreSQL hasn't been tested.** The script is written for both backends, but it has only been run against DuckDB. Try it on a copy of the PostgreSQL database first.
- **The old schemas stay in the database.** The app ignores them. Once you've checked the result, remove them yourself (see [After migrating](#after-migrating)).

### Usage

DuckDB:

```bash
DB_TYPE=duckdb uv run python scripts/db_migration.py --db-file workdir/db/db.duckdb
```

PostgreSQL (the connection comes from `DATABASE_URL` or the `POSTGRES_*` variables, as in the app):

```bash
DB_TYPE=postgresql uv run python scripts/db_migration.py
```

Show the options:

```bash
uv run python scripts/db_migration.py --help
```

Example output (DEBUG lines omitted):

```text
INFO     | Found 7 old project schemas
INFO     | Migrated schema CUR-0922 as project CUR-0922
...
INFO     | Done: 7 migrated, 0 skipped
```

### After migrating

1. Start the app and check that every project appears in the project list, and that checklists, comments and check results show up for a few of them.
2. When you're satisfied, drop each old schema:

   ```sql
   DROP SCHEMA "CUR-0922" CASCADE;
   ```

   To list the old schemas on DuckDB:

   ```sql
   SELECT schema_name FROM duckdb_tables()
   WHERE table_name = 'project_metadata' AND schema_name <> 'main';
   ```

   On PostgreSQL, run the same query against `information_schema.tables` (column `table_schema`) and exclude `public`.
