# Local Install Setup

Use this path when you want to run everything directly on your machine (without Docker).

## Prerequisites

Install these first:

- Python 3.11+
- Node.js (for MCP Inspector — optional but recommended for testing)
- Git

## 1) Get the repository

Clone the repository and open a terminal in the project root:

```bash
git clone <repository-url>
cd mock-mcp-server-template
```

If you already have the repository on disk, just open a terminal in the repository root.

## 2) Verify Python

Check that Python 3.11 or newer is available:

```bash
python --version
python -m pip --version
```

If `python` points to an older version on your machine, use the correct interpreter explicitly, for example `python3.11`.

## 3) Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate
```

Using a virtual environment avoids conflicts with system Python packages.

## 4) Install dependencies

For local development and tests:

```bash
python -m pip install -r requirements-dev.txt
```

For runtime only (no test tools):

```bash
python -m pip install -r requirements.txt
```

## 5) Configure environment variables (optional)

Copy `.env.example` to `.env` and adjust as needed. All variables have defaults, so this step is only required if you want to override them:

```bash
cp .env.example .env
```

## 6) Start the server

From the repository root:

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

## 7) Verify the server

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

## 8) Test with MCP Inspector

MCP Inspector is a browser-based tool for interactively calling tools and viewing MCP log messages.

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

## Run tests

```bash
pytest tests/ -v
```

## Reinstall dependencies when requirements change

If `requirements.txt` or `requirements-dev.txt` changes, rerun:

```bash
python -m pip install -r requirements-dev.txt
```

## Troubleshooting

- If `python -m app.main` fails with missing packages, reinstall dependencies.
- If `python --version` is not Python 3.11+, use the correct interpreter explicitly.
- If `pytest` is not found, install the development dependencies from `requirements-dev.txt`.
- If MCP Inspector shows "Couldn't connect to MCP Proxy Server" or "Invalid URL", make sure you opened the URL with `?MCP_PROXY_AUTH_TOKEN=localdev` appended.

Back to setup index: [SETUP.md](../../SETUP.md)
Back to project overview: [README.md](../../README.md)
