"""
Test configuration and fixtures.
"""

import threading

import httpx
import pytest
from http.server import HTTPServer

from app.main import MCPRequestHandler


@pytest.fixture(scope="session")
def server_url():
    """Start the MCP HTTP server in a background thread and return its base URL."""
    server = HTTPServer(("127.0.0.1", 0), MCPRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


@pytest.fixture
def client(server_url):
    """Return an httpx client pointed at the test server."""
    with httpx.Client(base_url=server_url) as c:
        yield c


@pytest.fixture
def test_settings():
    """Return a Settings instance with debug enabled."""
    from app.core.config import Settings

    return Settings(debug=True)
