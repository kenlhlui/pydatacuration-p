# Data curation script


## ⚙️Prerequisite
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
   sudo apt update && sudo apt-get install ffmpeg
   ```

## 🔐Configure Git authentication by GitHub CLI in WSL Ubuntu
To clone (download) a private repository, authentication is required. You must first create a GitHub account.
The following will use the [GitHub CLI](https://cli.github.com/) for authentication. The official Linux (incl. WSL Ubuntu) installation guide is [here](https://github.com/cli/cli/blob/trunk/docs/install_linux.md).
1. Run the following command in the WSL Ubuntu Terminal to install
   ```sh
   (type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
	&& sudo mkdir -p -m 755 /etc/apt/keyrings \
        && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& sudo apt update \
	&& sudo apt install gh -y
   ```
2. Check whether GitHub CLI (with alias `gh`) has been successfully installed.
   ```sh
   gh --version
   ```
3. To login, run
   ```sh
   gh auth login
   ```
4. Follow the prompts. Choose the following options when prompted
   ```
   1. Where do you use GitHub?  ->  GitHub.com
   2. What is your preferred protocol for Git operations on this host?  ->  HTTPS
   3. Authenticate Git with your GitHub credentials?  ->  Yes
   4. How would you like to authenticate GitHub CLI?  ->  Login with a web browser
   ```
   You should then be prompted to log in with your web browser. You will also see an 8-digit one-time code.

   Press enter to open the browser. Fill in the credentials.

   Once the web browser shows: 'Congratulations, you're all set!', you can close the browser window.

   Wait for a bit, the Terminal should eventually show `✓ Authentication complete.`
   
> [!NOTE]
> If it shows `! Failed opening a web browser`, try to type the `gh auth login` again. 
When the terminal prompts to `Press Enter to open https://github.com/login/device in your browser...`, try to press the control key (CTTL) then click on the https://github.com/login/device link, and enter the one-time code.
   
5. Lastly, you have to set the Git credentials, by running the following command.
   ```sh
   gh auth setup-git
   ```
6. You may also check the correct configuration of GitHub login by running the following command
   ```sh
   gh auth status
   ```

## 🪛Install
1. Clone the repository
   ```sh
   git clone https://github.com/kenlhlui/pydatacuration-p
   ```

2. Change to the project directory
   ```sh
   cd ./pydatacuration-p
   ```

3. Create an environment file (`.env`) and enter the `nano` editor
   ```sh
   touch .env && nano .env
   ```

4. Configure the environment (`.env`) file.
   ```sh
   BASE_URL = "TARGET_REPO_URL"  # Base URL of the repository; e.g., "https://demo.borealisdata.ca/"
   API_TOKEN = "YOUR_API_TOKEN"      # Found in your Dataverse account settings.
   ```
   Your `.env` file should look like this:
   ```sh
   BASE_URL = "https://demo.borealisdata.ca/"
   API_TOKEN = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX"
   ```
   Press control (CTRL) + S to save the file. 
   
   Once you saved the file, you should see [ Wrote 3 lines ] in the middle bottom. 
   
   Press CTRL + X to leave the editor.

5. Set up virtual environment (recommended)
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate     # For Unix/MacOS
   ```

6. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```

>[!TIP]
>If you prefer a Graphical User Interface (GUI), you can run the following command
>```sh
>explore.exe .
>```
> A Windows File Explorer should appear, and you can edit, copy, delete, or move files using the GUI.

## ℹ️Curator info
You can configure the curation project information by modifying the `res/config.yaml` file. 

You can modify it with Notepad (GUI) or nano editor (Terminal).
1. Open and edit the config.yaml file.
   ```sh
   nano res/config.yaml
   ```
2. Fill in the relevant information
   ```yaml
   ticket_number:
   curator_name:
   curator_email:
   ```

## 🏃Run the tool
You have finished the configuration. Now is time to run the tool.

1. Open a terminal, run the script with the following command
   ```sh
   python3 pydatacuration/main.py --doi $DOI  # (e.g. --doi doi:10.80240/FK2/U2VZH9)
   ```
   You may also define the working directory (the directory that stores the metadata JSON, data files, and curation log) by adding a `--workdir-input` flag following the path.

   For example, if you wish to create a `download` directory inside the `pydatacuration-p` directory:
   ```sh
   python3 pydatacuration/main.py --doi $DOI  --workdir-input 'download'
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

## 👀View the files
To view the files in Windows File Explorer, run the command below in the Terminal. The Explorer window should be prompted.
```sh
explore.exe $PATH
```
For example, if you use `--workdir-input 'download'` (same as the example above), type the following command
```sh
explore.exe download
``` 
