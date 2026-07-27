## 0.1.2 (2026-07-27)

### Fix

- refresh (erase) the form input when the back button is clicked and it's redirected to the checklist page (#501)

### Refactor

- apply unified action button across modules (#502)

## 0.1.1 (2026-07-15)

### Fix

- **ui**: reset for checklist selection menu with reset button (#498)

## 0.1.0 (2026-07-15)

### Feat

- **ui**: flaoting menu in the checklist page (#492)
- remove the time spent button (#454)
- added checking data sources and related dataset entries (#453)
- export the word file (#451)
- added the view mode access to the delete page (#445)
- update app settings to include reconnect timeout and reload options (#397)
- added metadata to the checklist model (#357)
- fixing the error checklist that crashes the selection (#355)
- changed the res to by dynamically mounted, rather is in the doc… (#273)
- added the exceptions for the ds_read_access (#257)
- added checklist_type to the API endpoint (get_schemas) and display in the landing page
- changed the default checklist selection to high
- added change of color based on the level.
- added dynamic change of level of checklist in the title.
- Changed the title of the index.html page
- added workable version for the selection of medium & high level checklist
- added new_dir to gitignore.
- updated the CLI guide
- added podman-compose.yml
- updated the correct user to allow `rm -rf` without sudo;  added health check; removed unused comment;
- changed to make the files write and readable in the volumes
- workable version for reading and writing to a local volume
- added docker compose for building and configuring the app
- added dockerignore file
- consolidated the js files
- workable version for loading results to the duckdb
- added writing status, comments and time_spent to duckdb
- refactored the download class for exporting dv_tree metadata
- added help text to the options; solved the showing of base_url if there's is an input for the TUI
- added TyperOptions for typer options centralized management
- streaming logs and reference back to FAST API terminal and frontend HTML
- changed emoji for Resume Work
- added UTL logo to the pages
- formatting
- workable version for deleting the schema using the UI
- uses duckdb checklist to render the yaml adn checklist
- using duckdb for loading the checklist
- Added writing checklist to duckdb
- added MAIN_DIR to the .env variable, for assigning the main (top working dir). By default will be workdir
- added merging  check_results to a same table `check_results`
- removed unused get_check_results that uses json file for loading the checklist
- added display_name for the project displaying in the main.html drop down menu
- removed the obsolete CheckResultBuilder and its export to json
- changed log_init_date to be handle by duckdb side rather than python side, making sure the initial value is preserved
- added log_last_update_date writing to project metadata
- store dataset_id in Checker class for improved metadata handling
- made dataset versioned id (dataset_id) as the primary key in ProjectMetadata
- added datasetid (persistent id of dataset) to the ProjectMetadata.
- using sqlmodel for checking sql_check_schema_exists
- workable version for loading results from duckdb
- replaced the old get_check_results (duckdb) to read_check_results (SQLmodel)
- created `sql_read_table` for reading sql records; replacted the old `sql_get_metadata_dict` method
- replated the original get_metadata_dict (duckdb method) to sql_get_metadata_dict (SQLmodel method)
- Added default values to the DuckDBmodels
- added new context manager for SQLmodels
- Added description to the sqlmodels
- added turing results to a nested list (list(dict))
- workable version for fetching records from duckdb inside app.py
- added workable version for writing check result (list) into a duckdb
- added last_modified_datetime to the ProjectMetadata model
- added CheckResultList model
- changed the type of log_init_date log_last_update_date to DATE in SQL
- added try methods to the duckdb functions.
- added check_table_has_records to replace the _records_exists in checker.py
- switched using context manager for get_metadata_dict
- workable version for writing dataset basic metadata to db
- workable version for loading duckdb as an instance to Checker
- moved DuckDBmodels as a class for unifying the schema names within the class when writing records in sqlmodels.py
- switched using duckdb to create schema instead of SQL model.
- changed project_metadata_table to project_metadata_record
- workable version for creating a table using sqlmodel under a specific schema
- initial workable version for duckdb creation.
- migrated confirm whether to delete directory  to pydatacuration/directory_manager.py from pydatacuration/utils.py
- added duckdb to pyproject.toml
- removed out template files
- unified the output in console and log file.
- added rich support for the console print
- ditched using custom logging, and use loguru now

### Fix

- **ui**: fix the order and display of the status counter in the 'Status and Time Dashboard'. (#495)
- version string in .release-please-manifest.json
- sorting of the yaml to word; regulate the id of the checklist item can only be int or float (#470)
- allow no (empty0 string (#468)
- dots in schema name that breaks the whole code (#467)
- counting timer will be stopped if some input was made (#381)
- improve table cell overflow handling and badge font sizing (#377)
- fixed the serialization of the time_spent field.
- update project deletion to use ticket number instead of name (#264)
- fixed the heading
- fix the uv lock
- fix the python version in the pyproject.toml
- fix the broken link in README.md
- create workdir for user files in Dockerfile; update README with volume mapping examples
- added endpoint for healthcheck
- fixed the permission issue for docker compose
- added back res to the docker image; added .env to the docker ignore feat: .env file is not externally managed
- fixed populating curator name and Curator email;
- remove unreachable/ invalid code
- fixed the debug.log does not output to the ticket_number/logs
- fixed the --main_dir parameter that no longer need in the setup
- removed unused imports and functions
- force reloading project_metadata when using reume/new dataset
- fixed force reloading project_metadata
- fixed loading the check_results  from duckdb when resume
- add quotes to auto-completion instructions for clarity
- remove unused code
- fixed using the newly defined MAIN_DIR in get_check_results_from_session and get_schemas
- fixed the correct return object tpye (dict) of read_project_metadata_record
- filtered out those system schemas
- concurrency issue
- reduce connection delay in DuckDB connection methods
- added back to checker
- added back check_name to CheckResultJson
- added default values for datetime related fields
- fixed the SQLModel engine does not close after writing records, that halts the later read-only options by duckdb
- fixed the variable to input for check_result_list should be table_name
- fixed wrong type passing to the duckdb
- added missing docstring for sql_write_records_to_table method
- fixed using the database entry for populating `Dataset Path:`
- revert the original version of the checklist
- paths of yaml for rendering the docx
- workable version for using duckdb for storing and fetching the metadata of dataset, and return to the frontend
- upsert to the db to allow working on same dataset
- directory path for compare_files_and_metadata
- Aligned the paths using directory_manager in app.py
- no output log file
- wrongly show debug info in console
- Revamped the directory manager

### Refactor

- switch to use the attached path info in native dataverse JSON (#478)
- workable version for utilizing the checklist_metadata (#400)
- rename priority badge classes for consistency
- change some help text in the new dataset page (#380)
- uses global logging (#375)
- update README for clarity and consistency; enhance TUI instructions
- set to copy only the necessary files in docker image; updated docker ignore
- removed unused get_logger function
- removed unused dependencies and imports
- clean up string formatting and remove unused imports in app.py
- remove unused imports from directory_manager and downloads modules
- remove confirm deletion method from DirectoryManager
- change sql_write_records_to_table to sql_merge_records_to_table to merge rather than write
- added duckdb_models as an attribute to Checker class
- switched using customized context manager for read/writing to duckdb, that adds a 0.1s delay when opening it
- added self defined context manager to add a small delay when opening database
- deleted unused code (ds path) & highlighted to fix the url
- migrated using context manager for duckdb execution
- changed DB class to directory calls the duck db file, rather than the directory. This moves the control of the db file name (duckdb.db for now) to directory manager
- update headings and labels for clarity in directory settings
- rename parent_dir to main_dir across the application for consistency
