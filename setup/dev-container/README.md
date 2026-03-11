# VS Code Dev Container Setup

Use this path when you want an isolated development environment managed by VS Code.

## Prerequisites

Install these first:

- Docker Engine or Docker Desktop
- Visual Studio Code
- `Dev Containers` extension (`ms-vscode-remote.remote-containers`)
- Git

## 1) Get the repository

Clone the repository and open it in VS Code:

```bash
git clone <repository-url>
cd mock-mcp-server-template
code .
```

If you already have the repository on disk, just open the folder in VS Code.

## 2) Verify Docker is ready

Before opening the dev container, make sure Docker is installed and running:

```bash
docker --version
docker compose version
docker ps
```

If `docker ps` fails, start Docker and try again.

## 3) Open in the dev container

In VS Code:

1. Open the Command Palette.
2. Run `Dev Containers: Reopen in Container`.
3. Wait for the initial build and startup to finish.

The first build can take a few minutes because the image installs Python dependencies and IDE tooling.

## 4) Start the server inside the container

Open a terminal in VS Code at the repository root and run:

```bash
python -m app.main
```

You should see output similar to:

```text
INFO MCP server listening on http://0.0.0.0:8000/mcp
```

You can also use the `MCP Server: Run` launch configuration in the VS Code debugger.

## 5) Verify the server

From another terminal on the host machine or from inside the container:

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-Goog-Api-Key: test-key" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m json.tool
```

## Run tests

From inside the container terminal:

```bash
pytest
```

## When to rebuild the container

Rebuild the container after changing any of these:

- `.devcontainer/devcontainer.json`
- `.devcontainer/Dockerfile`
- `.devcontainer/docker-compose.yml`
- `requirements.txt`
- `requirements-dev.txt`

Use:

- `Dev Containers: Rebuild Container`

## Troubleshooting

- If `python -m app.main` fails because a dependency is missing, rebuild the container.
- If Dev Container configuration changes do not take effect, rebuild the container.
- If VS Code cannot reopen in the container, confirm Docker is running and the Dev Containers extension is installed.

## Notes

- This setup uses the repository's Dev Container configuration under `.devcontainer/`.
- Container-specific reference details are in [.devcontainer/README.md](../../.devcontainer/README.md).

Back to setup index: [SETUP.md](../../SETUP.md)
Back to project overview: [README.md](../../README.md)
