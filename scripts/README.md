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
   - Converts every `last_modified_datetime` value from local time to UTC, and recalculates `log_last_update_date` in UTC (see [Timestamps](#timestamps)).
   - Compares old and new row counts for each table. On a mismatch, it rolls back that project and stops.
4. Leaves the old schemas untouched, unless you pass `--drop-old` (see [Dropping the old schemas](#dropping-the-old-schemas)).

It's safe to re-run:
- Projects already in the new tables are skipped.
- A schema without exactly one `project_metadata` row is skipped, with a warning.

### Dropping the old schemas

With `--drop-old`, the script also drops each old schema (`DROP SCHEMA … CASCADE`, which removes its 4 tables). For each schema:

- The drop happens in the same transaction as the copy, so a project is either copied and dropped, or neither.
- The schema is dropped only if the row counts of all 4 tables match the project's rows in the new tables. Otherwise, it's kept, with a warning.
- A schema copied by an earlier run without `--drop-old` is dropped too, unless its project has changed in the app since then. Added or deleted rows change the counts, so the schema is kept. Check it and drop it yourself (see [After migrating](#after-migrating)).
- A schema without exactly one `project_metadata` row is kept.

Back up the database first. There's no undo.

### Before you run it

- **Back up the database.** For DuckDB, copy the file, e.g. `cp workdir/db/db.duckdb workdir/db/db.duckdb.pre-migration`. For PostgreSQL, use `pg_dump`.
- **Stop the app.** DuckDB allows only one writer, so the migration fails if the app holds the file open.
- **Set `DB_TYPE`** to match the database you're migrating (`duckdb` or `postgresql`). The script reads it from the environment or `.env`, like the app does.
- **PostgreSQL hasn't been tested.** The script is written for both backends, but it has only been run against DuckDB. Try it on a copy of the PostgreSQL database first.
- **The old schemas stay in the database by default.** The app ignores them. Once you've checked the result, re-run with `--drop-old` or remove them yourself (see [After migrating](#after-migrating)).
- **Know which time zone the old timestamps are in.** In Docker it's the `TIMEZONE` setting (default `America/Toronto`). Outside Docker it's the time zone of the machine that ran the app. Pass it with `--source-tz`.

### Timestamps

The old layout stored `last_modified_datetime` as local time with no time zone attached. The new layout stores it as UTC, still with no time zone attached, and the app shows it in each user's browser time zone.

The script reads each old value as local time in `--source-tz` (default `America/Toronto`) and converts it to UTC. Daylight saving time is handled, so `2026-01-15 12:00` becomes `17:00` UTC and `2026-07-15 12:00` becomes `16:00` UTC.

One hour a year can't be converted exactly: when clocks fall back, times between 01:00 and 02:00 happen twice, and the database picks one of the two readings. Those values can be off by an hour.

The date columns are also UTC in the new layout. The script handles them like this:

| Column | What the script does |
|---|---|
| `project_metadata.log_last_update_date` | Sets it to the UTC date of the converted `last_modified_datetime`. The app always updated both at once, so this is exact. |
| `project_metadata.log_init_date` | Copies it unchanged. A date has no time of day, so it can't be converted. For a project started in the evening (after 19:00 or 20:00 in Toronto), the UTC date would have been one day later. |
| `checklist_metadata.last_updated` | Copies it unchanged. It's the date written in the checklist YAML, not a time recorded by the app. |

### Usage

DuckDB:

```bash
DB_TYPE=duckdb uv run python scripts/db_migration.py --db-file workdir/db/db.duckdb
```

If the old timestamps aren't Toronto time:

```bash
DB_TYPE=duckdb uv run python scripts/db_migration.py --db-file workdir/db/db.duckdb --source-tz America/Vancouver
```

Migrate and drop the old schemas in one go:

```bash
DB_TYPE=duckdb uv run python scripts/db_migration.py --db-file workdir/db/db.duckdb --drop-old
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
INFO     | Done: 7 migrated, 0 skipped, 0 old schemas dropped
```

With `--drop-old`, each migrated schema also logs `Dropped old schema CUR-0922`, and the last line counts the dropped schemas.

### After migrating

1. Start the app and check that every project appears in the project list, and that checklists, comments and check results show up for a few of them.
2. When you're satisfied, re-run the script with `--drop-old`. Or drop each old schema yourself, e.g. one that `--drop-old` kept:

   ```sql
   DROP SCHEMA "CUR-0922" CASCADE;
   ```

   To list the old schemas on DuckDB:

   ```sql
   SELECT schema_name FROM duckdb_tables()
   WHERE table_name = 'project_metadata' AND schema_name <> 'main';
   ```

   On PostgreSQL, run the same query against `information_schema.tables` (column `table_schema`) and exclude `public`.
