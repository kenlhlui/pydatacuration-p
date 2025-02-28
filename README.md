# Data curation script

The demo branch for 2024-10-31 meeting

## Steps to run the script
1. Clone the repository
   ```sh
   git clone https://github.com/scholarsportal/dataverse-metadata-crawler.git
   ```

2. Change to the project directory
   ```sh
   cd ./dataverse-metadata-crawler
   ```

3. Create an environment file (`.env`)
   ```sh
   touch .env  # For Unix/MacOS
   nano .env   # or vim .env, or your preferred editor
   # OR
   New-Item .env -Type File   # For Windows (Powershell)
   notepad .env
   ```

4. Configure the environment (`.env`) file using the text editor of your choice.
   ```sh
   # .env file
   BASE_URL = "TARGET_REPO_URL"  # Base URL of the repository; e.g., "https://demo.borealisdata.ca/"
   API_TOKEN = "YOUR_API_TOKEN"      # Found in your Dataverse account settings. Can also be specified in the CLI interface using the -a flag.
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
   # OR
   .venv\Scripts\activate       # For Windows
   ```

6. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```

7. Open a terminal, run the script with the following command
   ```bash
   python pydatacuration/main.py --doi $DOI  # (e.g. --doi doi:10.80240/FK2/U2VZH9)
   ```