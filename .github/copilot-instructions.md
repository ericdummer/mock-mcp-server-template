# GitHub Copilot Instructions for Mock MCP Server

This document defines coding guidance for GitHub Copilot in this project.

## Scope and Enforcement (Important)

- This file is assistant guidance, not a security control by itself.
- It is not a workaround to bypass secure engineering practices.
- Engineers must enforce security through:
  - code review,
  - branch protection,
  - CI scanners (Trivy, secret scanning, dependency checks),
  - automated tests,
  - runtime/environment controls.
- Treat generated code as untrusted when it conflicts with these rules.
- Do not intentionally introduce insecure patterns (hardcoded credentials, unsafe deserialization, disabled auth) in production code paths.

## Project Structure

Follow the standard layout:

```
app/
├── api/          # MCP handler and mock data builders
├── core/         # Core functionality (config, etc.)
├── models/       # Pydantic models for MCP protocol
└── main.py       # HTTP server entry point
```

## MCP Protocol Standards

This project implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) over HTTP using JSON-RPC 2.0.

### JSON-RPC 2.0 Envelope

Every request and response must include `"jsonrpc": "2.0"`. Always echo the request `id` back in the response.

```python
# Request shape
{
    "jsonrpc": "2.0",
    "id": 1,           # int, str, or null — always echo back
    "method": "tools/list",
    "params": {}       # optional
}

# Success response
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": { ... },
    "error": None
}

# Error response
{
    "jsonrpc": "2.0",
    "id": 1,           # use null if id was not parseable
    "result": None,
    "error": { "code": -32601, "message": "Method not found: foo" }
}
```

### Standard JSON-RPC Error Codes

Always use the correct code. Do not return HTTP 4xx/5xx for protocol-level errors — return HTTP 200 with a JSON-RPC error body.

| Code | Constant | Meaning |
|------|----------|---------|
| `-32700` | `_PARSE_ERROR` | Body could not be parsed as JSON |
| `-32600` | `_INVALID_REQUEST` | Valid JSON but not a valid JSON-RPC envelope |
| `-32601` | `_METHOD_NOT_FOUND` | Method not recognised |
| `-32602` | `_INVALID_PARAMS` | Missing or invalid parameters for a known method |
| `-32603` | `_INTERNAL_ERROR` | Unexpected server-side error |
| `-32000` | `_UNAUTHENTICATED` | Missing or invalid API key (app-level) |

### MCP Methods

Implement exactly the methods your server advertises. The two core methods are:

- **`tools/list`** — returns a list of `ToolDefinition` objects (no params required).
- **`tools/call`** — dispatches to a named tool; params must include `name` and `arguments`.

```python
def handle_mcp_request(body: bytes, api_key: str | None) -> JsonRpcResponse:
    if not api_key:
        return _err(None, _UNAUTHENTICATED, "Missing X-Goog-Api-Key header")

    try:
        body_dict = json.loads(body)
    except Exception:
        return _err(None, _PARSE_ERROR, "Could not parse JSON body")

    try:
        rpc_req = JsonRpcRequest(**body_dict)
    except (ValidationError, TypeError) as exc:
        return _err(None, _INVALID_REQUEST, f"Invalid JSON-RPC request: {exc}")

    try:
        if rpc_req.method == "tools/list":
            result = _handle_tools_list()
        elif rpc_req.method == "tools/call":
            if not rpc_req.params:
                return _err(rpc_req.id, _INVALID_PARAMS, "Missing params for tools/call")
            result = _handle_tools_call(rpc_req.params)
        else:
            return _err(rpc_req.id, _METHOD_NOT_FOUND, f"Method not found: {rpc_req.method}")
    except (ValidationError, TypeError) as exc:
        return _err(rpc_req.id, _INVALID_PARAMS, f"Invalid parameters: {exc}")
    except ValueError as exc:
        return _err(rpc_req.id, _INVALID_PARAMS, str(exc))
    except Exception as exc:
        return _err(rpc_req.id, _INTERNAL_ERROR, f"Internal error: {exc}")

    return _ok(rpc_req.id, result)
```

### Tool Definitions

Every tool must declare `name`, `description`, and `inputSchema` (JSON Schema object).

```python
ToolDefinition(
    name="my_tool",
    description=(
        "Call this tool when the user wants to do X. "
        "Be specific so the LLM knows when to use it."
    ),
    inputSchema={
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            },
        },
    },
)
```

- `description` should clearly state **when** to call the tool, not just what it does.
- `inputSchema` must be a valid JSON Schema. Mark truly required fields in `"required"`.
- Return a `content` array with at least one `{"type": "text", "text": "..."}` entry.

### Tool Response Shape

```python
# tools/call result
{
    "content": [{"type": "text", "text": "<human-readable summary>"}],
    "result": { ... }   # structured data for programmatic use
}
```

## HTTP Server

This project uses Python's stdlib `http.server`. Keep the handler thin — delegate all business logic to `handle_mcp_request`.

```python
class MCPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path == "/mcp":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""
            api_key = self.headers.get("X-Goog-Api-Key")
            response = handle_mcp_request(body, api_key)
            response_bytes = response.model_dump_json().encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        logger.debug(format, *args)
```

- Always respond HTTP 200 for any request that reaches the MCP handler (errors go in the JSON-RPC body).
- Only respond with HTTP 404 for unknown paths.
- Suppress `BaseHTTPRequestHandler`'s default stdout logging; use Python `logging` instead.

## Schemas and Validation

- Use Pydantic models for all request/response validation.
- Separate input models, output models, and protocol envelope models.
- Use `from __future__ import annotations` at the top of every model file to support `X | Y` union syntax across Python versions.

```python
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

class JsonRpcRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: int | str | None = None
    method: str
    params: dict[str, Any] | None = None

class MyToolInput(BaseModel):
    query: str
    max_results: int | None = Field(None, ge=1, le=20)
```

- Use `model_dump(exclude_none=True)` when serializing responses to avoid null noise.
- Use `Literal["2.0"]` to enforce the `jsonrpc` version field.

## Security and Secrets Management

### Critical Rules
1. Never hardcode credentials, API keys, or secrets in source code.
2. Always use environment variables for sensitive data.
3. Never commit `.env` files (commit only `.env.example`).
4. Use `pydantic-settings` for configuration.

### What NOT to do

```python
# ❌ NEVER do this
API_KEY = "sk_live_51HxABC123..."
SECRET_KEY = "mysecretkey"
```

### What to DO instead

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Mock MCP Server"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
```

### Environment Variable Guidelines
- Keep secrets in `.env` (gitignored).
- Provide `.env.example` with dummy values.
- Document available env vars in `README.md`.

## Configuration and Runtime Settings

- Use `pydantic-settings` for typed config.
- Cache settings with `@lru_cache`.
- Provide safe defaults for all values (no required fields unless truly mandatory).

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Mock MCP Server"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## Code Quality Standards

- Use type hints on all function parameters and return types.
- Add `from __future__ import annotations` to files that use `X | Y` union syntax.
- Keep docstrings on public functions and classes.
- Keep `README.md` in sync with actual server behavior.

### Ruff Formatting (Required)

- Format all Python code with `ruff format` standards.
- After applying code changes, run `ruff format` on all changed Python files before finalizing.
- Ensure imports and lint fixes align with Ruff by running `ruff check --fix` when generating or modifying code.
- Do not introduce formatting that conflicts with the project's Ruff configuration in `pyproject.toml`.

## Testing Guidelines

- Use `pytest` with `httpx.Client` against a real `HTTPServer` spun up in a session-scoped fixture.
- Test the MCP protocol directly — do not mock `handle_mcp_request` in integration tests.
- Cover all JSON-RPC error paths: missing auth, parse error, invalid envelope, unknown method, invalid params, unknown tool.

```python
# conftest.py
import threading
import httpx
import pytest
from http.server import HTTPServer
from app.main import MCPRequestHandler

@pytest.fixture(scope="session")
def server_url():
    server = HTTPServer(("127.0.0.1", 0), MCPRequestHandler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()

@pytest.fixture
def client(server_url):
    with httpx.Client(base_url=server_url) as c:
        yield c
```

```python
# test pattern
def test_tools_list(client):
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={"X-Goog-Api-Key": "test-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is None
    assert len(data["result"]["tools"]) > 0
```

- Use `scope="session"` for the server fixture to avoid restarting it per test.
- Pass `daemon=True` to the server thread so it doesn't block test suite exit.
- Use port `0` to let the OS assign a free port; read it back from `server.server_address[1]`.

## Docker and Container Practices

### Dockerfile
- Prefer official Python slim images (`python:3.11-slim-bookworm`).
- Use multi-stage builds to keep the final image small.
- Run as a non-root user.
- Install only required system packages.

### Docker Compose
- Use environment variables for configuration via `env_file`.
- Keep to a single service unless a dependency (e.g., a real database) is required.

## Git and Version Control

### Do Not Commit
- `.env` files
- `__pycache__`
- credentials/secrets

### Do Commit
- `.env.example` with dummy values
- `requirements.txt` or `pyproject.toml`
- source code
- tests
- documentation

## Summary Checklist

When generating code for this project:
1. Follow the MCP JSON-RPC 2.0 protocol: correct envelope, standard error codes, always echo `id`.
2. Keep the HTTP handler thin — all logic lives in `handle_mcp_request`.
3. Define clear tool `description` strings so LLMs know when to call each tool.
4. Use Pydantic models for all inputs and outputs; validate early, fail with `_INVALID_PARAMS`.
5. Never hardcode secrets; rely on environment variables via `pydantic-settings`.
6. Add `from __future__ import annotations` to files using `X | Y` union syntax.
7. After applying changes, run `ruff format` and `ruff check --fix` on changed Python files.
8. Keep code typed, tested, and documented.
9. Follow secure Docker and CI practices.
