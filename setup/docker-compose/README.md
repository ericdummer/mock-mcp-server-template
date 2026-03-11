# Docker Compose Setup

Use this path when you want to run the MCP server in a container.

## Prerequisites

Install these first:

- Docker Engine or Docker Desktop
- Docker Compose (`docker compose`)
- Git

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

## 4) Verify the server

Send a test request to the MCP endpoint:

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-Goog-Api-Key: test-key" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m json.tool
```

## 5) Stop the service

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

You should rebuild after changing any of these:

- `Dockerfile`
- `requirements.txt`
- `.dockerignore`

The application source under `app/` is bind-mounted into the container, so Python code changes usually do not require a rebuild.

## Optional overrides

The Compose setup uses defaults from `.env.example`.

You can override the exposed port for a single run:

```bash
WEB_PORT=8001 docker compose up --build
```

You can also enable debug mode for a single run:

```bash
DEBUG=true docker compose up --build
```

## Running tests

This Docker image is for running the app, not the development toolchain. The `tests/` directory is excluded from the image build and `requirements-dev.txt` is not installed in the runtime container.

If you want to run tests, use either the local install path or the VS Code Dev Container path instead:

```bash
pytest
```

## Troubleshooting

- If the port is already in use, set a different `WEB_PORT` value.
- If container changes do not show up after a Dockerfile or dependency change, rerun `docker compose up --build`.
- If Docker commands fail, confirm Docker is running and your user has permission to use it.

Back to setup index: [SETUP.md](../../SETUP.md)
Back to project overview: [README.md](../../README.md)
