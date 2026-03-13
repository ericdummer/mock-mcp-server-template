"""Mock MCP server entry point.

Exposes the MCP protocol over HTTP using the official MCP SDK Streamable HTTP transport:
  POST /mcp  — send MCP JSON-RPC messages; responses may be streamed via SSE
  GET  /mcp  — open a long-lived SSE stream for server-initiated messages

Authentication: every request to /mcp must include the configured API key header
(default: X-Api-Key). Missing key → HTTP 401.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.datastructures import Headers
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from app.api.mcp import server  # noqa: F401 — registers list_tools/call_tool
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MCPASGIEndpoint:
    """ASGI endpoint wrapper so StreamableHTTP can own response writes."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return

        settings = get_settings()
        headers = Headers(scope=scope)
        api_key = headers.get(settings.api_key_header)
        if not api_key:
            logger.warning(
                "auth: missing %s header from %s",
                settings.api_key_header,
                scope.get("client"),
            )
            await Response(
                f"Missing {settings.api_key_header} header",
                status_code=401,
                media_type="text/plain",
            )(scope, receive, send)
            return

        logger.debug(
            "MCP request from %s (%s)",
            scope.get("client"),
            scope.get("method"),
        )
        session_manager: StreamableHTTPSessionManager = scope[
            "app"
        ].state.session_manager
        await session_manager.handle_request(scope, receive, send)


mcp_endpoint = MCPASGIEndpoint()


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """Create and run the session manager for the lifetime of the app."""
    session_manager = StreamableHTTPSessionManager(app=server)
    app.state.session_manager = session_manager
    async with session_manager.run():
        logger.info("MCP Streamable HTTP session manager started")
        yield
    logger.info("MCP Streamable HTTP session manager stopped")


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/mcp", endpoint=mcp_endpoint, methods=["GET", "POST", "DELETE"]),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
    ],
)


if __name__ == "__main__":
    import logging as _logging

    import uvicorn

    settings = get_settings()

    log_level = settings.log_level.upper()
    numeric_level = getattr(_logging, log_level, None)
    if not isinstance(numeric_level, int):
        numeric_level = _logging.INFO
        print(f"Warning: invalid LOG_LEVEL '{settings.log_level}', defaulting to INFO")

    _logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    logger.info(
        "Starting %s on http://%s:%s",
        settings.app_name,
        settings.host,
        settings.port,
    )
    logger.debug("Settings: %s", settings.model_dump())

    uvicorn.run(
        app, host=settings.host, port=settings.port, log_level=log_level.lower()
    )
