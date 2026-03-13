# GitHub Copilot Instructions for Mock MCP Server

This document defines coding guidance for GitHub Copilot in this project.

## Scope and Enforcement (Important)

- This file is assistant guidance, not a security control by itself.
- Engineers must enforce security through code review, branch protection, CI scanners (Trivy, secret scanning), automated tests, and runtime controls.
- Treat generated code as untrusted when it conflicts with these rules.
- Do not intentionally introduce insecure patterns (hardcoded credentials, unsafe deserialization, disabled auth) in production code paths.

## Project Structure

```
app/
├── main.py              # Starlette ASGI entry point — SSE transport setup, auth check
├── api/mcp.py           # MCP SDK handlers — registers list_tools/call_tool on the server
├── core/
│   ├── config.py        # Settings via pydantic-settings
│   └── server.py        # MCP SDK Server singleton
└── tools/
    ├── __init__.py      # Auto-discovery — framework, do not edit
    ├── _items_store.py  # Shared in-memory store (prefixed _ = not auto-discovered)
    └── *.py             # One file per tool; add/remove tools by adding/removing files
tests/                   # Async test suite using anyio + MCP in-memory transport
.devcontainer/           # Dev container: full deps (requirements.txt + requirements-dev.txt)
Dockerfile               # Production: slim, runtime deps only
```

**To add a tool:** create a new file in `app/tools/`. No other files need changing.
**To remove a tool:** delete its file from `app/tools/`.

## Running Tests

**Always run tests inside the devcontainer**, not using the production `Dockerfile`.

The devcontainer installs both `requirements.txt` and `requirements-dev.txt` and mounts the full project at `/workspaces/<repo-name>`. From a devcontainer terminal:

```bash
cd /workspaces/<repo-name>
pytest tests/ -v
```

**Do not** run tests by doing `docker compose run web pytest` — the root `docker-compose.yml` uses the production image which does not have dev dependencies or the `tests/` directory.

CI (GitHub Actions `tests.yml`) installs `requirements-dev.txt` and runs `pytest tests/` directly on the runner — no Docker needed in CI.

### Two Docker images — never confuse them

| | `.devcontainer/Dockerfile` | Root `Dockerfile` |
|---|---|---|
| Purpose | Local dev & testing | Production deployment |
| Deps | `requirements.txt` + `requirements-dev.txt` | `requirements.txt` only |
| Tests included | Yes (via volume mount at `/workspaces`) | No |
| Used by | VS Code Dev Containers | `docker-compose.yml`, CI Trivy scan |

### Diagnosing Missing Python Packages

When the application fails to start or a module is missing (`ModuleNotFoundError`):

1. Check `.devcontainer/Dockerfile` — this builds the dev container; packages are installed at image-build time.
2. Check `.devcontainer/devcontainer.json` for `postCreateCommand` and container behavior.
3. Check `.devcontainer/docker-compose.yml` and root `docker-compose.yml` for service/build/volume overrides.
4. Check `requirements.txt` and `requirements-dev.txt` — verify the missing package is declared.
5. If requirements changed after the image was built, rebuild the dev container (`Dev Containers: Rebuild Container` in VS Code).

### Docker-First Rule for Fixes

- For this repository, default to Docker/devcontainer diagnostics and fixes when startup/runtime dependency issues are reported.
- Do not recommend ad hoc `pip install` as the fix path for containerized workflows.
- Treat `pip install` as a temporary check only; persistent fixes must be made through dependency files plus image/container rebuild.

### Canonical Docker Validation Commands

Use these commands when validating runtime dependency/setup issues:

```bash
docker compose up --build
docker compose logs -f web
docker compose run --rm web python -c "import mcp; print(mcp.__file__)"
```

### Clean Docker Reset (When State Is Suspect)

If behavior seems inconsistent with current files (stale images/containers), run:

```bash
docker compose down --remove-orphans
docker compose build --no-cache web
docker compose up -d --force-recreate
```

This reset is preferred over local environment patching when troubleshooting containerized runtime issues.

### Rebuild Decision Table

| Situation | Recommended Action |
|---|---|
| You are developing in VS Code Dev Containers and changed `requirements.txt`, `requirements-dev.txt`, `.devcontainer/Dockerfile`, or `.devcontainer/devcontainer.json`. | Use `Dev Containers: Rebuild Container` in VS Code. |
| You are running the app via root `docker-compose.yml` and changed `Dockerfile` or `requirements.txt`. | Run `docker compose up --build` (or `docker compose build web && docker compose up`). |
| Python code only changed under `app/` with compose bind mount enabled. | No rebuild required; restart service if needed (`docker compose restart web`). |
| Runtime behavior seems stale or inconsistent with current files. | Run the clean reset sequence (`down --remove-orphans`, `build --no-cache`, `up --force-recreate`). |
| A package is missing inside a running container. | Update dependency files if needed, then rebuild image/container. Do not use ad hoc `pip install` as the final fix. |

## MCP SDK Architecture

This project uses the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) with an SSE transport over HTTP.

### Transport

- `POST /mcp` — client sends MCP JSON-RPC messages; server responds with JSON or SSE stream
- `GET /mcp` — client opens a long-lived SSE stream for server-initiated messages
- `DELETE /mcp` — client explicitly terminates a session

Authentication: include any non-empty value in the configured API key header on every request to `/mcp`. Missing key → HTTP 401.

### Server Singleton (`app/core/server.py`)

```python
from mcp.server import Server
server = Server("mock-mcp-server")
```

Imported by both `app/api/mcp.py` (registers handlers) and `app/main.py` (runs the ASGI app).

### Registering Handlers (`app/api/mcp.py`)

Use `@server.list_tools()` and `@server.call_tool()` decorators. The SDK calls these automatically when a client sends `tools/list` or `tools/call`.

```python
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="my_tool", description="...", inputSchema={...})]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "my_tool":
        return [TextContent(type="text", text="result")]
    raise ValueError(f"Unknown tool: {name}")
```

### MCP Protocol Logging (`send_log_message`)

Use `server.request_context.session.send_log_message()` to send log messages to the MCP client (visible in MCP Inspector's Notifications tab):

```python
ctx = server.request_context
await ctx.session.send_log_message(level="info", data="tool called", logger="my_tool")
```

Valid levels: `"debug"`, `"info"`, `"notice"`, `"warning"`, `"error"`, `"critical"`, `"alert"`, `"emergency"`.

Always wrap `send_log_message` in a try/except — if there is no active session context the call will raise.

## Tool Plugin Pattern

Each file in `app/tools/` (not prefixed with `_`) that defines `TOOL_DEFINITION` and `handle()` is automatically discovered and registered at startup.

### Minimal tool file

```python
# app/tools/my_tool.py
from __future__ import annotations
from typing import Any

TOOL_DEFINITION = {
    "name": "my_tool",
    "description": "Call this tool when the user wants to do X.",
    "inputSchema": {
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "description": "The search query."},
        },
    },
}

def handle(params: dict[str, Any]) -> dict[str, Any]:
    query = params.get("query", "")
    return {"content": [{"type": "text", "text": f"Result for: {query}"}]}
```

### Tool file conventions

- Use `params.get("key", default)` — never assume a key exists.
- Always return a `content` list with at least one `{"type": "text", "text": "..."}` entry.
- For structured responses, serialize to JSON and put in the `text` field.
- Keep mock data deterministic. Avoid random values that make tests flaky.
- Files prefixed with `_` (e.g., `_items_store.py`) are skipped by auto-discovery — use this for shared state.

### Auto-discovery mechanism

`app/tools/__init__.py` uses `pkgutil.iter_modules` + `importlib.import_module` to scan the package at startup. A module is registered if it has both `TOOL_DEFINITION` (a dict) and `handle` (a callable). Do not modify this file.

## Testing Guidelines

Tests use `pytest` with `@pytest.mark.anyio` and the MCP SDK's in-memory transport — no HTTP server needed.

### Fixture pattern (`tests/conftest.py`)

```python
import pytest
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams
from app.api.mcp import server  # registers handlers as side-effect

@pytest.fixture
async def mcp_session():
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        async with anyio.create_task_group() as tg:
            tg.start_soon(server.run, server_streams[0], server_streams[1],
                          server.create_initialization_options())
            async with ClientSession(*client_streams) as session:
                await session.initialize()
                yield session
                tg.cancel_scope.cancel()
```

### Test pattern

```python
import pytest

@pytest.mark.anyio
async def test_list_tools(mcp_session):
    result = await mcp_session.list_tools()
    names = [t.name for t in result.tools]
    assert "my_tool" in names

@pytest.mark.anyio
async def test_call_tool(mcp_session):
    result = await mcp_session.call_tool("my_tool", {"query": "test"})
    assert not result.isError
    assert result.content[0].text
```

- Use `@pytest.mark.anyio` for all async tests (provided by the `anyio` package).
- Test all error paths: unknown tool name, missing required params, denied operations.
- Write one test per tool that verifies the happy path response shape.
- Run from devcontainer terminal: `pytest tests/ -v`

## Security and Secrets Management

### Critical Rules
1. Never hardcode credentials, API keys, or secrets in source code.
2. Always use environment variables for sensitive data.
3. Never commit `.env` files — commit only `.env.example`.
4. Use `pydantic-settings` for configuration.

### Settings pattern

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Mock MCP Server"
    host: str = "0.0.0.0"
    port: int = 8000
    api_key_header: str = "X-Api-Key"
    log_level: str = "INFO"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- Keep secrets in `.env` (gitignored).
- Provide `.env.example` with dummy/default values.
- Document all env vars in `README.md`.

## Code Quality Standards

- Use type hints on all function parameters and return types.
- Add `from __future__ import annotations` to files using `X | Y` union syntax.
- Keep docstrings on public functions and classes.

### Ruff Formatting (Required)

- Format all Python code with `ruff format` standards.
- After applying code changes, run `ruff format` on changed files and `ruff check --fix`.
- Do not introduce formatting that conflicts with `pyproject.toml`.

## Docker Practices

- **Production `Dockerfile`**: multi-stage, slim runtime image, no dev deps, no test files.
- **`.devcontainer/Dockerfile`**: dev image with Node.js, full Python deps (runtime + dev), used only for local development.
- Run as non-root user (`appuser`) in both images.
- Use `env_file` in compose files; never hardcode env vars.

## Git and Version Control

### Do Not Commit
- `.env` files
- `__pycache__`
- credentials or secrets

### Do Commit
- `.env.example` with dummy values
- `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`
- source code, tests, documentation

## Summary Checklist

When generating code for this project:
1. **New tools go in `app/tools/`** — one file per tool, `TOOL_DEFINITION` + `handle()`, no other files change.
2. Use the MCP SDK patterns — `@server.list_tools()`, `@server.call_tool()`, `send_log_message`.
3. Never hardcode secrets; use environment variables via `pydantic-settings`.
4. Add `from __future__ import annotations` to files using `X | Y` union syntax.
5. **Run tests in the devcontainer**: `pytest tests/ -v` from `/workspaces/<repo-name>`.
6. After applying changes, run `ruff format` and `ruff check --fix` on changed Python files.
7. Keep code typed, tested, and documented.
8. Follow secure Docker and CI practices — production image stays slim.

