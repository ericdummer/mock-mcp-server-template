# Mock MCP Server

A mock implementation of the [Google Maps Grounding Lite MCP server](https://developers.google.com/maps/ai/grounding-lite), built with plain Python. Returns realistic synthetic data — no real API calls are made.

## Start Here

Use the setup index to choose the right path for your workflow:

- [SETUP.md](SETUP.md)

Direct links:

- [setup/local-install/README.md](setup/local-install/README.md)
- [setup/docker-compose/README.md](setup/docker-compose/README.md)
- [setup/dev-container/README.md](setup/dev-container/README.md)

## Current Application State

- Server: plain Python `http.server` (`app/main.py`)
- MCP endpoint: `POST /mcp` — JSON-RPC 2.0, requires `X-Goog-Api-Key` header
- Mock tools: `search_places`, `lookup_weather`, `compute_routes`
- Runtime config: environment variables via `pydantic-settings` (`app/core/config.py`)
- Container stack: single `web` service (`docker-compose.yml`)

## Configuration

Environment variables are defined in [.env.example](.env.example). Available variables:

- `APP_NAME`, `DEBUG`
- `HOST`, `PORT`, `WEB_PORT`

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

## Repository Layout

```
app/
    api/       # MCP handler and mock data builders
    core/      # settings/config
    models/    # Pydantic models for MCP protocol
tests/         # test suite
.github/
    workflows/ # CI workflows
```

## Development Guidelines

Project coding/security guidance is documented in [.github/copilot-instructions.md](.github/copilot-instructions.md).
