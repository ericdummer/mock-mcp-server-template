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

## 4) Configure environment variables

Copy `.env.example` to `.env` inside the container terminal:

```bash
cp .env.example .env
```

All variables have safe defaults so this step is optional unless you need to override them.

## 5) Start the server inside the container

Open a terminal in VS Code (inside the container) at the repository root and run:

```bash
python -m app.main
```

You should see output similar to:

```
INFO:     Started server process [1234]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The server listens on port 8000, which VS Code forwards to your host machine.

## 6) Verify the server

From a terminal on your host machine (not inside the container):

```bash
# No auth — should return 401
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/mcp

# With auth — should return 200 (may stream or return JSON)
curl -s --max-time 3 -X POST \
  -H "X-Api-Key: test-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}' \
  http://localhost:8000/mcp
```

## 7) Test with MCP Inspector

MCP Inspector is a browser-based tool for interactively calling tools and viewing MCP log messages. Run it from your **host machine** (not inside the container):

```bash
MCP_PROXY_AUTH_TOKEN=localdev npx @modelcontextprotocol/inspector
```

Setting a fixed `MCP_PROXY_AUTH_TOKEN` lets you bookmark the URL. Open this URL in your browser:

```
http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=localdev
```

> ⚠️ Do not navigate to `http://localhost:6274` without the token — the Inspector UI will fail to connect to its own proxy and show "Invalid URL" errors.

In the Inspector UI:

1. Set **Transport** to `Streamable HTTP`.
2. Set **URL** to `http://localhost:8000/mcp`.
3. Under **Headers**, add: `X-Api-Key` = `test-key`.
4. Click **Connect**.

You should see the connection succeed and the **Tools** tab populate with the available tools.

## Run tests

From inside the container terminal (the devcontainer has all dev dependencies):

```bash
pytest tests/ -v
```

## When to rebuild the container

Rebuild the container after changing any of these:

- `.devcontainer/devcontainer.json`
- `.devcontainer/Dockerfile`
- `.devcontainer/docker-compose.yml`
- `requirements.txt`
- `requirements-dev.txt`

Use: `Dev Containers: Rebuild Container` in the VS Code Command Palette.

## Troubleshooting

- If `python -m app.main` fails because a dependency is missing, rebuild the container.
- If Dev Container configuration changes do not take effect, rebuild the container.
- If VS Code cannot reopen in the container, confirm Docker is running and the Dev Containers extension is installed.
- If MCP Inspector shows "Couldn't connect to MCP Proxy Server" or "Invalid URL", make sure you opened the URL with `?MCP_PROXY_AUTH_TOKEN=localdev` appended.

## Notes

- This setup uses the repository's Dev Container configuration under `.devcontainer/`.
- Container-specific reference details are in [.devcontainer/README.md](../../.devcontainer/README.md).

Back to setup index: [SETUP.md](../../SETUP.md)
Back to project overview: [README.md](../../README.md)
