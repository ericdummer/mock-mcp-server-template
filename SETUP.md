# Setup Guides

Choose one setup path based on your workflow:

- Local install (optionally with a virtual environment): [setup/local-install/README.md](setup/local-install/README.md)
- Docker Compose: [setup/docker-compose/README.md](setup/docker-compose/README.md)
- VS Code Dev Container: [setup/dev-container/README.md](setup/dev-container/README.md)

## Quick Path Selection

- Choose Local install if you want fastest iteration without Docker and full local control.
- Choose Docker Compose if you want containerized runtime without using VS Code Dev Containers.
- Choose VS Code Dev Container if you want a fully containerized development environment inside VS Code.

## Comparison

| Setup path | Best for | Includes test tooling by default | Typical start command |
|---|---|---|---|
| Local install | Direct host development | Yes (`requirements-dev.txt`) | `python -m app.main` |
| Docker Compose | Containerized app runtime | No (runtime image only) | `docker compose up --build` |
| VS Code Dev Container | Containerized development in VS Code | Yes (built into dev image) | `python -m app.main` |

## Common Requirements

- Git
- Access to this repository
- For Docker-based paths: Docker Engine/Desktop and `docker compose`
- For Dev Container path: VS Code + Dev Containers extension

For project architecture, endpoints, configuration, and CI/security details, see [README.md](README.md).
