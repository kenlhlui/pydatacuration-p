# Database Schema Version

The database layout has its own version number, separate from the app version in `pyproject.toml`. The app checks it every time it opens a database, so it never reads or writes a database whose tables it doesn't understand.

| Version | Layout |
|---|---|
| 1 | One schema per project, e.g. `"CUR-0922".checklist`. No `schema_version` table. |
| 2 | The 4 shared tables (`project_metadata`, `checklist_metadata`, `checklist`, `check_results`), keyed by `project_number`. |

The app version and the schema version change independently. Most releases don't touch the schema. A release that changes the layout bumps the schema version once, however many tables it changes.

---

## Changing the Schema

When you change a table model in [`sqlmodels.py`](../../pydatacuration/db/sqlmodels.py), for example by adding a column or changing a type:

1. **Edit the model** in `sqlmodels.py`.
2. **Bump `SCHEMA_VERSION`** in the same file, e.g. from `2` to `3`. Add a line for the new version to the comment above it.
3. **Write the new snapshots:**
   ```sh
   just schema-snapshot
   ```
   This creates `tests/schema_snapshots/v3.duckdb.sql` and `v3.postgresql.sql`, then checks that they match the models.
4. **Give existing databases a way to reach the new version.** Update [`scripts/db_migration.py`](../../scripts/db_migration.py) so it migrates the data and records the new version when it's done.
5. **Commit the model change, the version bump and the snapshots together.**

If you skip step 2, the test suite fails:

```
AssertionError: The table layout no longer matches schema version 2. Bump SCHEMA_VERSION in
pydatacuration/db/sqlmodels.py, make scripts/db_migration.py handle the change, then create the new
snapshot with: UPDATE_SCHEMA_SNAPSHOT=1 uv run pytest tests/test_schema_snapshot.py. Do not edit v2.postgresql.sql.
```

> [!IMPORTANT]
> Never edit or regenerate the snapshot of an existing version. It records what every database at that version looks like. `just schema-snapshot` only writes files that don't exist yet, so it can't overwrite one by accident.

### Without `just`

```sh
UPDATE_SCHEMA_SNAPSHOT=1 uv run pytest tests/test_schema_snapshot.py  # writes the missing snapshots, then fails on purpose
uv run pytest tests/test_schema_snapshot.py                           # passes once the snapshots match
```

---

## Upgrading a Database

If the app finds a database at an older version, it stops with this error in the logs:

```
The database is at schema version 1, but this version of the app needs version 2.
Back up the database, then run scripts/db_migration.py.
```

Back up the database and run the migration script. See the [migration script guide](../../scripts/README.md) for the options. The script records the new version only after every project has been copied, so a failed run leaves the database at its old version.

If the database is newer than the app, for example after you roll the app back to an older release, the app stops and asks you to upgrade the app. Use the newer release, or restore a backup taken before the upgrade.

> [!NOTE]
> The project list page logs this error and shows no projects. Check the logs if the list is unexpectedly empty.

---

## How It Works

### Version in code, version in the database

| Where | What |
|---|---|
| [`SCHEMA_VERSION`](../../pydatacuration/db/sqlmodels.py) | The layout this code expects. |
| `schema_version` table | The layout this database has. A single row with one `version` column. |

[`DatabaseBackend.get_schema_version()`](../../pydatacuration/db/base.py) reads the database's version:

| What the database contains | Version |
|---|---|
| A row in `schema_version` | That row's value |
| No version row, but a `project_metadata` table in any schema | 1 (the old layout, or a database created before versioning existed) |
| Neither (or, for DuckDB, no file yet) | `None`: an empty database |

### Checking on open

[`get_database()`](../../pydatacuration/db/__init__.py) compares the two versions before it returns a backend:

- **They match:** the database is remembered for the rest of the process, so later calls don't query it again.
- **The database is empty:** the check passes. `create_tables()` records the version when it creates the tables.
- **The database is older or newer:** it raises `SchemaVersionError`.

The check runs in `get_database()` because the app has no single startup point that opens the database. The DuckDB file depends on the working directory in the setup form, so every way into the database, including the API, the pages and the scripts, goes through this function.

Only the migration script turns the check off, with `get_database(..., check_schema_version=False)`, because the database it opens is meant to be behind.

### Who writes the version

| When | Who | Version written |
|---|---|---|
| A new, empty database gets its tables | `create_tables()` | `SCHEMA_VERSION` |
| An old database has been migrated | `scripts/db_migration.py`, after the last project is copied | `SCHEMA_VERSION` |
| Any other time | Nobody | |

`create_tables()` never changes the version of a database that already has tables: an old database must not be marked as current before its data has moved.

### Snapshot test

[`tests/test_schema_snapshot.py`](../../tests/test_schema_snapshot.py) stops the layout from changing without a version bump:

- It renders the `CREATE TABLE` statements from the models with SQLAlchemy, without connecting to a database.
- It compares them with `tests/schema_snapshots/v{SCHEMA_VERSION}.{dialect}.sql`.
- It checks both dialects, because some types render differently. JSON columns are `JSONB` in PostgreSQL and `JSON` in DuckDB.
- Trailing spaces are stripped, so an editor that trims whitespace doesn't break the comparison.

The snapshot covers everything that ends up in the SQL: table and column names, types, nullability, primary and foreign keys, and server defaults. Python-side defaults, such as `default_factory`, aren't part of the layout and aren't checked.

---

## Design Choices

- **A whole number, not the app version.** The schema changes far less often than the app. A separate counter only goes up when the layout changes, so "is this database compatible?" is a single comparison.
- **Fail fast, don't guess.** A mismatch stops the app instead of letting queries fail later with confusing SQL errors. It never migrates on its own: migrations rewrite data, so they run only when someone has made a backup and starts them deliberately.
- **Migrations stay manual.** The migration script is run by hand. If schema changes become frequent, the version table is the base for running migrations automatically, or for moving to a tool like [Alembic](https://alembic.sqlalchemy.org/).
- **Snapshot files, not hashes.** The snapshots are plain SQL, so a schema change shows up as a readable diff in a pull request.
- **One snapshot per version, never edited.** An old snapshot is a record of what databases at that version look like, which is what a migration from that version has to start from.

---

## Files

| File | Purpose |
|---|---|
| [`pydatacuration/db/sqlmodels.py`](../../pydatacuration/db/sqlmodels.py) | `SCHEMA_VERSION` and the `SchemaVersion` table model |
| [`pydatacuration/db/base.py`](../../pydatacuration/db/base.py) | `get_schema_version()`, `set_schema_version()`, and `create_tables()` recording the version |
| [`pydatacuration/db/__init__.py`](../../pydatacuration/db/__init__.py) | The check in `get_database()` |
| [`pydatacuration/exceptions.py`](../../pydatacuration/exceptions.py) | `SchemaVersionError` |
| [`scripts/db_migration.py`](../../scripts/db_migration.py) | Migrates old databases and records the new version |
| [`tests/test_schema_snapshot.py`](../../tests/test_schema_snapshot.py) | The snapshot test |
| [`tests/schema_snapshots/`](../../tests/schema_snapshots/) | One SQL file per version and dialect |
| [`tests/test_db_schema_version.py`](../../tests/test_db_schema_version.py) | Tests for the version check |
