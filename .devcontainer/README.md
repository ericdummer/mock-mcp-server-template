# Dev Container Reference

For the user-facing setup flow, use [setup/dev-container/README.md](../setup/dev-container/README.md).

This file documents Dev Container-specific behavior in this repository.

## Container Configuration Summary

- Primary service: `web` (from root `docker-compose.yml`)
- Compose files used by Dev Containers:
  - `../docker-compose.yml`
  - `./docker-compose.yml` (override)
- Workspace mount: repository mounted under `/workspaces/...`
- Forwarded ports: `8000` (MCP server)

## Runtime Behavior in Dev Container

- The override sets `command: sleep infinity` so the container stays running for interactive development.
- Start the MCP server manually from the container terminal:

```bash
python -m app.main
```

- Compose uses the root `docker-compose.yml` plus `.devcontainer/docker-compose.yml`; environment files are defined in those compose files.

## Tooling Included for IDE Analysis

- Python comes from the base image and the Dev Container pins VS Code to `/usr/local/bin/python`.
- Project dependencies are installed in the Dev Container image from `requirements-dev.txt`.
- Ruff is installed via `postCreateCommand`.
- OpenJDK 17 is installed in `.devcontainer/Dockerfile` for SonarLint Java support.
- Node.js 20 is installed in `.devcontainer/Dockerfile` for SonarLint JS/TS support.
- VS Code extensions include:
  - `ms-python.python`
  - `ms-python.vscode-pylance`
  - `SonarSource.sonarlint-vscode`

## Troubleshooting

- If Sonar analysis does not start, verify:

```bash
java -version
node -v
python --version
```

- If Dev Container config changes are not applied, run:
  - `Dev Containers: Rebuild Container`

- If Python dependencies appear to be missing after a requirements or Dev Container config change, rebuild the container.