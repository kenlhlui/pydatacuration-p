# Introduction
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


## Getting the API token

After starting the dataverse instance, to get the api token, you can run the following command:

```bash
docker exec postgres_dataverse psql -U dataverse -t -A -c "SELECT t.tokenstring FROM apitoken t JOIN authenticateduser u ON t.authenticateduser_id = u.id WHERE u.superuser = true LIMIT 1;"
```
It will get the api token for the superuser, which can be used for testing purposes.

To verify the api token is working,

```
curl -s "http://localhost:8080/api/users/:me" -H "X-Dataverse-key: f59f5dff-fc4c-422c-9302-76f80dbbe9ef"
```