# Data Curation Tool

A containerized data curation tool for Dataverse repositories with web interface support.

<img src="docs/full-tool-demo.gif" alt="The full curation tool demo" width="70%" height="70%">

## 🚀 Quick Start with Docker🐋/Podman🦭 (Recommended)

### Prerequisites
- **Docker** and **Docker Compose** installed
  - 👉 [Get Docker](https://www.docker.com/get-started)
  - Note: Docker Desktop includes Docker Compose by default
- **Alternative**: **Podman** and **podman-compose**
  - 👉 [Installation instructions](https://github.com/containers/podman-compose)

### ⚙️ Setup & Run
Refer to the [Container Guide](docs/container/README.md) for detailed setup instructions.


> [!NOTE]
> Or if you have just installed, then you can simply run:
> ```sh
> just docker-build-and-run -f # The -f flag skips the confirmation prompt for removing existing './workdir'
> ```

### 🏗️ Development Mode
For development with rebuild and reloading the container, run:
```sh
docker compose down && docker compose build && docker compose up
```