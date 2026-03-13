# Mock MCP Server Template

A generic template for building a mock [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server using the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk). Returns realistic synthetic data — no real API calls are made.

Clone this repo, add your tool files, and have a running mock MCP server in minutes.

## Start Here

Use the setup index to choose the right path for your workflow:

- [SETUP.md](SETUP.md)

Direct links:

- [setup/local-install/README.md](setup/local-install/README.md)
- [setup/docker-compose/README.md](setup/docker-compose/README.md)
- [setup/dev-container/README.md](setup/dev-container/README.md)

## Connecting an MCP Client

The server uses Streamable HTTP transport. A sample client config is provided in [`mcp.json`](mcp.json):

```json
{
    "mcpServers": {
        "mock-mcp-server": {
            "type": "http",
            "url": "http://localhost:8000/mcp",
            "headers": {
                "X-Api-Key": "your-api-key-here"
            }
        }
    }
}
```

**MCP Inspector** (browser-based testing tool):

```bash
MCP_PROXY_AUTH_TOKEN=localdev npx @modelcontextprotocol/inspector
```

Open: `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=localdev`  
Set Transport to **Streamable HTTP**, URL to `http://localhost:8000/mcp`, add header `X-Api-Key: test-key`.

## Entities and Tools

The server implements full CRUD for three entities: **Customers**, **Products**, and **Orders**.

| Entity | Tools |
|--------|-------|
| Customer | `create_customer`, `update_customer`, `delete_customer`, `get_customer`, `list_customers` |
| Product | `create_product`, `update_product`, `delete_product`, `get_product`, `list_products` |
| Order | `create_order`, `update_order_status`, `add_products_to_order`, `remove_products_from_order`, `delete_order`, `get_order`, `list_orders`, `list_orders_by_customer` |

## Resources

Read-only resources are available alongside tools:

| URI | Description |
|-----|-------------|
| `customers://all` | All customers |
| `customers://{id}` | Single customer by ID |
| `customers://{id}/orders` | All orders for a customer |
| `products://all` | All products |
| `products://{id}` | Single product by ID |
| `orders://all` | All orders |
| `orders://{id}` | Single order by ID |
| `orders://{id}/products` | Full product objects for all products in an order |

## How to Add Tools

Tools are grouped by entity in `app/tools/`. Each entity file exposes `TOOL_DEFINITIONS` (list of schemas) and `handle(name, params)` (dispatcher). To add a new tool:

1. Add its definition to `TOOL_DEFINITIONS` in the relevant entity file (or create a new entity file).
2. Add a handler function and route it in `handle()`.
3. Register the entity module in `app/api/mcp.py` (add it to `_entity_tool_modules`).

## Architecture

```
app/
├── main.py              # Starlette ASGI app — Streamable HTTP transport, auth check
├── core/
│   ├── config.py        # Settings via pydantic-settings
│   └── server.py        # MCP SDK Server singleton
├── api/mcp.py           # Registers tools + resources; dispatches to entity modules
├── data/
│   └── store.py         # Shared in-memory store with seed data (singleton)
├── models/
│   ├── customer.py      # Customer dataclass
│   ├── product.py       # Product dataclass
│   └── order.py         # Order dataclass
├── resources/
│   ├── customers.py     # Read-only customer resource handlers
│   ├── products.py      # Read-only product resource handlers
│   └── orders.py        # Read-only order resource handlers
└── tools/
    ├── customers.py     # Customer CRUD tools
    ├── products.py      # Product CRUD tools
    └── orders.py        # Order CRUD tools
tests/                   # Async tests using anyio + MCP in-memory transport
.devcontainer/           # VS Code Dev Container (full dev deps)
.github/workflows/       # CI: tests, lint, security scans
Dockerfile               # Production image (slim, runtime deps only)
mcp.json                 # Sample MCP client connection config
```

## Transport

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/mcp` | `POST` | Send MCP JSON-RPC messages — responses may be streamed via SSE |
| `/mcp` | `GET` | Open a long-lived SSE stream for server-initiated messages |

Authentication: include any non-empty value in the `X-Api-Key` header. Missing key → HTTP 401.

## MCP Logging

Tools call `server.request_context.session.send_log_message()` to emit structured log events visible in MCP clients that support notifications (e.g. MCP Inspector's **Notifications** tab).

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Mock MCP Server` | Application name |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Listen port |
| `API_KEY_HEADER` | `X-Api-Key` | HTTP header name for the API key |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

Never commit `.env` with real credentials.

## CI / Security Workflows

GitHub Actions workflows in [.github/workflows](.github/workflows):

- [tests.yml](.github/workflows/tests.yml): unit tests and coverage
- [ruff.yml](.github/workflows/ruff.yml): lint and format checks
- [trivy.yml](.github/workflows/trivy.yml): filesystem and container vulnerability scans
- [codeql.yml](.github/workflows/codeql.yml): CodeQL analysis

## Sonar Configuration

Sonar scanner settings are defined in [sonar-project.properties](sonar-project.properties):

- `sonar.sources=app`: scans application source files under `app/`
- `sonar.tests=tests`: identifies test files under `tests/`
- `sonar.python.version=3.11`: pins analysis to the project Python version
- `sonar.python.coverage.reportPaths=coverage.xml`: imports pytest coverage results

## Development Guidelines

Project coding/security guidance is documented in [.github/copilot-instructions.md](.github/copilot-instructions.md).

