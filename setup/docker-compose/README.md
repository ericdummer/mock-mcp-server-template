# Docker Compose Setup

Use this path when you want to run the MCP server in a container without VS Code Dev Containers.

## Prerequisites

Install these first:

- Docker Engine or Docker Desktop
- Docker Compose (`docker compose`)
- Git
- Node.js (for MCP Inspector — optional but recommended for testing)

## 1) Get the repository

Clone the repository and open a terminal in the project root:

```bash
git clone <repository-url>
cd mock-mcp-server-template
```

If you already have the repository on disk, just open a terminal in the repository root.

## 2) Verify Docker is ready

Before starting the container, make sure Docker is installed and running:

```bash
docker --version
docker compose version
docker ps
```

If `docker ps` fails, start Docker and try again.

## 3) Start the service

From the repository root:

```bash
docker compose up --build
```

The first build can take a few minutes because Docker needs to build the image and install Python dependencies.

If you want to run it in the background instead:

```bash
docker compose up --build -d
```

You should see output similar to:

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## 4) Verify the server

```bash
# No auth — should return 401
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/mcp

# With auth — should return 200
curl -s --max-time 3 -X POST \
  -H "X-Api-Key: test-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}' \
  http://localhost:8000/mcp
```

## 5) Test with MCP Inspector

MCP Inspector is a browser-based tool for interactively calling tools and viewing MCP log messages. Run it on your host machine (not inside Docker):

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

## 6) Stop the service

```bash
docker compose down
```

## Useful commands

View logs:

```bash
docker compose logs -f web
```

Restart after changing application code:

```bash
docker compose restart web
```

Rebuild after changing image or dependency files:

```bash
docker compose up --build
```

Rebuild after changing any of these:

- `Dockerfile`
- `requirements.txt`
- `.dockerignore`

The `app/` directory is bind-mounted into the container, so Python code changes take effect without a rebuild.

## Optional overrides

Override the exposed port for a single run:

```bash
WEB_PORT=8001 docker compose up --build
```

Enable debug logging:

```bash
LOG_LEVEL=DEBUG docker compose up --build
```

## Running tests

This Docker image is for running the app, not the development toolchain. `requirements-dev.txt` is not installed in the runtime container.

To run tests, use either the local install path or the VS Code Dev Container path instead:

```bash
pytest tests/ -v
```

## Troubleshooting

- If the port is already in use, set a different `WEB_PORT` value.
- If container changes do not show up after a Dockerfile or dependency change, rerun `docker compose up --build`.
- If Docker commands fail, confirm Docker is running and your user has permission to use it.
- If MCP Inspector shows "Couldn't connect to MCP Proxy Server" or "Invalid URL", make sure you opened the URL with `?MCP_PROXY_AUTH_TOKEN=localdev` appended.

Back to setup index: [SETUP.md](../../SETUP.md)
Back to project overview: [README.md](../../README.md)
