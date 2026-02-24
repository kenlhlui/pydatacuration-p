# To use the Command Line Interface (CLI)

## Options
| Option                 | Argument | Description                                                                      |
| ---------------------- | -------- | -------------------------------------------------------------------------------- |
| `--main-dir`           | PATH     | Top-level working directory for all runs                                         |
| `--install-completion` | –        | Install completion for the current shell.                                        |
| `--show-completion`    | –        | Show completion for the current shell, to copy it or customize the installation. |
| `--help`               | –        | Show this message and exit.                                                      |




## Commands
| Command  | Description                                                                          |
| -------- | ------------------------------------------------------------------------------------ |
| `all`    | Run the full pipeline: init ➜ fetch ➜ check ➜ report.                                |
| `check`  | Run curation checks on downloaded files/metadata.                                    |
| `fetch`  | Download dataset files and metadata.                                                 |
| `init`   | Prepare working directory and Database schema.                                         |
| `report` | Generate artifacts (tree diagram, spreadsheets/docs) and optionally open the folder. |
| `tui`    | Open Textual TUI.                                                                    |


## Usage
```sh
python -m pydatacuration.main [command] [OPTIONS]
```

## Step by step tutorial
1. After activating the Python environment (you’ll see (.venv) at the start of your prompt) in the terminal, run the following command with the relevant information. 

    The command `all` is used to run the full pipeline: init ➜ fetch ➜ check ➜ report, as shown below:


    ```sh
    python -m pydatacuration.main all [OPTIONS]
    ```
    ### Options

    | Option(s)                                    | Argument | Description                                                                                                   |
    | -------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------- |
    | `--pid`, `-p`                                | TEXT     | Dataset Persistent Identifier. **Required**.                                                                  |
    | `--base-url`, `-b`                           | TEXT     | The base URL of the Dataverse installation.<br/>Env var: `BASE_URL`. Default: `https://demo.borealisdata.ca/` |
    | `--api-token`, `-a`                          | TEXT     | The API token for the Dataverse installation.<br/>Env var: `ba4d1dd5-904f-49fe-9a7c-e24e2f27cf45`.            |
    | `--ticket-number`, `-t`                      | TEXT     | Ticket number (also used as schema and folder name). **Required**.                                            |
    | `--force-del`, `-f`, `--no-force-del`, `-nf` | –        | Delete existing working directory and DB schema if present. Default: `no-force-del`.                          |
    | `--check-zip`, `-z`, `--no-check-zip`, `-nz` | –        | Unzip archives and inspect their contents. Default: `check-zip`.                                              |
    | `--collection-alias`, `-c`                   | TEXT     | Alias of Dataverse collection to search for the datasets' author history.                                     |
    | `--curator-name`, `-cn`                      | TEXT     | Curator name. Default: `Ken Lui`.                                                                             |
    | `--curator-email`, `-ce`                     | TEXT     | Curator email. Default: `kenlh.lui@utoronto.ca`.                                                              |
    | `--open-dir`, `--no-open-dir`                | –        | Open working directory in Windows Explorer after the run is finished (WSL compatible only). Default: `open-dir`.                                |
    | `--help`                                     | –        | Show this message and exit.                                                                                   |

    Example with specific values:
    
    ```sh
    python -m pydatacuration.main all \
    -p doi:10.80240/FK2/W4P2FH \
    -t CUR-001 \
    -c toronto
    ```

    In this example:

    `doi:10.80240/FK2/W4P2FH` → Dataset Persistent Identifier

    `CUR-001` → Ticket/Project number (folder will also be named CUR-001)

    `toronto` → Collection alias (`toronto` as [U of T Dataverse](https://borealisdata.ca/dataverse/toronto)) to narrow the author search