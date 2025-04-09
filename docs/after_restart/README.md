# After restart


1. Open 'Terminal' and switch to the 'Ubuntu'


   <img src="01_open-terminal.gif" width="70%" height="70%">


2. Run the following script to initialize the python environment for running the tool, and to update the tool.

   If successful, you should see `✅Successfully configured the python environment` printed out in the terminal.
   ```sh
   cd pydatacuration-p || { echo "❌Failed to navigate to pydatacuration-p directory."; return || exit; }
   source .venv/bin/activate || { echo "❌Failed to activate virtual environment."; return || exit; }
   git pull origin main --quiet || { echo "Failed to pull from origin main."; return || exit; }
   pip install -r requirements.txt -qq || { echo "Failed to pull from origin main."; return || exit; }
   printf "\n ✅Successfully configured the python environment \n"
   ```

   <img src="02_config.gif" width="70%" height="70%">


3. Run `nano res/config.yaml` to configure the Curator Info, inside the terminal. You may skip this if you have done before and no changes needed.


   <img src="03_change_config.gif" width="70%" height="70%">

4. See the following guide to learn how to use the tool in TUI or CLI
   
   - [TUI](/docs/tui/README.md)
   
   - [CLI](/docs/cli/README.md)