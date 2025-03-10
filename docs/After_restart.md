# After restart

1. Open 'Terminal' and swtich to the 'Ubuntu'

<img src="img/01_open-terminal.gif" width="50%" height="50%">

2. Run `cd pydatacuration-p` to change directory to 'pydatacuration-p'

<img src="img/02_cd.gif" width="50%" height="50%">

3. Run `source .venv/bin/activate` to enter the virtual enviroment

<img src="img/03_source-venv.gif" width="50%" height="50%">

4. Run `nano res/config.yaml` to configure the Curator Info, inside the terminal

<img src="img/04_change_config.gif" width="50%" height="50%">

5. Run the following command to download start the automated curated data. Replace the `$doi` with the actual doi.
   ```sh
   python3 pydatacuration/main.py --doi $DOI  # (e.g. --doi doi:10.80240/FK2/U2VZH9)
   ```

For example:
   ```sh
   python3 pydatacuration/main.py --doi doi:10.80240/FH2/U2VCH9
   ```