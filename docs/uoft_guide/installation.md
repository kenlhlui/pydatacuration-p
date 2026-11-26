---
title: Install on Windows
description: Instructions for installing the U of T Dataverse Curation Tool on Windows
---

Installation instructions
===

To install the U of T Dataverse Curation Tool on a Windows local machine, follow the steps below. For other systems, or for more detail on each setting, see [Local setup (uv)](../local_setup/README.md).

## Prerequisites

1. [Git](https://git-scm.com/)
2. [uv](https://docs.astral.sh/uv/)
3. [VS Code](https://code.visualstudio.com/)
4. [FFmpeg](https://ffmpeg.org/), which the tool uses to check that audio and video files open. You can install it in PowerShell with:
   ```powershell
   winget install ffmpeg
   ```

## Steps

1. Install the prerequisites if you haven't already, from the links above.
2. Clone the repository to your local machine in a PowerShell terminal:
   ```powershell
   git clone https://github.com/kenlhlui/pydatacuration-p.git
   ```
3. Navigate to the cloned repository:
   ```powershell
   cd pydatacuration-p
   ```
4. Switch to the latest release of the tool:
   ```powershell
   git fetch --tags; git switch --detach (git describe --tags --abbrev=0 origin/main)
   ```
   Git may show a message about being in a 'detached HEAD' state. This is expected: the tool is on a release rather than a branch.
5. Make a directory called `workdir` for the tool to use as a workspace:
   ```powershell
   New-Item -ItemType Directory -Name workdir
   ```
6. Install the required dependencies using uv:
   ```powershell
   uv sync
   ```
7. Open the project in VS Code and create a `.env` file in the root directory. Its values prefill the new dataset form:
   ```dotenv
   BASE_URL=https://borealisdata.ca/
   CURATOR_NAME="YOUR NAME"
   CURATOR_EMAIL=YOUR_EMAIL
   # The alias for the U of T Dataverse collection on Borealis
   COLLECTION_ALIAS=toronto
   # API_TOKEN=YOUR_API_TOKEN
   ```
      - Put quotes around values that contain spaces, like `CURATOR_NAME` above.
      - `API_TOKEN` is optional. Leave it out to paste the token into the form instead.
      - See [App settings](../app_settings/README.md) for the other variables you can set.
8. Run the application using uv:
   ```powershell
   uv run --env-file .env app.py
   ```

## Access the tool

You should be able to access the tool at <http://localhost:9005> in your web browser.

## Close the application

To close the application, press `Ctrl + C` in the PowerShell terminal.

!!! danger "API Token security tip"

    A best security practice is to revoke the API Token in Borealis after you are done using the tool. You can generate a new API token for the next time you use the tool.

## Next steps

To start the tool again later, see [Restart the tool](./restart.md). To review a dataset, see [Review a dataset](./review_dataset.md).
