CREATE TABLE project_metadata (
	project_number VARCHAR NOT NULL,
	curator_name VARCHAR NOT NULL,
	curator_email VARCHAR NOT NULL,
	dataset_title VARCHAR NOT NULL,
	dataset_pid VARCHAR NOT NULL,
	dataset_id INTEGER NOT NULL,
	datasetid INTEGER NOT NULL,
	dataset_url VARCHAR NOT NULL,
	dataset_path VARCHAR,
	checklist_type VARCHAR NOT NULL,
	log_init_date DATE DEFAULT CAST(timezone('UTC', now()) AS DATE) NOT NULL,
	log_last_update_date DATE NOT NULL,
	last_modified_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (project_number),
	UNIQUE (project_number)
);

CREATE TABLE schema_version (
	version INTEGER NOT NULL,
	PRIMARY KEY (version)
);

CREATE TABLE check_results (
	project_number VARCHAR NOT NULL,
	check_name VARCHAR NOT NULL,
	check_id VARCHAR NOT NULL,
	description VARCHAR NOT NULL,
	unit VARCHAR NOT NULL,
	results JSONB NOT NULL,
	last_modified_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (project_number, check_id),
	FOREIGN KEY(project_number) REFERENCES project_metadata (project_number)
);

CREATE TABLE checklist (
	project_number VARCHAR NOT NULL,
	id VARCHAR NOT NULL,
	action VARCHAR,
	instructions VARCHAR,
	priority VARCHAR,
	section VARCHAR,
	automated_check_ids JSONB,
	tool_explanation VARCHAR,
	curator_check_item VARCHAR,
	check_type VARCHAR,
	status VARCHAR,
	comments VARCHAR,
	time_spent INTERVAL,
	last_modified_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (project_number, id),
	FOREIGN KEY(project_number) REFERENCES project_metadata (project_number)
);

CREATE TABLE checklist_metadata (
	project_number VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	version VARCHAR NOT NULL,
	description VARCHAR,
	created_by JSONB NOT NULL,
	last_updated DATE NOT NULL,
	status VARCHAR NOT NULL,
	PRIMARY KEY (project_number, name),
	FOREIGN KEY(project_number) REFERENCES project_metadata (project_number)
);
