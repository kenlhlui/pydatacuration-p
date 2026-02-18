# Introduction

> [!WARNING]  
> This is a modified version of the official Dataverse compose file, and is intended for testing purposes only. IT IS NOT FOR PRODUCTION USE.

This folder contains the modified compose file for running a local Dataverse instance for testing purposes. It is based on the official Dataverse compose file, but with some modifications to make it work with our setup.

The official guide is available at: https://borealisdata.ca/guides/en/latest/container/index.html

The latest version of the compose file is available at: https://github.com/IQSS/dataverse/blob/develop/docker/compose/demo/compose.yml


# Modifications
postgres:
- container_name is changed to postgres_dataverse
- ports are changed to 5433:5432 to avoid conflicts with any existing PostgreSQL instances on the host machine

# Usage
## Just
If you have Just installed, you can simply run the following command to start the Dataverse instance:

```bash
just start-dataverse
```

To stop the Dataverse instance, you can run:

```bash
just stop-dataverse
```

To run a development build for testing with sample dataset ('Test dataset for curation service'):

```bash
just stop-dataverse && just start-dataverse && just publish
```