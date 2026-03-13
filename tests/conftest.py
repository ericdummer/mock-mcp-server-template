"""
Test configuration and fixtures.

Tests use an in-memory MCP transport so no HTTP server or network is needed.
Each test gets a fresh ClientSession connected to the shared server instance.
"""

from __future__ import annotations

from typing import AsyncGenerator

import anyio
import pytest

from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from app.api.mcp import server


@pytest.fixture
def test_settings():
    """Return a Settings instance with debug enabled."""
    from app.core.config import Settings

    return Settings(debug=True)


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Ensure get_settings() cache does not leak between tests."""
    from app.core.config import get_settings

    get_settings.cache_clear()


@pytest.fixture
async def mcp_session() -> AsyncGenerator[ClientSession, None]:
    """Provide an in-memory MCP client session connected to the server."""
    async with create_client_server_memory_streams() as (
        client_streams,
        server_streams,
    ):
        async with ClientSession(*client_streams) as session:
            async with anyio.create_task_group() as tg:
                tg.start_soon(
                    server.run,
                    server_streams[0],
                    server_streams[1],
                    server.create_initialization_options(),
                )
                await session.initialize()
                yield session
                tg.cancel_scope.cancel()
