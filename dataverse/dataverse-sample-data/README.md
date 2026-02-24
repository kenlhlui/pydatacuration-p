# Dataverse Sample Data

Populate your Dataverse installation with sample data.

The folder is adapted from  https://github.com/IQSS/dataverse-sample-data.

# Overview

Copy dvconfig.py.sample to dvconfig.py (see the cp command below) and add your API token (using your favorite text editor, which may not be vi as shown below). Note that the config file specifies which sample data will be created.

```bash
cp dvconfig.py.sample dvconfig.py
vi dvconfig.py
```

The run the create_dataverse.py to create a dataverse collection ('University of Toronto'), under the root collection.

Lastly, run the create_dataset.py to create a dataset.


# Usage
If you have just installed, you can simply run the following command to create the dataverse collection and dataset:

Create 'University of Toronto' dataverse collection:
```bash
just publish-sample-dataverse
```

Create 'Test dataset for curation service' dataset under 'University of Toronto' dataverse collection:
```bash
just publish-sample-dataset
```

To do both at the same time:
```bash
just publish
```