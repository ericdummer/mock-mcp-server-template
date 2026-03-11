# Local Install Setup

Use this path when you want to run everything directly on your machine (without Docker).

## Prerequisites

Install these first:

- Python 3.11+
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

Using `python -m pip` ensures packages are installed into the same Python interpreter that runs the app.

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
INFO MCP server listening on http://0.0.0.0:8000/mcp
```

## 7) Verify the server

Send a test request to the MCP endpoint:

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-Goog-Api-Key: test-key" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m json.tool
```

## Run tests

```bash
pytest
```

## Reinstall dependencies when requirements change

If `requirements.txt` or `requirements-dev.txt` changes, rerun the appropriate install command:

```bash
python -m pip install -r requirements-dev.txt
```

## Troubleshooting

- If `python -m app.main` fails with missing packages, reinstall dependencies with `python -m pip install -r requirements-dev.txt`.
- If `python --version` is not Python 3.11+, use the correct interpreter explicitly, such as `python3.11`.
- If `pytest` is not found, install the development dependencies from `requirements-dev.txt`.

Back to setup index: [SETUP.md](../../SETUP.md)
Back to project overview: [README.md](../../README.md)
