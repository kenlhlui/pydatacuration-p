# Data curation script


## Prerequisite
1. [Linux on Windows with WSL (Ubuntu)](https://learn.microsoft.com/en-us/windows/wsl/setup/environment)
   1. Run the following command in a Windows Powershell Terminal (with administrative access). You might need to restart your computer once the execution is finished.
      ```powershell
      Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
      ```
      You should see a prompt output like this:
      ```powershell
      Path          :
      Online        : True
      RestartNeeded : False
      ```
   2. Run the following command in a Windows Powershell Terminal (with administrative access). This will install the latest WSL Ubuntu version (24.04 LTS)
      ```powershell
      wsl --install
      ```
   3. Run the following command once the `Distribution successfully installed. It can be launched via 'wsl.exe -d Ubuntu` prompt appears
      ```powershell
      wsl.exe -d Ubuntu
      ```
   4. You should be directed to configure the default user name and password. It does not have to be the same with your windows one.
   
      You should see the following prompt configure the name of the default user account. Enter the user name you like.
      ```sh
      Create a default Unix user account:  # Input your user name here
      ```
      You will then see a prompt configuring the password for the account:
      ```sh
      New password:
      Retype new password:
      ```
      Once you have finished the initial configuration process, you should see the following prompt in the terminal:
      ```sh
      Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 5.15.167.4-microsoft-standard-WSL2 x86_64)

      * Documentation:  https://help.ubuntu.com
      * Management:     https://landscape.canonical.com
      * Support:        https://ubuntu.com/pro
      ...
      ```

   5. To re-enter the WSL Ubuntu environment, simply open a Terminal and type `wsl.exe -d Ubuntu`. You may also consider installing the [Windows Terminal app](https://learn.microsoft.com/en-us/windows/terminal/) for better user experience.
2. [Git](https://git-scm.com/)
> [!NOTE]
> WSL Ubuntu should by default comes with Git. 
> Type `git --version` to check.
> Or run `sudo apt update && sudo apt install git` to install.
   
3. [Python3.10^](https://www.python.org/downloads/release/python-3100/)
> [!NOTE]
> WSL Ubuntu should by default comes with Python3.12.
> Type `python3 --version` to check.
4. [FFmpeg](https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu)
   1. Run the following command to install FFmpeg. You will be prompted to ask for your password and confirmation.
   ```sh
   sudo apt update && sudo apt-get install ffmpeg.
   ```


## Steps to run the script
1. Clone the repository
   ```sh
   git clone https://github.com/kenlhlui/pydatacuration-p
   ```

2. Change to the project directory
   ```sh
   cd ./pydatacuration-p
   ```

3. Create an environment file (`.env`)
   ```sh
   touch .env  # For Unix
   nano .env   # or vim .env, or your preferred editor
   ```

4. Configure the environment (`.env`) file using the text editor of your choice.
   ```sh
   # .env file
   BASE_URL = "TARGET_REPO_URL"  # Base URL of the repository; e.g., "https://demo.borealisdata.ca/"
   API_TOKEN = "YOUR_API_TOKEN"      # Found in your Dataverse account settings.
   ```
   Your `.env` file should look like this:
   ```sh
   BASE_URL = "https://demo.borealisdata.ca/"
   API_TOKEN = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX"
   ```

5. Set up virtual environment (recommended)
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate     # For Unix/MacOS
   ```

6. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```

7. Open a terminal, run the script with the following command
   ```sh
   python3 pydatacuration/main.py --doi $DOI  # (e.g. --doi doi:10.80240/FK2/U2VZH9)
   ```
   You may also define the working directory (directory that stores the metadata JSON, data files, and curation log) by adding a `--workdir` flag following with the path.

   For example, if you wish to create a `download` directory inside the `pydatacuration-p` directory:
   ```sh
   python3 pydatacuration/main.py --doi $DOI  --workdir 'download'
   ```
   What you will get:
   ```sh
   .
   ├── README.md
   ├── config.yaml
   ├── download  # The metadata JSON file, data files, and curation log.
   ├── poetry.lock
   ├── pydatacuration
   ├── pyproject.toml
   ├── requirements.txt
   ├── res
   ```