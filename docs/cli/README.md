# To use the Command Line Interface (CLI)

## Options
| Option                          | Alias(s)       | Type  | Default       | Required | Details                                                                                                                    |
|---------------------------------|----------------|-------|---------------|----------|----------------------------------------------------------------------------------------------------------------------------|
| `--pid`                         | `-p`           | TEXT  | None          | Yes      | Enter the Persistent Identifier of the dataset.                                                                          |
| `--base-url`                    | `-b`           | TEXT  | None          | No       | The base URL of the Dataverse installation (current value: `https://demo.borealisdata.ca/`). [Env var: BASE_URL]             |
| `--api-token`                   | `-a`           | TEXT  | None          | No       | The API token for the Dataverse installation (current: Set). [Env var: API_TOKEN]                                           |
| `--parent-dir`                  | `-dir`         | TEXT  | workdir       | No       | The working directory. If not specified, a directory named "workdir" will be created in the current directory.              |
| `--ticket-number`               | `-t`           | TEXT  | None          | Yes      | The ticket number for the curation report; also the directory name created under the working directory.                    |
| `--force-del` / `--no-force-del` | `-f` / `-nf`   | FLAG  | no-force-del  | No       | Force replace (delete) an existing working directory, if any.                                                             |
| `--help`                        |                | FLAG  | N/A           | No       | Show this message and exit.                                                                                               |

## Usage
```sh
python -m pydatacuration.main cli [OPTIONS]
```

## Step by step tutorial
1. After activating the Python environment (you’ll see (.venv) at the start of your prompt), run the following command with the relevant information. 

    The required options are `--pid` (`-p`) and `--ticket-number` (`-t`).
    ```sh
    python -m pydatacuration.main cli -p $pid -t $ticket-number
    ```

    For example if the dataset persistent identifier is `doi:10.80240/FK2/W4P2FH`, and the ticket/project number (this will also be the project folder name) is `CUR-001`, then your command will be

    ```sh
    python -m pydatacuration.main cli -p doi:10.80240/FK2/W4P2FH -t CUR-001
    ```